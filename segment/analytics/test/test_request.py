from datetime import datetime, date
import unittest
import json
import requests
from unittest import mock

from segment.analytics.request import post, DatetimeSerializer


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
