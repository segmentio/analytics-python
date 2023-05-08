import unittest
import pkgutil
import logging
import sys
import journify


def all_names():
    for _, modname, _ in pkgutil.iter_modules(__path__):
        yield 'journify.test.' + modname


def all():
    logging.basicConfig(stream=sys.stderr)
    return unittest.defaultTestLoader.loadTestsFromNames(all_names())


class TestInit(unittest.TestCase):
    def test_writeKey(self):
        self.assertIsNone(journify.default_client)
        journify.flush()
        self.assertEqual(journify.default_client.write_key, 'test-init')

    def test_debug(self):
        self.assertIsNone(journify.default_client)
        journify.debug = True
        journify.flush()
        self.assertTrue(journify.default_client.debug)
        journify.default_client = None
        journify.debug = False
        journify.flush()
        self.assertFalse(journify.default_client.debug)

    def test_gzip(self):
        self.assertIsNone(journify.default_client)
        journify.gzip = True
        journify.flush()
        self.assertTrue(journify.default_client.gzip)
        journify.default_client = None
        journify.gzip = False
        journify.flush()
        self.assertFalse(journify.default_client.gzip)

    def test_host(self):
        self.assertIsNone(journify.default_client)
        journify.host = 'test-host'
        journify.flush()
        self.assertEqual(journify.default_client.host, 'test-host')

    def test_max_queue_size(self):
        self.assertIsNone(journify.default_client)
        journify.max_queue_size = 1337
        journify.flush()
        self.assertEqual(journify.default_client.queue.maxsize, 1337)

    def test_max_retries(self):
        self.assertIsNone(journify.default_client)
        client = journify.Client('testsecret', max_retries=42)
        for consumer in client.consumers:
            self.assertEqual(consumer.retries, 42)

    def test_sync_mode(self):
        self.assertIsNone(journify.default_client)
        journify.sync_mode = True
        journify.flush()
        self.assertTrue(journify.default_client.sync_mode)
        journify.default_client = None
        journify.sync_mode = False
        journify.flush()
        self.assertFalse(journify.default_client.sync_mode)

    def test_timeout(self):
        self.assertIsNone(journify.default_client)
        journify.timeout = 1.234
        journify.flush()
        self.assertEqual(journify.default_client.timeout, 1.234)

    def setUp(self):
        journify.write_key = 'test-init'
        journify.default_client = None
