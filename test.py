
import unittest

from datetime import datetime, timedelta

from time import sleep, time

import logging
logging.basicConfig()

from dateutil.tz import tzutc

import segment
import segment.utils


def on_success(data, response):
    print 'Success', response


def on_failure(data, error):
    print 'Failure', error


class SegmentioBasicTests(unittest.TestCase):

    def setUp(self):
        segment.initialize('fakeid', log_level=logging.DEBUG)

        segment.on_success(on_success)
        segment.on_failure(on_failure)

    def test_timezone_utils(self):

        now = datetime.now()
        utcnow = datetime.now(tz=tzutc())

        self.assertTrue(segment.utils.is_naive(now))
        self.assertFalse(segment.utils.is_naive(utcnow))

        fixed = segment.utils.guess_timezone(now)

        self.assertFalse(segment.utils.is_naive(fixed))

        shouldnt_be_edited = segment.utils.guess_timezone(utcnow)

        self.assertTrue(utcnow == shouldnt_be_edited)

    def test_clean(self):
        supported = {
            'integer': 1,
            'float': 2.0,
            'long': 200000000,
            'bool': True,
            'str': 'woo',
            'date': datetime.now(),
        }

        unsupported = {
            'exception': Exception(),
            'timedelta': timedelta(microseconds=20),
            'list': [1, 2, 3]
        }

        combined = dict(supported.items() + unsupported.items())

        segment.default_client._clean(combined)

        self.assertTrue(combined == supported)

    def test_async_basic_identify(self):
        # flush after every message
        segment.default_client.flush_at = 1
        segment.default_client.async = True

        last_identifies = segment.stats.identifies
        last_successful = segment.stats.successful
        last_flushes = segment.stats.flushes

        segment.identify('random_session_id', 'ilya@segment.io', {
            "Subscription Plan": "Free",
            "Friends": 30
        })

        self.assertTrue(segment.stats.identifies == last_identifies + 1)

        # this should flush because we set the flush_at to 1
        self.assertTrue(segment.stats.flushes == last_flushes + 1)

        # this should do nothing, as the async thread is currently active
        segment.flush()

        # we should see no more flushes here
        self.assertTrue(segment.stats.flushes == last_flushes + 1)

        sleep(1)

        self.assertTrue(segment.stats.successful == last_successful + 1)

    def test_async_basic_track(self):

        segment.default_client.flush_at = 50
        segment.default_client.async = True

        last_tracks = segment.stats.tracks
        last_successful = segment.stats.successful

        segment.track('random_session_id', 'ilya@segment.io', 'Played a Song', {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        })

        self.assertTrue(segment.stats.tracks == last_tracks + 1)

        segment.flush()

        sleep(1)

        self.assertTrue(segment.stats.successful == last_successful + 1)

    def test_async_full_identify(self):

        segment.default_client.flush_at = 1
        segment.default_client.async = True

        last_identifies = segment.stats.identifies
        last_successful = segment.stats.successful

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
            "language": "en-us"
        }

        segment.identify('random_session_id', 'ilya@segment.io', traits,
            context=context, timestamp=datetime.now())

        self.assertTrue(segment.stats.identifies == last_identifies + 1)

        sleep(1)

        self.assertTrue(segment.stats.successful == last_successful + 1)

    def test_async_full_track(self):

        segment.default_client.flush_at = 1
        segment.default_client.async = True

        last_tracks = segment.stats.tracks
        last_successful = segment.stats.successful

        properties = {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        }

        segment.track('random_session_id', 'ilya@segment.io', 'Played a Song',
            properties, timestamp=datetime.now())

        self.assertTrue(segment.stats.tracks == last_tracks + 1)

        sleep(1)

        self.assertTrue(segment.stats.successful == last_successful + 1)

    def test_blocking_flush(self):

        segment.default_client.flush_at = 1
        segment.default_client.async = False

        last_tracks = segment.stats.tracks
        last_successful = segment.stats.successful

        properties = {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        }

        segment.track('random_session_id', 'ilya@segment.io', 'Played a Song',
            properties, timestamp=datetime.today())

        self.assertTrue(segment.stats.tracks == last_tracks + 1)
        self.assertTrue(segment.stats.successful == last_successful + 1)

    def test_time_policy(self):

        segment.default_client.async = False
        segment.default_client.flush_at = 1

        # add something so we have a reason to flush
        segment.track('random_session_id', 'ilya@segment.io', 'Played a Song', {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        })

        # flush to reset flush count
        segment.flush()

        last_flushes = segment.stats.flushes

        # set the flush size trigger high
        segment.default_client.flush_at = 50
        # set the time policy to 1 second from now
        segment.default_client.flush_after = timedelta(seconds=1)

        segment.track('random_session_id', 'ilya@segment.io', 'Played a Song', {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        })

        # that shouldn't of triggered a flush
        self.assertTrue(segment.stats.flushes == last_flushes)

        # sleep past the time-flush policy
        sleep(1.2)

        # submit another track to trigger the policy
        segment.track('random_session_id', 'ilya@segment.io', 'Played a Song', {
            "Artist": "The Beatles",
            "Song": "Eleanor Rigby"
        })

        self.assertTrue(segment.stats.flushes == last_flushes + 1)

    def test_performance(self):

        to_send = 100

        target = segment.stats.successful + to_send

        segment.default_client.async = True
        segment.default_client.flush_at = 200
        segment.default_client.max_flush_size = 50
        segment.default_client.set_log_level(logging.WARN)

        for i in range(to_send):
            segment.track('random_session_id', 'ilya@segment.io', 'Played a Song', {
                "Artist": "The Beatles",
                "Song": "Eleanor Rigby"
            })

        print 'Finished submitting into the queue'

        start = time()
        while segment.stats.successful < target:
            print 'Successful ', segment.stats.successful, 'Left', (target - segment.stats.successful), 'Duration ', (time() - start)
            segment.flush()
            sleep(1.0)

if __name__ == '__main__':
    unittest.main()
