from datetime import datetime, date
import unittest
import json
import requests
import base64
from unittest import mock

from segment.analytics.request import post, DatetimeSerializer, parse_retry_after, APIError


class TestRequests(unittest.TestCase):

    def test_valid_request(self):
        res = post('testsecret', batch=[{
            'userId': 'userId',
            'event': 'python event',
            'type': 'track'
        }])
        self.assertEqual(res.status_code, 200)

    def test_invalid_request_error(self):
        self.assertRaises(Exception, post, 'testsecret',
                          'https://api.segment.io', False, '[{]')

    def test_invalid_host(self):
        self.assertRaises(Exception, post, 'testsecret',
                          'api.segment.io/', batch=[])

    def test_datetime_serialization(self):
        data = {'created': datetime(2012, 3, 4, 5, 6, 7, 891011)}
        result = json.dumps(data, cls=DatetimeSerializer)
        self.assertEqual(result, '{"created": "2012-03-04T05:06:07.891011"}')

    def test_date_serialization(self):
        today = date.today()
        data = {'created': today}
        result = json.dumps(data, cls=DatetimeSerializer)
        expected = '{"created": "%s"}' % today.isoformat()
        self.assertEqual(result, expected)

    def test_should_not_timeout(self):
        res = post('testsecret', batch=[{
            'userId': 'userId',
            'event': 'python event',
            'type': 'track'
        }], timeout=15)
        self.assertEqual(res.status_code, 200)

    def test_should_timeout(self):
        with self.assertRaises(requests.ReadTimeout):
            post('testsecret', batch=[{
                'userId': 'userId',
                'event': 'python event',
                'type': 'track'
            }], timeout=0.0001)

    def test_proxies(self):
        proxies = {'http': '203.243.63.16:80', 'https': '203.243.63.16:80'}
        def mock_post_fn(*args, **kwargs):
            res = mock.Mock()
            res.status_code = 200
            res.json.return_value = {'code': 'success', 'message': 'success'}
            return res

        with mock.patch('segment.analytics.request._session.post', side_effect=mock_post_fn) as mock_post:
            res = post('testsecret', proxies= proxies, batch=[{
                'userId': 'userId',
                'event': 'python event',
                'type': 'track'
            }])
            self.assertEqual(res.status_code, 200)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn('proxies', kwargs)
            self.assertEqual(kwargs['proxies'], proxies)

    def test_authorization_header_basic_auth(self):
        """Test that Basic Authorization header is added when no OAuth manager"""
        def mock_post_fn(*args, **kwargs):
            res = mock.Mock()
            res.status_code = 200
            return res

        with mock.patch('segment.analytics.request._session.post', side_effect=mock_post_fn) as mock_post:
            post('testsecret', batch=[{
                'userId': 'userId',
                'event': 'python event',
                'type': 'track'
            }])

            args, kwargs = mock_post.call_args
            headers = kwargs['headers']
            self.assertIn('Authorization', headers)

            # Verify it's Basic auth with correct encoding
            expected_credentials = base64.b64encode(b'testsecret:').decode('utf-8')
            expected_auth = f'Basic {expected_credentials}'
            self.assertEqual(headers['Authorization'], expected_auth)

    def test_authorization_header_oauth(self):
        """Test that Bearer Authorization header is used with OAuth manager"""
        oauth_manager = mock.Mock()
        oauth_manager.get_token.return_value = 'test_token_123'

        def mock_post_fn(*args, **kwargs):
            res = mock.Mock()
            res.status_code = 200
            return res

        with mock.patch('segment.analytics.request._session.post', side_effect=mock_post_fn) as mock_post:
            post('testsecret', oauth_manager=oauth_manager, batch=[{
                'userId': 'userId',
                'event': 'python event',
                'type': 'track'
            }])

            args, kwargs = mock_post.call_args
            headers = kwargs['headers']
            self.assertIn('Authorization', headers)
            self.assertEqual(headers['Authorization'], 'Bearer test_token_123')

    def test_x_retry_count_header(self):
        """Test that X-Retry-Count header is omitted on first attempt and included on retries"""
        def mock_post_fn(*args, **kwargs):
            res = mock.Mock()
            res.status_code = 200
            return res

        with mock.patch('segment.analytics.request._session.post', side_effect=mock_post_fn) as mock_post:
            # Test with retry_count=0 (first attempt) — header should be absent
            post('testsecret', retry_count=0, batch=[{
                'userId': 'userId',
                'event': 'python event',
                'type': 'track'
            }])

            args, kwargs = mock_post.call_args
            headers = kwargs['headers']
            self.assertNotIn('X-Retry-Count', headers)

        with mock.patch('segment.analytics.request._session.post', side_effect=mock_post_fn) as mock_post:
            # Test with retry_count=5
            post('testsecret', retry_count=5, batch=[{
                'userId': 'userId',
                'event': 'python event',
                'type': 'track'
            }])

            args, kwargs = mock_post.call_args
            headers = kwargs['headers']
            self.assertEqual(headers['X-Retry-Count'], '5')

    def test_parse_retry_after_integer(self):
        """Test parsing Retry-After header with integer seconds"""
        response = mock.Mock()
        response.headers = {'Retry-After': '30'}
        result = parse_retry_after(response)
        self.assertEqual(result, 30)

    def test_parse_retry_after_capped(self):
        """Test that Retry-After is capped at 300 seconds"""
        response = mock.Mock()
        response.headers = {'Retry-After': '600'}
        result = parse_retry_after(response)
        self.assertEqual(result, 300)

    def test_parse_retry_after_missing(self):
        """Test parsing when Retry-After header is missing"""
        response = mock.Mock()
        response.headers = {}
        result = parse_retry_after(response)
        self.assertIsNone(result)

    def test_parse_retry_after_invalid(self):
        """Test parsing with invalid Retry-After header"""
        response = mock.Mock()
        response.headers = {'Retry-After': 'invalid'}
        result = parse_retry_after(response)
        self.assertIsNone(result)

    def test_oauth_token_cleared_on_511(self):
        """Test that OAuth token is cleared on 511 status"""
        oauth_manager = mock.Mock()
        oauth_manager.get_token.return_value = 'test_token'

        def mock_post_fn(*args, **kwargs):
            res = mock.Mock()
            res.status_code = 511
            res.json.return_value = {'code': 'error', 'message': 'Network Authentication Required'}
            return res

        with mock.patch('segment.analytics.request._session.post', side_effect=mock_post_fn):
            with self.assertRaises(APIError):
                post('testsecret', oauth_manager=oauth_manager, batch=[{
                    'userId': 'userId',
                    'event': 'python event',
                    'type': 'track'
                }])

            # Verify clear_token was called
            oauth_manager.clear_token.assert_called_once()

    def test_api_error_includes_response(self):
        """Test that APIError includes the response object"""
        def mock_post_fn(*args, **kwargs):
            res = mock.Mock()
            res.status_code = 429
            res.json.return_value = {'code': 'rate_limit', 'message': 'Too Many Requests'}
            return res

        with mock.patch('segment.analytics.request._session.post', side_effect=mock_post_fn):
            try:
                post('testsecret', batch=[{
                    'userId': 'userId',
                    'event': 'python event',
                    'type': 'track'
                }])
            except APIError as e:
                self.assertEqual(e.status, 429)
                self.assertIsNotNone(e.response)
            else:
                self.fail('Expected APIError to be raised')
