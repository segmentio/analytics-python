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

        # we should retry on HTTP 429 errors
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
        """Test that retryable 4xx errors are retried"""
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

    def test_retry_after_header_support(self):
        """Test that Retry-After header is respected and doesn't count against retry budget"""
        consumer = Consumer(None, 'testsecret', retries=2)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0
        sleep_durations = []

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count <= 3:
                # Return 429 with Retry-After for first 3 attempts
                response = mock.Mock()
                response.headers = {'Retry-After': '10'}
                error = APIError(429, 'rate_limit', 'Too Many Requests')
                error.response = response
                raise error

            # Success on 4th attempt
            return mock.Mock(status_code=200)

        def mock_sleep(duration):
            sleep_durations.append(duration)

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep', side_effect=mock_sleep):
                consumer.request([track])

        # Should succeed after 4 attempts (3 Retry-After, then success)
        self.assertEqual(call_count, 4)

        # First 3 sleeps should be for Retry-After (10 seconds each)
        self.assertEqual(sleep_durations[:3], [10, 10, 10])

    def test_retry_after_capped_at_300_seconds(self):
        """Test that Retry-After delay is capped at 300 seconds"""
        consumer = Consumer(None, 'testsecret', retries=2)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0
        sleep_duration = None

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # Return 429 with large Retry-After
                response = mock.Mock()
                response.headers = {'Retry-After': '600'}  # 10 minutes
                error = APIError(429, 'rate_limit', 'Too Many Requests')
                error.response = response
                raise error

            # Success on 2nd attempt
            return mock.Mock(status_code=200)

        def mock_sleep(duration):
            nonlocal sleep_duration
            sleep_duration = duration

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep', side_effect=mock_sleep):
                consumer.request([track])

        # Sleep should be capped at 300 seconds
        self.assertEqual(sleep_duration, 300)

    def test_retry_after_for_408_and_503(self):
        """Test that Retry-After is respected for 408 and 503 status codes"""
        consumer = Consumer(None, 'testsecret', retries=2)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        for status_code in [408, 503]:
            call_count = 0
            sleep_duration = None

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
                nonlocal sleep_duration
                sleep_duration = duration

            with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
                with mock.patch('time.sleep', side_effect=mock_sleep):
                    consumer.request([track])

            self.assertEqual(sleep_duration, 5, f'Retry-After should be respected for {status_code}')

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

    def test_429_without_retry_after_uses_backoff(self):
        """T09: 429 without Retry-After header uses backoff retry"""
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
                # 429 without Retry-After header
                error = APIError(429, 'rate_limit', 'Too Many Requests')
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

    def test_511_is_retryable(self):
        """T05: 511 status code is retryable (part of 5xx family, not in non-retryable list)"""
        consumer = Consumer(None, 'testsecret', retries=3)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0
        retry_counts = []

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            retry_counts.append(kwargs.get('retry_count', 0))

            if call_count < 3:
                raise APIError(511, 'auth_required', 'Network Authentication Required')

            return mock.Mock(status_code=200)

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep'):  # Mock sleep to speed up test
                consumer.request([track])

        # Should have been called 3 times (511 is retryable)
        self.assertEqual(call_count, 3)
        self.assertEqual(retry_counts, [0, 1, 2])

    def test_retry_after_not_counted_against_backoff_budget(self):
        """T17: Retry-After attempts don't consume backoff retry budget"""
        consumer = Consumer(None, 'testsecret', retries=1)
        track = {'type': 'track', 'event': 'python event', 'userId': 'userId'}

        call_count = 0
        retry_counts = []

        def mock_post_fn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            retry_counts.append(kwargs.get('retry_count', 0))

            if call_count <= 2:
                # First two: 429 with Retry-After (shouldn't count against budget)
                response = mock.Mock()
                response.headers = {'Retry-After': '1'}
                error = APIError(429, 'rate_limit', 'Too Many Requests')
                error.response = response
                raise error
            elif call_count == 3:
                # Third: 500 without Retry-After (counts against budget)
                raise APIError(500, 'error', 'Server Error')

            # Success on 4th attempt
            return mock.Mock(status_code=200)

        with mock.patch('segment.analytics.consumer.post', side_effect=mock_post_fn):
            with mock.patch('time.sleep'):  # Mock sleep to speed up test
                consumer.request([track])

        # Should succeed after 4 attempts:
        # - 2 Retry-After attempts (don't count against budget)
        # - 1 backoff attempt (counts against budget = 1)
        # - 1 final backoff attempt (counts against budget = 1, limit reached)
        # Actually wait, with retries=1, we have max_backoff_attempts=2
        # So: 2 Retry-After + 2 backoff attempts = 4 total
        self.assertEqual(call_count, 4)
        self.assertEqual(retry_counts, [0, 1, 2, 3])

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
