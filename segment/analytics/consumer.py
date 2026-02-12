import logging
import time
import random
from threading import Thread
import json

from segment.analytics.request import post, APIError, DatetimeSerializer, parse_retry_after

from queue import Empty

MAX_MSG_SIZE = 32 << 10

# Our servers only accept batches less than 500KB. Here limit is set slightly
# lower to leave space for extra data that will be added later, eg. "sentAt".
BATCH_SIZE_LIMIT = 475000


class FatalError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        msg = "[Segment] {0})"
        return msg.format(self.message)


class Consumer(Thread):
    """Consumes the messages from the client's queue."""
    log = logging.getLogger('segment')

    def __init__(self, queue, write_key, upload_size=100, host=None,
                 on_error=None, upload_interval=0.5, gzip=False, retries=10,
                 timeout=15, proxies=None, oauth_manager=None):
        """Create a consumer thread."""
        Thread.__init__(self)
        # Make consumer a daemon thread so that it doesn't block program exit
        self.daemon = True
        self.upload_size = upload_size
        self.upload_interval = upload_interval
        self.write_key = write_key
        self.host = host
        self.on_error = on_error
        self.queue = queue
        self.gzip = gzip
        # It's important to set running in the constructor: if we are asked to
        # pause immediately after construction, we might set running to True in
        # run() *after* we set it to False in pause... and keep running
        # forever.
        self.running = True
        self.retries = retries
        self.timeout = timeout
        self.proxies = proxies
        self.oauth_manager = oauth_manager

    def run(self):
        """Runs the consumer."""
        self.log.debug('consumer is running...')
        while self.running:
            self.upload()

        self.log.debug('consumer exited.')

    def pause(self):
        """Pause the consumer."""
        self.running = False

    def upload(self):
        """Upload the next batch of items, return whether successful."""
        success = False
        batch = self.next()
        if len(batch) == 0:
            return False

        try:
            self.request(batch)
            success = True
        except Exception as e:
            self.log.error('error uploading: %s', e)
            success = False
            if self.on_error:
                self.on_error(e, batch)
        finally:
            # mark items as acknowledged from queue
            for _ in batch:
                self.queue.task_done()
        return success

    def next(self):
        """Return the next batch of items to upload."""
        queue = self.queue
        items = []

        start_time = time.monotonic()
        total_size = 0

        while len(items) < self.upload_size:
            elapsed = time.monotonic() - start_time
            if elapsed >= self.upload_interval:
                break
            try:
                item = queue.get(
                    block=True, timeout=self.upload_interval - elapsed)
                item_size = len(json.dumps(
                    item, cls=DatetimeSerializer).encode())
                if item_size > MAX_MSG_SIZE:
                    self.log.error(
                        'Item exceeds 32kb limit, dropping. (%s)', str(item))
                    continue
                items.append(item)
                total_size += item_size
                if total_size >= BATCH_SIZE_LIMIT:
                    self.log.debug(
                        'hit batch size limit (size: %d)', total_size)
                    break
            except Empty:
                break
            except Exception as e:
                self.log.exception('Exception: %s', e)

        return items

    def request(self, batch):
        """Attempt to upload the batch and retry before raising an error"""

        def is_retryable_status(status):
            """
            Determine if a status code is retryable.
            Retryable 4xx: 408, 410, 429, 460
            Non-retryable 4xx: 400, 401, 403, 404, 413, 422, and all other 4xx
            Retryable 5xx: All except 501, 505
            Non-retryable 5xx: 501, 505
            """
            if 400 <= status < 500:
                return status in (408, 410, 429, 460)
            elif 500 <= status < 600:
                return status not in (501, 505)
            return False

        def should_use_retry_after(status):
            """Check if status code should respect Retry-After header"""
            return status in (408, 429, 503)

        total_attempts = 0
        backoff_attempts = 0
        max_backoff_attempts = self.retries + 1

        while True:
            try:
                # Make the request with current retry count
                response = post(
                    self.write_key,
                    self.host,
                    gzip=self.gzip,
                    timeout=self.timeout,
                    batch=batch,
                    proxies=self.proxies,
                    oauth_manager=self.oauth_manager,
                    retry_count=total_attempts
                )
                # Success
                return response

            except FatalError as e:
                # Non-retryable error
                self.log.error(f"Fatal error after {total_attempts} attempts: {e}")
                raise

            except APIError as e:
                total_attempts += 1

                # Check if we should use Retry-After header
                if should_use_retry_after(e.status) and e.response:
                    retry_after = parse_retry_after(e.response)
                    if retry_after:
                        self.log.debug(
                            f"Retry-After header present: waiting {retry_after}s (attempt {total_attempts})"
                        )
                        time.sleep(retry_after)
                        continue  # Does not count against backoff budget

                # Check if status is retryable
                if not is_retryable_status(e.status):
                    self.log.error(
                        f"Non-retryable error {e.status} after {total_attempts} attempts: {e}"
                    )
                    raise

                # Count this against backoff attempts
                backoff_attempts += 1
                if backoff_attempts >= max_backoff_attempts:
                    self.log.error(
                        f"All {self.retries} retries exhausted after {total_attempts} total attempts. Final error: {e}"
                    )
                    raise

                # Calculate exponential backoff delay with jitter
                base_delay = 0.5 * (2 ** (backoff_attempts - 1))
                jitter = random.uniform(0, 0.1 * base_delay)
                delay = min(base_delay + jitter, 60)  # Cap at 60 seconds

                self.log.debug(
                    f"Retry attempt {backoff_attempts}/{self.retries} (total attempts: {total_attempts}) "
                    f"after {delay:.2f}s for status {e.status}"
                )
                time.sleep(delay)

            except Exception as e:
                # Network errors or other exceptions - retry with backoff
                total_attempts += 1
                backoff_attempts += 1

                if backoff_attempts >= max_backoff_attempts:
                    self.log.error(
                        f"All {self.retries} retries exhausted after {total_attempts} total attempts. Final error: {e}"
                    )
                    raise

                # Calculate exponential backoff delay with jitter
                base_delay = 0.5 * (2 ** (backoff_attempts - 1))
                jitter = random.uniform(0, 0.1 * base_delay)
                delay = min(base_delay + jitter, 60)  # Cap at 60 seconds

                self.log.debug(
                    f"Network error retry {backoff_attempts}/{self.retries} (total attempts: {total_attempts}) "
                    f"after {delay:.2f}s: {e}"
                )
                time.sleep(delay)
