import unittest

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from journify.consumer import Consumer, MAX_MSG_SIZE


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
