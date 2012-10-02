
import unittest

from datetime import date

from time import sleep

import segmentio


def on_success(data, response):
    print 'Success', response


def on_failure(data, error):
    print 'Failure', error


class SegmentioBasicTests(unittest.TestCase):

    def setUp(self):
        segmentio.options.host = 'http://192.168.1.139:81'
        segmentio.init('fakeid')

        segmentio.on_success(on_success)
        segmentio.on_failure(on_failure)

    def test_basic_identify(self):

        lastIdentifies = segmentio.stats.identifies
        lastSuccessful = segmentio.stats.successful

        segmentio.identify('random_session_id', 'ilya@segment.io', {
            "Subscription Plan": "Free",
            "Friends": 30
        })

        self.assertTrue(segmentio.stats.identifies == lastIdentifies + 1)

        segmentio.flush()

        sleep(2)

        print segmentio.stats.successful
        print lastSuccessful + 1

        self.assertTrue(segmentio.stats.successful == lastSuccessful + 1)

    def test_basic_track(self):

        lastTracks = segmentio.stats.tracks
        lastSuccessful = segmentio.stats.successful

        segmentio.track('random_session_id', 'ilya@segment.io', 'Played a Song', {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        })

        self.assertTrue(segmentio.stats.tracks == lastTracks + 1)

        segmentio.flush()

        sleep(1)

        print segmentio.stats.successful
        print lastSuccessful + 1

        self.assertTrue(segmentio.stats.successful == lastSuccessful + 1)

    def test_full_identify(self):

        lastIdentifies = segmentio.stats.identifies
        lastSuccessful = segmentio.stats.successful

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
            context=context, timestamp=date.today())

        self.assertTrue(segmentio.stats.identifies == lastIdentifies + 1)

        segmentio.flush()

        sleep(1)

        print segmentio.stats.successful
        print lastSuccessful + 1

        self.assertTrue(segmentio.stats.successful == lastSuccessful + 1)

    def test_full_track(self):

        lastTracks = segmentio.stats.tracks
        lastSuccessful = segmentio.stats.successful

        properties = {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        }

        segmentio.track('random_session_id', 'ilya@segment.io', 'Played a Song',
            properties, timestamp=date.today())

        self.assertTrue(segmentio.stats.tracks == lastTracks + 1)

        segmentio.flush()

        sleep(1)

        print segmentio.stats.successful
        print lastSuccessful + 1

        self.assertTrue(segmentio.stats.successful == lastSuccessful + 1)


if __name__ == '__main__':
    unittest.main()
