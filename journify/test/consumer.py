import logging
import unittest
import json
import time
from unittest import mock

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from journify.consumer import Consumer, MAX_MSG_SIZE
from journify.request import APIError


if __name__ == '__main__':
    unittest.main()


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
        consumer = Consumer(q, 'wk_test_2N0WZTEtnQZxBwdvrdMUJwFyIa1')
        track = {
            'type': 'track',
            'event': 'python event',
            'userId': 'userId',
            'messageId': 'messageId',
            'timestamp': '2002-10-02T10:00:00-05:00'
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
        consumer = Consumer(q, 'wk_test_2N0WZTEtnQZxBwdvrdMUJwFyIa1', upload_size=10,
                            upload_interval=upload_interval)
        with mock.patch('journify.consumer.post') as mock_post:
            mock_post.return_value = {'status_code': 200}
            consumer.start()
            for i in range(0, 3):
                track = {
                    'type': 'track',
                    'event': 'python event %d' % i,
                    'userId': 'userId',
                    'messageId': 'messageId',
                    'timestamp': '2002-10-02T10:00:00-05:00'
                }
                q.put(track)
                time.sleep(upload_interval * 1.1)
            self.assertEqual(mock_post.call_count, 3)

    @classmethod
    def test_request(cls):
        consumer = Consumer(None, 'wk_test_2N0WZTEtnQZxBwdvrdMUJwFyIa1')
        track = {
            'type': 'track',
            'event': 'python event',
            'userId': 'userId',
            'messageId': 'messageId',
            'timestamp': '2002-10-02T10:00:00-05:00'
        }
        consumer.request([track])

    def test_pause(self):
        consumer = Consumer(None, 'wk_test_2N0WZTEtnQZxBwdvrdMUJwFyIa1')
        consumer.pause()
        self.assertFalse(consumer.running)