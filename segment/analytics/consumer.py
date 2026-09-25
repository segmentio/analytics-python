import json
import logging
import random
import time
from queue import Empty
from threading import Thread

from segment.analytics.request import APIError, DatetimeSerializer, parse_retry_after, post


class ShutdownInterrupted(Exception):
    """A retry wait was cut short by shutdown.

    Distinct from an upload failure: the batch has not exhausted its budget, so it
    is re-queued rather than reported through on_error.
    """


MAX_MSG_SIZE = 32 << 10

# Our servers only accept batches less than 500KB. Here limit is set slightly
# lower to leave space for extra data that will be added later, eg. "sentAt".
BATCH_SIZE_LIMIT = 475000

# Default duration limits (12 hours in seconds)
DEFAULT_MAX_TOTAL_BACKOFF_DURATION = 43200
# Rate-limited attempts are deliberately uncounted, so this duration is the only
# thing bounding them. It is deliberately several times MAX_RETRY_AFTER_SECONDS:
# when the two are equal a single maximal Retry-After consumes the whole budget,
# leaving one attempt and no retry at all.
DEFAULT_MAX_RATE_LIMIT_DURATION = 1800


class FatalError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        msg = "[Segment] {0})"
        return msg.format(self.message)


class Consumer(Thread):
    """Consumes the messages from the client's queue."""

    log = logging.getLogger("segment")

    def __init__(
        self,
        queue,
        write_key,
        upload_size=100,
        host=None,
        on_error=None,
        upload_interval=0.5,
        gzip=False,
        retries=10,
        timeout=15,
        proxies=None,
        oauth_manager=None,
        max_total_backoff_duration=DEFAULT_MAX_TOTAL_BACKOFF_DURATION,
        max_rate_limit_duration=DEFAULT_MAX_RATE_LIMIT_DURATION,
    ):
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
        self.log.debug("consumer is running...")
        while self.running:
            self.upload()

        self.log.debug("consumer exited.")

    def pause(self):
        """Pause the consumer."""
        self.running = False

    def _wait(self, seconds):
        """Sleep in slices so pause()/join()/atexit are not blocked for up to
        MAX_RETRY_AFTER_SECONDS. Returns False if the consumer was stopped."""
        deadline = time.monotonic() + seconds
        while self.running:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return True
            time.sleep(min(1.0, remaining))
        return False

    def _requeue(self, batch):
        """Put a batch back on the queue, reporting anything that no longer fits."""
        dropped = []
        for item in batch:
            try:
                self.queue.put(item, block=False)
            except Exception:
                dropped.append(item)
        if dropped:
            self.log.error("Queue full during rate-limit re-queue. Dropping %d item(s).", len(dropped))
            if self.on_error:
                self.on_error(Exception("Queue full, items dropped during rate-limit re-queue"), dropped)

    def set_rate_limit_state(self, retry_after):
        """Open or extend a rate-limit episode using an already-parsed Retry-After.

        Takes the delay rather than the response on purpose. Parsing an HTTP-date
        Retry-After reads the wall clock and truncates to whole seconds, so parsing
        twice for one response can straddle a second boundary and disagree with
        itself — leaving the episode open with no deadline, which skipped the wait
        entirely on the next attempt.
        """
        if retry_after is not None:
            self.rate_limited_until = time.monotonic() + retry_after
        if self.rate_limit_start_time is None:
            self.rate_limit_start_time = time.monotonic()

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

        # rate_limit_start_time marks the episode; rate_limited_until is only the
        # current deadline and is cleared once served, so gate on the former.
        if self.rate_limit_start_time is not None:
            now = time.monotonic()

            # Check if maxRateLimitDuration has been exceeded
            if now - self.rate_limit_start_time > self.max_rate_limit_duration:
                self.log.error(
                    "Rate limit duration exceeded (%ds). Clearing rate-limit state and dropping batch.", self.max_rate_limit_duration
                )
                self.clear_rate_limit_state()
                # Drop the batch by marking items as done
                if self.on_error:
                    self.on_error(Exception("Rate limit duration exceeded, batch dropped"), batch)
                for _ in batch:
                    self.queue.task_done()
                return False

            # Still rate-limited; wait until the rate limit expires
            if self.rate_limited_until is not None:
                remaining = self.max_rate_limit_duration - (now - self.rate_limit_start_time)
                wait_time = self.rate_limited_until - now
                if wait_time > remaining:
                    # Shortening the wait to fit the budget would send the next request
                    # inside the window the server asked us to wait out — a request it
                    # has already said it will not serve — and the budget would then be
                    # spent, so it would be the last one anyway. Give up here instead of
                    # spending a request to be told the same thing.
                    self.log.error(
                        "Rate limit budget (%ds) cannot accommodate the requested wait; dropping batch.",
                        self.max_rate_limit_duration,
                    )
                    self.clear_rate_limit_state()
                    if self.on_error:
                        self.on_error(Exception("Rate limit duration exceeded, batch dropped"), batch)
                    for _ in batch:
                        self.queue.task_done()
                    return False
                if wait_time > 0:
                    self.log.debug("Rate-limited. Waiting %.2fs before next upload attempt.", wait_time)
                    if not self._wait(wait_time):
                        # Shutting down: hand the batch back rather than uploading
                        # into a consumer that is stopping. This returns before the
                        # try/finally below, so the get() obligations have to be
                        # discharged here or queue.join() never completes; the
                        # re-queued copies carry their own fresh obligations.
                        self._requeue(batch)
                        for _ in batch:
                            self.queue.task_done()
                        return False
                # Clear the served deadline so it cannot classify a later error.
                self.rate_limited_until = None

        try:
            self.request(batch)
            # Success — clear rate-limit state
            self.clear_rate_limit_state()
            success = True
        except ShutdownInterrupted:
            # Budget was not exhausted; the wait was. Hand the batch back so the
            # next run uploads it, rather than reporting a failure that did not
            # happen. Matches the rate-limited wait above.
            self.log.debug("Shutting down during retry backoff. Re-queuing batch.")
            self._requeue(batch)
            success = False

        except APIError as e:
            if getattr(e, "rate_limited", False):
                self.log.debug("Rate-limited (status %d). Re-queuing batch and halting upload iteration.", e.status)
                self._requeue(batch)
                success = False
            else:
                # The request completed and carried no rate-limit signal, so the
                # episode is over. Leaving the marker set strands it: this consumer
                # outlives the batch, upload() returns at the empty-batch guard
                # before the budget block, and nothing else clears it — so the next
                # batch to arrive after the budget elapses is dropped for a rate
                # limit that ended here, without ever being sent.
                self.clear_rate_limit_state()
                self.log.error("error uploading: %s", e)
                success = False
                if self.on_error:
                    self.on_error(e, batch)
        except Exception as e:
            # Same reasoning as above.
            self.clear_rate_limit_state()
            self.log.error("error uploading: %s", e)
            success = False
            if self.on_error:
                self.on_error(e, batch)
        finally:
            # Each item in batch was obtained via queue.get() and must have
            # exactly one matching task_done() call — including re-queued items,
            # which will produce a new task_done() obligation on their next get().
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
                item = queue.get(block=True, timeout=self.upload_interval - elapsed)
                item_size = len(json.dumps(item, cls=DatetimeSerializer).encode())
                if item_size > MAX_MSG_SIZE:
                    self.log.error("Item exceeds 32kb limit, dropping. (%s)", str(item))
                    continue
                items.append(item)
                total_size += item_size
                if total_size >= BATCH_SIZE_LIMIT:
                    self.log.debug("hit batch size limit (size: %d)", total_size)
                    break
            except Empty:
                break
            except Exception as e:
                self.log.exception("Exception: %s", e)

        return items

    def request(self, batch):
        """Attempt to upload the batch and retry before raising an error"""

        def is_retryable_status(status):
            # Retryable 4xx: 408, 429, 460
            # 410 Gone: permanently removed, but included for parity with the
            # Node.js SDK. Retrying is harmless since the server will keep
            # returning 410, and the retry budget caps total attempts.
            # Non-retryable 4xx: 400, 401, 403, 404, 413, 422, and all other 4xx
            # Retryable 5xx: all except 501, 505
            # 511: only retryable when OauthManager is configured
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
            # First retry is immediate; thereafter 0.5s, 1s, 2s, 4s… capped at 60s
            if attempt == 1:
                return 0
            base_delay = 0.5 * (2 ** (attempt - 2))
            jitter = random.uniform(0, 0.1 * base_delay)
            return min(base_delay + jitter, 60)

        def apply_backoff(e, label):
            """Apply retry backoff logic. Returns delay if should retry, raises if exhausted."""
            nonlocal first_failure_time, backoff_attempts
            if first_failure_time is None:
                first_failure_time = time.monotonic()
            if time.monotonic() - first_failure_time >= self.max_total_backoff_duration:
                self.log.error(
                    f"Max total backoff duration ({self.max_total_backoff_duration}s) exceeded "
                    f"after {total_attempts} attempts. Final error: {e}"
                )
                raise e
            backoff_attempts += 1
            if backoff_attempts >= self.retries + 1:
                self.log.error(f"All {self.retries} retries exhausted after {total_attempts} total attempts. Final error: {e}")
                raise e
            delay = calculate_backoff_delay(backoff_attempts)
            self.log.debug(f"{label} {backoff_attempts}/{self.retries} (total attempts: {total_attempts}) after {delay:.2f}s: {e}")
            return delay

        total_attempts = 0
        backoff_attempts = 0
        first_failure_time = None

        while True:
            total_attempts += 1

            try:
                response = post(
                    self.write_key,
                    self.host,
                    gzip=self.gzip,
                    timeout=self.timeout,
                    batch=batch,
                    proxies=self.proxies,
                    oauth_manager=self.oauth_manager,
                    retry_count=total_attempts - 1,
                )
                return response

            except FatalError as e:
                # Raised by oauth_manager when token refresh fails permanently;
                # not safe to retry.
                self.log.error(f"Fatal error after {total_attempts} attempts: {e}")
                raise

            except APIError as e:
                if not is_retryable_status(e.status):
                    self.log.error(f"Non-retryable error {e.status} after {total_attempts} attempts: {e}")
                    raise

                # Any retryable status with valid Retry-After > 0: block pipeline, re-queue
                retry_after = parse_retry_after(e.response) if e.response is not None else None
                if retry_after is not None and retry_after > 0:
                    self.set_rate_limit_state(retry_after)
                    # upload() classifies on this flag rather than consumer state,
                    # which may still hold an earlier episode's deadline.
                    e.rate_limited = True
                    raise

                # No Retry-After: counted backoff
                delay = apply_backoff(e, f"Retry attempt (status {e.status})")
                if not self._wait(delay):
                    raise ShutdownInterrupted() from e

            except Exception as e:
                delay = apply_backoff(e, "Network error retry")
                if not self._wait(delay):
                    raise ShutdownInterrupted() from e
