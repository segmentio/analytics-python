
from date import today

import unittest

import segmentio


class SegmentioBasicTests(unittest.TestCase):

    def setUp(self):
        segmentio.host = 'http://localhost:81'
        segmentio.api_key = 'fakeid'

    def basic_identify(self):
        segmentio.identify('random_session_id', 'ilya@segment.io', {
            "Subscription Plan": "Free",
            "Friends": 30
        })

        self.assertTrue(segmentio.stats.identifies == 1)

    def basic_track(self):
        segmentio.track('random_session_id', 'ilya@segment.io', 'Played a Song', {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        })

        self.assertTrue(segmentio.stats.tracks == 1)

    def full_identify(self):

        traits = {
            "Subscription Plan": "Free",
            "Friends": 30
        }

        context = {
            "ip": "12.31.42.111",
            "location": {
                "countryCode": "US",
                "region": "CA"
            },
            "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.53.11 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10",
            "langauge": "en-us"
        }

        segmentio.identify('random_session_id', 'ilya@segment.io', traits,
            context=context, timestamp=today())

        self.assertTrue(segmentio.stats.identifies == 2)

    def full_track(self):
        properties = {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        }

        segmentio.track('random_session_id', 'ilya@segment.io', 'Played a Song',
            properties, timestamp=today())

        self.assertTrue(segmentio.stats.track == 2)


if __name__ == '__main__':
    unittest.main()
