from datetime import datetime, date
import unittest
import json
import requests

from journify.request import post, DatetimeSerializer


class TestRequests(unittest.TestCase):
    def test_valid_request(self):
        res = post('wk_test_2N0WZTEtnQZxBwdvrdMUJwFyIa1', batch=[{
            'userId': 'userId',
            'event': 'python event',
            'type': 'track',
            'messageId': 'messageId',
            'timestamp': '2002-10-02T10:00:00-05:00'
        }])
        self.assertEqual(res.status_code, 202)

    def test_invalid_request_error(self):
        self.assertRaises(Exception, post, 'wk_test_2N0WZTEtnQZxBwdvrdMUJwFyIa1',
                          'https://t.journify.io', False, '[{]')

    def test_invalid_host(self):
        self.assertRaises(Exception, post, 'wk_test_2N0WZTEtnQZxBwdvrdMUJwFyIa1',
                          't.journify.io/', batch=[])

    def test_datetime_serialization(self):
        data = {'created': datetime(2012, 3, 4, 5, 6, 7, 891011)}
        result = json.dumps(data, cls=DatetimeSerializer)
        self.assertEqual(result, '{"created": "2012-03-04T05:06:07.891011"}')

    def test_date_serialization(self):
        today = date.today()
        data = {'created': today}
        result = json.dumps(data, cls=DatetimeSerializer)
        expected = f'{{"created": "{today.isoformat()}"}}'
        self.assertEqual(result, expected)

    def test_should_not_timeout(self):
        res = post('wk_test_2N0WZTEtnQZxBwdvrdMUJwFyIa1', batch=[{
            'userId': 'userId',
            'event': 'python event',
            'type': 'track',
            'messageId': 'messageId',
            'timestamp': '2002-10-02T10:00:00-05:00'
        }], timeout=15)
        self.assertEqual(res.status_code, 202)

    def test_should_timeout(self):
        with self.assertRaises(requests.ReadTimeout):
            post('wk_test_2N0WZTEtnQZxBwdvrdMUJwFyIa1', batch=[{
                'userId': 'userId',
                'event': 'python event',
                'type': 'track',
                'messageId': 'messageId',
                'timestamp': '2002-10-02T10:00:00-05:00'
            }], timeout=0.0001)