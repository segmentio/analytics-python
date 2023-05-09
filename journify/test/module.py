import unittest

import journify


class TestModule(unittest.TestCase):

    # def failed(self):
    #     self.failed = True

    def setUp(self):
        self.failed = False
        journify.write_key = 'testsecret'
        journify.on_error = self.failed

    def test_no_write_key(self):
        journify.write_key = None
        self.assertRaises(Exception, journify.track)

    def test_no_host(self):
        journify.host = None
        self.assertRaises(Exception, journify.track)

    def test_track(self):
        journify.track('userId', 'python module event')
        journify.flush()

    def test_identify(self):
        journify.identify('userId', {'email': 'user@email.com'})
        journify.flush()

    def test_group(self):
        journify.group('userId', 'groupId')
        journify.flush()

    def test_page(self):
        journify.page('userId')
        journify.flush()

    def test_flush(self):
        journify.flush()