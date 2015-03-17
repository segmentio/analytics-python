import unittest

import segment


class TestModule(unittest.TestCase):

    def failed(self):
        self.failed = True

    def setUp(self):
        self.failed = False
        segment.write_key = 'testsecret'
        segment.on_error = self.failed

    def test_no_write_key(self):
        segment.write_key = None
        self.assertRaises(Exception, segment.track)

    def test_track(self):
        segment.track('userId', 'python module event')
        segment.flush()

    def test_identify(self):
        segment.identify('userId', { 'email': 'user@email.com' })
        segment.flush()

    def test_group(self):
        segment.group('userId', 'groupId')
        segment.flush()

    def test_alias(self):
        segment.alias('previousId', 'userId')
        segment.flush()

    def test_page(self):
        segment.page('userId')
        segment.flush()

    def test_screen(self):
        segment.screen('userId')
        segment.flush()

    def test_flush(self):
        segment.flush()
