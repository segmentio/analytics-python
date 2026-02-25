import unittest
import mock
import time
import json

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from segment.analytics.consumer import Consumer, MAX_MSG_SIZE, FatalError
from segment.analytics.request import APIError


class TestConsumer(unittest.TestCase):

    def test_next(self):
        q = Queue()
        consumer = Consumer(q, '')
        q.put(1)
        next = consumer.next()
        self.assertEqual(next, [1])

    def test_next_limit(self):
        q = Queue()
        upload_size = 50
        consumer = Consumer(q, '', upload_size)
        for i in range(10000):
            q.put(i)
        next = consumer.next()
        self.assertEqual(next, list(range(upload_size)))

    def test_dropping_oversize_msg(self):
        q = Queue()
        consumer = Consumer(q, '')
        oversize_msg = {'m': 'x' * MAX_MSG_SIZE}
        q.put(oversize_msg)
        next = consumer.next()
        self.assertEqual(next, [])
        self.assertTrue(q.empty())

    def test_upload(self):
        q = Queue()
        consumer = Consumer(q, 'testsecret')
        track = {
            'type': 'track',
            'event': 'python event',
            'userId': 'userId'
        }
        q.put(track)
        success = consumer.upload()
        self.assertTrue(success)

    def test_upload_interval(self):
        # Put _n_ items in the queue, pausing a little bit more than
        # _upload_interval_ after each one.
        # The consumer should upload _n_ times.
        q = Queue()
        upload_interval = 0.3
        consumer = Consumer(q, 'testsecret', upload_size=10,
                            upload_interval=upload_interval)
        with mock.patch('segment.analytics.consumer.post') as mock_post:
            consumer.start()
            for i in range(0, 3):
                track = {
                    'type': 'track',
                    'event': 'python event %d' % i,
                    'userId': 'userId'
                }
                q.put(track)
                time.sleep(upload_interval * 1.1)
            self.assertEqual(mock_post.call_count, 3)

    def test_multiple_uploads_per_interval(self):
        # Put _upload_size*2_ items in the queue at once, then pause for
        # _upload_interval_. The consumer should upload 2 times.
        q = Queue()
        upload_interval = 0.5
        upload_size = 10
        consumer = Consumer(q, 'testsecret', upload_size=upload_size,
                            upload_interval=upload_interval)
        with mock.patch('segment.analytics.consumer.post') as mock_post:
            consumer.start()
            for i in range(0, upload_size * 2):
                track = {
                    'type': 'track',
                    'event': 'python event %d' % i,
                    'userId': 'userId'
                }
                q.put(track)
            time.sleep(upload_interval * 1.1)
            self.assertEqual(mock_post.call_count, 2)

    @classmethod
    def test_request(cls):
        consumer = Consumer(None, 'testsecret')
        track = {
            'type': 'track',
            'event': 'python event',
            'userId': 'userId'
        }
        consumer.request([track])

    def _test_request_retry(self, consumer,
                            expected_exception, exception_count):

        def mock_post(*args, **kwargs):
            mock_post.call_count += 1
            if mock_post.call_count <= exception_count:
                raise expected_exception
        mock_post.call_count = 0

        with mock.patch('segment.analytics.consumer.post',
                        mock.Mock(side_effect=mock_post)):
            track = {
                'type': 'track',
                'event': 'python event',
                'userId': 'userId'
            }
            # request() should succeed if the number of exceptions raised is
            # less than the retries parameter.
            if exception_count <= consumer.retries:
                consumer.request([track])
            else:
                # if exceptions are raised more times than the retries
                # parameter, we expect the exception to be returned to
                # the caller.
                try:
                    consumer.request([track])
                except type(expected_exception) as exc:
                    self.assertEqual(exc, expected_exception)
                else:
                    self.fail(
                        "request() should raise an exception if still failing "
                        "after %d retries" % consumer.retries)

    def test_request_retry(self):
        # we should retry on general errors
        consumer = Consumer(None, 'testsecret')
        self._test_request_retry(consumer, Exception('generic exception'), 2)

        # we should retry on server errors
        consumer = Consumer(None, 'testsecret')
        self._test_request_retry(consumer, APIError(
            500, 'code', 'Internal Server Error'), 2)

        # 429 without Retry-After uses counted backoff (like other retryable errors)
        consumer = Consumer(None, 'testsecret')
        self._test_request_retry(consumer, APIError(
            429, 'code', 'Too Many Requests'), 2)

        # we should NOT retry on other client errors
        consumer = Consumer(None, 'testsecret')
        api_error = APIError(400, 'code', 'Client Errors')
        try:
            self._test_request_retry(consumer, api_error, 1)
        except APIError:
            pass
        else:
            self.fail('request() should not retry on client errors')

        # test for number of exceptions raise > retries value
        consumer = Consumer(None, 'testsecret', retries=3)
        self._test_request_retry(consumer, APIError(
            500, 'code', 'Internal Server Error'), 3)

    def test_pause(self):
        consumer = Consumer(None, 'testsecret')
        consumer.pause()
        self.assertFalse(consumer.running)

    def test_max_batch_size(self):
        q = Queue()
        consumer = Consumer(
            q, 'testsecret', upload_size=100000, upload_interval=3)
        track = {
            'type': 'track',
            'event': 'python event',
            'userId': 'userId'
        }
        msg_size = len(json.dumps(track).encode())
        # number of messages in a maximum-size batch
        n_msgs = int(475000 / msg_size)

        def mock_post_fn(_, data, **kwargs):
            res = mock.Mock()
            res.status_code = 200
            self.assertTrue(len(data.encode()) < 500000,
                            'batch size (%d) exceeds 500KB limit'
                            % len(data.encode()))
            return res

        with mock.patch('segment.analytics.request._session.post',
                        side_effect=mock_post_fn) as mock_post:
            consumer.start()
            for _ in range(0, n_msgs + 2):
                q.put(track)
            q.join()
            self.assertEqual(mock_post.call_count, 2)

    @classmethod
    def test_proxies(cls):
        proxies = {'http': '203.243.63.16:80', 'https': '203.243.63.16:80'}
        consumer = Consumer(None, 'testsecret', proxies=proxies)
        track = {
            'type': 'track',
            'event': 'python event',
            'userId': 'userId'
        }

        def mock_post_fn(*args, **kwargs):
            res = mock.Mock()
            res.status_code = 200
            res.json.return_value = {'code': 'success', 'message': 'success'}
            return res

        with mock.patch('segment.analytics.request._session.post', side_effect=mock_post_fn) as mock_post:
            consumer.request([track])
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            cls().assertIn('proxies', kwargs)
            cls().assertEqual(kwargs['proxies'], proxies)

    def test_retry_count_header_increments(self):
        """Test that X-Retry-Count header increments on each retry"""
        consumer = Consumer(None, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        retry_counts = []

        def mock_post_fn(*args, **kwargs):
            retry_counts.append(kwargs.get('retry_count', 0))
            if len(retry_counts) < 3:
                raise APIError(500, 'error', 'Server Error')
            # Success on third attempt
            return mock.Mock(status_code=200)

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            consumer.request([track])

        # Should have been called 3 times with retry counts 0, 1, 2
        self.assertEqual(retry_counts, [0, 1, 2])

    def test_non_retryable_4xx_status_codes(self):
        """Test that non-retryable 4xx errors are not retried"""
        consumer = Consumer(None, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        non_retryable_codes = [400, 401, 403, 404, 413, 422]

        for status_code in non_retryable_codes:
            call_count = 0

            def mock_post_fn(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                raise APIError(status_code, 'error', f'Client Error {status_code}')

            with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
                try:
                    consumer.request([track])
                except APIError as e:
                    self.assertEqual(e.status, status_code)

                # Should only be called once (no retries)
                self.assertEqual(call_count, 1, f'Status {status_code} should not be retried')

    def test_retryable_4xx_status_codes(self):
        """Test that retryable 4xx errors are retried (429 without Retry-After uses backoff too)"""
        consumer = Consumer(None, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        retryable_codes = [408, 410, 429, 460]

        for status_code in retryable_codes:
            call_count = 0

            def mock_post_fn(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise APIError(status_code, 'error', f'Retryable Error {status_code}')
                # Success on third attempt
                return mock.Mock(status_code=200)

            with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
                with mock.patch('time.sleep'):  # Mock sleep to speed up test
                    consumer.request([track])

                # Should have been called 3 times
                self.assertEqual(call_count, 3, f'Status {status_code} should be retried')

    def test_non_retryable_5xx_status_codes(self):
        """Test that non-retryable 5xx errors are not retried"""
        consumer = Consumer(None, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        non_retryable_codes = [501, 505]

        for status_code in non_retryable_codes:
            call_count = 0

            def mock_post_fn(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                raise APIError(status_code, 'error', f'Server Error {status_code}')

            with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
                try:
                    consumer.request([track])
                except APIError as e:
                    self.assertEqual(e.status, status_code)

                # Should only be called once (no retries)
                self.assertEqual(call_count, 1, f'Status {status_code} should not be retried')

    def test_retryable_5xx_status_codes(self):
        """Test that retryable 5xx errors are retried"""
        consumer = Consumer(None, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        retryable_codes = [500, 502, 503, 504]

        for status_code in retryable_codes:
            call_count = 0

            def mock_post_fn(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise APIError(status_code, 'error', f'Server Error {status_code}')
                # Success on third attempt
                return mock.Mock(status_code=200)

            with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
                with mock.patch('time.sleep'):  # Mock sleep to speed up test
                    consumer.request([track])

                # Should have been called 3 times
                self.assertEqual(call_count, 3, f'Status {status_code} should be retried')

    def test_429_sets_rate_limit_state_with_retry_after(self):
        """Test that 429 with Retry-After sets rate_limited_until on consumer"""
        consumer = Consumer(None, 'testsecret', retries=2)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        def mock_post_fn(*args, **kwargs):
            response = mock.Mock()
            response.headers = {'Retry-After': '10'}
            error = APIError(429, 'rate_limit', 'Too Many Requests')
            error.response = response
            raise error

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with self.assertRaises(APIError) as ctx:
                consumer.request([track])
            self.assertEqual(ctx.exception.status, 429)

        # Rate-limit state should be set
        self.assertIsNotNone(consumer.rate_limited_until)
        self.assertIsNotNone(consumer.rate_limit_start_time)
        # rate_limited_until should be ~10 seconds in the future
        self.assertGreater(consumer.rate_limited_until, time.time() + 5)

    def test_retry_after_capped_at_300_seconds(self):
        """Test that Retry-After delay is capped at 300 seconds when setting rate-limit state"""
        consumer = Consumer(None, 'testsecret', retries=2)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        def mock_post_fn(*args, **kwargs):
            response = mock.Mock()
            response.headers = {'Retry-After': '600'}  # 10 minutes
            error = APIError(429, 'rate_limit', 'Too Many Requests')
            error.response = response
            raise error

        now = time.time()
        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with self.assertRaises(APIError):
                consumer.request([track])

        # rate_limited_until should be capped at ~300s from now (not 600s)
        self.assertIsNotNone(consumer.rate_limited_until)
        self.assertLessEqual(consumer.rate_limited_until, now + 310)
        self.assertGreater(consumer.rate_limited_until, now + 290)

    def test_408_and_503_use_backoff(self):
        """Test that 408 and 503 use exponential backoff"""
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        for status_code in [408, 503]:
            consumer = Consumer(None, 'testsecret', retries=2)
            call_count = 0
            sleep_durations = []

            def mock_post_fn(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    response = mock.Mock()
                    response.headers = {'Retry-After': '5'}
                    error = APIError(status_code, 'error', 'Error')
                    error.response = response
                    raise error
                return mock.Mock(status_code=200)

            def mock_sleep(duration):
                sleep_durations.append(duration)

            with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
                with mock.patch('time.sleep', side_effect=mock_sleep):
                    consumer.request([track])

            # Should use backoff delay (0 for first retry), NOT the Retry-After value of 5
            self.assertEqual(call_count, 2)
            self.assertEqual(len(sleep_durations), 1)
            self.assertEqual(sleep_durations[0], 0, f'{status_code} should use backoff, not Retry-After')

    def test_exponential_backoff_with_jitter(self):
        """Test that exponential backoff is used for retries without Retry-After"""
        consumer = Consumer(None, 'testsecret', retries=4)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0
        sleep_durations = []

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count <= 3:
                raise APIError(500, 'error', 'Server Error')

            return mock.Mock(status_code=200)

        def mock_sleep(duration):
            sleep_durations.append(duration)

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep', side_effect=mock_sleep):
                consumer.request([track])

        # Should have 3 backoff delays
        self.assertEqual(len(sleep_durations), 3)

        # Delays should be increasing (exponential)
        # First: 0s (immediate), Second: ~0.5s, Third: ~1s (with jitter)
        self.assertEqual(sleep_durations[0], 0)  # First retry is immediate
        self.assertGreater(sleep_durations[1], 0.4)
        self.assertLess(sleep_durations[1], 0.6)
        self.assertGreater(sleep_durations[2], 0.9)
        self.assertLess(sleep_durations[2], 1.2)

    def test_fatal_error_not_retried(self):
        """Test that FatalError is not retried"""
        consumer = Consumer(None, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise FatalError('Fatal error occurred')

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with self.assertRaises(FatalError):
                consumer.request([track])

        # Should only be called once (no retries)
        self.assertEqual(call_count, 1)

    def test_max_retries_exhausted(self):
        """Test that request fails after max retries exhausted"""
        consumer = Consumer(None, 'testsecret', retries=2)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Always fail with retryable error
            raise APIError(500, 'error', 'Server Error')

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep'):  # Mock sleep to speed up test
                try:
                    consumer.request([track])
                except APIError as e:
                    self.assertEqual(e.status, 500)

        # Should be called 3 times (initial + 2 retries)
        self.assertEqual(call_count, 3)

    def test_first_request_has_retry_count_zero(self):
        """T01: First successful request includes X-Retry-Count=0"""
        consumer = Consumer(None, 'testsecret')
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        retry_count = None

        def mock_post_fn(*args, **kwargs):
            nonlocal retry_count
            retry_count = kwargs.get('retry_count')
            return mock.Mock(status_code=200)

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            consumer.request([track])

        # First request should have retry_count=0
        self.assertEqual(retry_count, 0)

    def test_429_without_retry_after_uses_counted_backoff(self):
        """429 without Retry-After uses counted backoff (not pipeline blocking)"""
        consumer = Consumer(None, 'testsecret', retries=2)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                error = APIError(429, 'rate_limit', 'Too Many Requests')
                error.response = mock.Mock()
                error.response.headers = {}  # No Retry-After
                raise error
            return mock.Mock(status_code=200)

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep'):
                consumer.request([track])

        # Should retry with backoff (3 calls: initial + 2 retries)
        self.assertEqual(call_count, 3)
        # Rate-limit state should NOT be set (no pipeline blocking)
        self.assertIsNone(consumer.rate_limited_until)

    def test_408_without_retry_after_uses_backoff(self):
        """T10: 408 without Retry-After header uses backoff retry"""
        consumer = Consumer(None, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0
        retry_counts = []
        sleep_duration = None

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            retry_counts.append(kwargs.get('retry_count', 0))

            if call_count == 1:
                # 408 without Retry-After header
                error = APIError(408, 'timeout', 'Request Timeout')
                error.response = mock.Mock()
                error.response.headers = {}  # No Retry-After
                raise error

            return mock.Mock(status_code=200)

        def mock_sleep(duration):
            nonlocal sleep_duration
            sleep_duration = duration

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep', side_effect=mock_sleep):
                consumer.request([track])

        # Should have two attempts
        self.assertEqual(call_count, 2)
        self.assertEqual(retry_counts, [0, 1])

        # First retry should be immediate (0s delay)
        self.assertIsNotNone(sleep_duration)
        if sleep_duration is not None:
            self.assertEqual(sleep_duration, 0)

    def test_network_error_retried_with_backoff(self):
        """T15: Network/IO error is retried with backoff"""
        consumer = Consumer(None, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0
        retry_counts = []
        sleep_duration = None

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            retry_counts.append(kwargs.get('retry_count', 0))

            if call_count == 1:
                # Network error
                raise ConnectionError('Network connection failed')

            return mock.Mock(status_code=200)

        def mock_sleep(duration):
            nonlocal sleep_duration
            sleep_duration = duration

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep', side_effect=mock_sleep):
                consumer.request([track])

        # Should have two attempts
        self.assertEqual(call_count, 2)
        self.assertEqual(retry_counts, [0, 1])

        # First retry should be immediate (0s delay)
        self.assertIsNotNone(sleep_duration)
        if sleep_duration is not None:
            self.assertEqual(sleep_duration, 0)

    def test_511_not_retryable_without_oauth(self):
        """T17: 511 is NOT retried when OauthManager is not configured"""
        consumer = Consumer(None, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise APIError(511, 'auth_required', 'Network Authentication Required')

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with self.assertRaises(APIError) as ctx:
                consumer.request([track])
            self.assertEqual(ctx.exception.status, 511)

        # Should only be called once (not retried without OAuth)
        self.assertEqual(call_count, 1)

    def test_511_retryable_with_oauth(self):
        """T17: 511 IS retried when OauthManager is configured"""
        oauth_manager = mock.Mock()
        consumer = Consumer(None, 'testsecret', retries=3, oauth_manager=oauth_manager)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise APIError(511, 'auth_required', 'Network Authentication Required')
            return mock.Mock(status_code=200)

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep'):
                consumer.request([track])

        # Should have been called 3 times (511 is retryable with OAuth)
        self.assertEqual(call_count, 3)

    def test_429_with_retry_after_does_not_count_against_backoff_budget(self):
        """429 with Retry-After raises immediately (pipeline blocking) without consuming backoff budget"""
        consumer = Consumer(None, 'testsecret', retries=1)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            error = APIError(429, 'rate_limit', 'Too Many Requests')
            error.response = mock.Mock()
            error.response.headers = {'Retry-After': '1'}
            raise error

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with self.assertRaises(APIError) as ctx:
                consumer.request([track])
            self.assertEqual(ctx.exception.status, 429)

        # 429 with Retry-After raises on first attempt (pipeline blocking)
        self.assertEqual(call_count, 1)

    def test_413_payload_too_large_not_retried(self):
        """T12: 413 Payload Too Large is non-retryable (won't succeed on retry)"""
        consumer = Consumer(None, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise APIError(413, 'payload_too_large', 'Payload Too Large')

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            try:
                consumer.request([track])
            except APIError as e:
                self.assertEqual(e.status, 413)

        # Should only be called once (no retries)
        self.assertEqual(call_count, 1)

    def test_t04_429_halts_upload_iteration(self):
        """T04: 429 halts current upload iteration — batch is re-queued, not dropped"""
        q = Queue()
        consumer = Consumer(q, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        # Put a message in the queue
        q.put(track)

        call_count = 0

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            response = mock.Mock()
            response.headers = {'Retry-After': '10'}
            error = APIError(429, 'rate_limit', 'Too Many Requests')
            error.response = response
            raise error

        on_error_called = []

        def on_error(e, batch):
            on_error_called.append((e, batch))

        consumer.on_error = on_error

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep'):
                result = consumer.upload()

        # upload() should return False (not successful)
        self.assertFalse(result)
        # request() should have been called exactly once
        self.assertEqual(call_count, 1)
        # on_error should NOT have been called (batch was re-queued, not dropped)
        self.assertEqual(len(on_error_called), 0)
        # Rate-limit state should be set
        self.assertIsNotNone(consumer.rate_limited_until)
        self.assertIsNotNone(consumer.rate_limit_start_time)

    def test_429_without_retry_after_does_not_requeue_batch(self):
        """429 without Retry-After is treated as normal failure in upload() and is not re-queued"""
        q = Queue()
        consumer = Consumer(q, 'testsecret', retries=0)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}
        q.put(track)

        def mock_post_fn(*args, **kwargs):
            error = APIError(429, 'rate_limit', 'Too Many Requests')
            error.response = mock.Mock()
            error.response.headers = {}
            raise error

        on_error_called = []

        def on_error(e, batch):
            on_error_called.append((e, batch))

        consumer.on_error = on_error

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep'):
                result = consumer.upload()

        self.assertFalse(result)
        self.assertEqual(len(on_error_called), 1)
        self.assertIsNone(consumer.rate_limited_until)
        self.assertEqual(q.qsize(), 0)

    def test_retry_after_zero_sets_rate_limit_state(self):
        """429 with Retry-After: 0 still sets rate-limit state for consistent pipeline handling"""
        consumer = Consumer(None, 'testsecret', retries=1)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        def mock_post_fn(*args, **kwargs):
            response = mock.Mock()
            response.headers = {'Retry-After': '0'}
            error = APIError(429, 'rate_limit', 'Too Many Requests')
            error.response = response
            raise error

        before = time.time()
        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with self.assertRaises(APIError) as ctx:
                consumer.request([track])
            self.assertEqual(ctx.exception.status, 429)
        after = time.time()

        self.assertIsNotNone(consumer.rate_limited_until)
        self.assertIsNotNone(consumer.rate_limit_start_time)
        self.assertGreaterEqual(consumer.rate_limited_until, before)
        self.assertLessEqual(consumer.rate_limited_until, after + 0.1)

    def test_t19_max_total_backoff_duration(self):
        """T19: Gives up after maxTotalBackoffDuration elapsed"""
        consumer = Consumer(None, 'testsecret', retries=1000,
                            max_total_backoff_duration=5)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0
        fake_time = [100.0]  # Start time

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise APIError(500, 'error', 'Server Error')

        original_time = time.time

        def mock_time():
            # Advance time by 3 seconds on each call after the first
            result = fake_time[0]
            fake_time[0] += 3.0
            return result

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep'):
                with mock.patch('time.time', side_effect=mock_time):
                    with self.assertRaises(APIError) as ctx:
                        consumer.request([track])
                    self.assertEqual(ctx.exception.status, 500)

        # With max_total_backoff_duration=5 and time advancing 3s per call:
        # Attempt 1: fails, first_failure_time set at 100, time now 103
        # Attempt 2: fails, time is 106, 106-100=6 > 5, exceeds duration
        # So should be called exactly 2 times
        self.assertEqual(call_count, 2)

    def test_t20_max_rate_limit_duration(self):
        """T20: Rate-limited state clears and batch is dropped after maxRateLimitDuration"""
        q = Queue()
        consumer = Consumer(q, 'testsecret', retries=3,
                            max_rate_limit_duration=10)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        # Pre-set rate-limit state as if we entered it 15 seconds ago
        now = time.time()
        consumer.rate_limit_start_time = now - 15  # 15s ago, exceeds 10s limit
        consumer.rate_limited_until = now + 5  # Would still be rate-limited

        # Put a message in the queue
        q.put(track)

        on_error_called = []

        def on_error(e, batch):
            on_error_called.append((e, batch))

        consumer.on_error = on_error

        # upload() should detect duration exceeded, clear state, drop batch
        result = consumer.upload()

        self.assertFalse(result)
        # Rate-limit state should be cleared
        self.assertIsNone(consumer.rate_limited_until)
        self.assertIsNone(consumer.rate_limit_start_time)
        # on_error should have been called (batch was dropped)
        self.assertEqual(len(on_error_called), 1)

    def test_rate_limit_state_cleared_on_success(self):
        """Rate-limit state is cleared after a successful request"""
        q = Queue()
        consumer = Consumer(q, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        # Set rate-limit state
        consumer.rate_limited_until = time.time() - 1  # Already expired
        consumer.rate_limit_start_time = time.time() - 10

        q.put(track)

        with mock.patch('segment.analytics.consumer.post', return_value=mock.Mock(status_code=200)):
            result = consumer.upload()

        self.assertTrue(result)
        # Rate-limit state should be cleared on success
        self.assertIsNone(consumer.rate_limited_until)
        self.assertIsNone(consumer.rate_limit_start_time)
