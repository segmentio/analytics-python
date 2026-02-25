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

# Default duration limits (12 hours in seconds)
DEFAULT_MAX_TOTAL_BACKOFF_DURATION = 43200
DEFAULT_MAX_RATE_LIMIT_DURATION = 43200


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
                 on_error=None, upload_interval=0.5, gzip=False, retries=1000,
                 timeout=15, proxies=None, oauth_manager=None,
                 max_total_backoff_duration=DEFAULT_MAX_TOTAL_BACKOFF_DURATION,
                 max_rate_limit_duration=DEFAULT_MAX_RATE_LIMIT_DURATION):
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
        self.max_total_backoff_duration = max_total_backoff_duration
        self.max_rate_limit_duration = max_rate_limit_duration

        # Rate-limit state
        self.rate_limited_until = None
        self.rate_limit_start_time = None

    def run(self):
        """Runs the consumer."""
        self.log.debug('consumer is running...')
        while self.running:
            self.upload()

        self.log.debug('consumer exited.')

    def pause(self):
        """Pause the consumer."""
        self.running = False

    def set_rate_limit_state(self, response):
        """Set rate-limit state from a 429 response with a valid Retry-After header."""
        retry_after = parse_retry_after(response) if response else None
        if retry_after is not None:
            self.rate_limited_until = time.time() + retry_after
        if self.rate_limit_start_time is None:
            self.rate_limit_start_time = time.time()

    def clear_rate_limit_state(self):
        """Clear rate-limit state after successful request or duration exceeded."""
        self.rate_limited_until = None
        self.rate_limit_start_time = None

    def upload(self):
        """Upload the next batch of items, return whether successful."""
        success = False
        batch = self.next()
        if len(batch) == 0:
            return False

        # Check rate-limit state before attempting upload
        if self.rate_limited_until is not None:
            now = time.time()

            # Check if maxRateLimitDuration has been exceeded
            if (self.rate_limit_start_time is not None and
                    now - self.rate_limit_start_time > self.max_rate_limit_duration):
                self.log.error(
                    'Rate limit duration exceeded (%ds). Clearing rate-limit state and dropping batch.',
                    self.max_rate_limit_duration
                )
                self.clear_rate_limit_state()
                # Drop the batch by marking items as done
                if self.on_error:
                    self.on_error(
                        Exception('Rate limit duration exceeded, batch dropped'),
                        batch
                    )
                for _ in batch:
                    self.queue.task_done()
                return False

            # Still rate-limited; wait until the rate limit expires
            wait_time = self.rate_limited_until - now
            if wait_time > 0:
                self.log.debug(
                    'Rate-limited. Waiting %.2fs before next upload attempt.',
                    wait_time
                )
                time.sleep(wait_time)

        try:
            self.request(batch)
            # Success — clear rate-limit state
            self.clear_rate_limit_state()
            success = True
        except APIError as e:
            if e.status == 429 and self.rate_limited_until is not None:
                # 429: rate-limit state already set by request(). Re-queue batch.
                self.log.debug('429 received. Re-queuing batch and halting upload iteration.')
                for item in batch:
                    try:
                        self.queue.put(item, block=False)
                    except Exception:
                        pass  # Queue full, item lost
                success = False
            else:
                self.log.error('error uploading: %s', e)
                success = False
                if self.on_error:
                    self.on_error(e, batch)
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
              - 511 is only retryable when OauthManager is configured
            Non-retryable 5xx: 501, 505
            """
            if 400 <= status < 500:
                return status in (408, 410, 429, 460)
            elif 500 <= status < 600:
                if status in (501, 505):
                    return False
                if status == 511:
                    return self.oauth_manager is not None
                return True
            return False

        def calculate_backoff_delay(attempt):
            """
            Calculate exponential backoff delay with jitter.
            First retry is immediate, then 0.5s, 1s, 2s, 4s, etc.
            """
            if attempt == 1:
                return 0  # First retry is immediate
            base_delay = 0.5 * (2 ** (attempt - 2))
            jitter = random.uniform(0, 0.1 * base_delay)
            return min(base_delay + jitter, 60)  # Cap at 60 seconds

        total_attempts = 0
        backoff_attempts = 0
        first_failure_time = None

        while True:
            total_attempts += 1

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
                    retry_count=total_attempts - 1
                )
                # Success
                return response

            except FatalError as e:
                # Non-retryable error
                self.log.error(f"Fatal error after {total_attempts} attempts: {e}")
                raise

            except APIError as e:
                # 429 with valid Retry-After: set rate-limit state and raise
                # to caller (pipeline blocking). Without Retry-After, fall
                # through to counted backoff like any other retryable error.
                if e.status == 429:
                    retry_after = parse_retry_after(e.response) if e.response else None
                    if retry_after is not None:
                        self.set_rate_limit_state(e.response)
                        raise

                # Check if status is retryable
                if not is_retryable_status(e.status):
                    self.log.error(
                        f"Non-retryable error {e.status} after {total_attempts} attempts: {e}"
                    )
                    raise

                # Transient error -- per-batch backoff
                if first_failure_time is None:
                    first_failure_time = time.time()
                if time.time() - first_failure_time > self.max_total_backoff_duration:
                    self.log.error(
                        f"Max total backoff duration ({self.max_total_backoff_duration}s) exceeded "
                        f"after {total_attempts} attempts. Final error: {e}"
                    )
                    raise

                # Count this against backoff attempts
                backoff_attempts += 1
                if backoff_attempts >= self.retries + 1:
                    self.log.error(
                        f"All {self.retries} retries exhausted after {total_attempts} total attempts. Final error: {e}"
                    )
                    raise

                # Calculate exponential backoff delay with jitter
                delay = calculate_backoff_delay(backoff_attempts)

                self.log.debug(
                    f"Retry attempt {backoff_attempts}/{self.retries} (total attempts: {total_attempts}) "
                    f"after {delay:.2f}s for status {e.status}"
                )
                time.sleep(delay)

            except Exception as e:
                # Network errors or other exceptions - retry with backoff
                if first_failure_time is None:
                    first_failure_time = time.time()
                if time.time() - first_failure_time > self.max_total_backoff_duration:
                    self.log.error(
                        f"Max total backoff duration ({self.max_total_backoff_duration}s) exceeded "
                        f"after {total_attempts} attempts. Final error: {e}"
                    )
                    raise

                backoff_attempts += 1

                if backoff_attempts >= self.retries + 1:
                    self.log.error(
                        f"All {self.retries} retries exhausted after {total_attempts} total attempts. Final error: {e}"
                    )
                    raise

                # Calculate exponential backoff delay with jitter
                delay = calculate_backoff_delay(backoff_attempts)

                self.log.debug(
                    f"Network error retry {backoff_attempts}/{self.retries} (total attempts: {total_attempts}) "
                    f"after {delay:.2f}s: {e}"
                )
                time.sleep(delay)
