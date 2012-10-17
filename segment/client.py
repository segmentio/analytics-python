
import json
import threading
import datetime
import collections

import requests

from stats import Statistics
from errors import ApiError, BatchError
from utils import guess_timezone

import options



logging_enabled = True
import logging
logger = logging.getLogger('segment')


def log(level, *args):
    if logging_enabled:
        method = getattr(logger, level)
        method(*args)


def package_exception(client, data, e):
    log('warn', 'Segment.io request error', e)
    client._on_failed_flush(data, e)


def package_response(client, data, response):
    if response.status_code == 200:
        client._on_successful_flush(data, response)
    elif response.status_code == 400:
        content = response.text
        try:
            errors = []
            for error in json.loads(content):
                code = None
                message = None

                if 'code' in error:
                    code = error['code']

                if 'message' in error:
                    message = error['message']

                errors.append(ApiError(code, message))

            client._on_failed_flush(data, BatchError(errors))

        except Exception:
            client._on_failed_flush(data, ApiError('Bad Request', content))
    else:
        client._on_failed_flush(data, ApiError(response.status_code, response.text))


def request(client, url, data):

    log('debug', 'Sending request to Segment.io ...')
    try:
        response = requests.post(url, data=json.dumps(data),
            headers={'content-type': 'application/json'})

        log('debug', 'Finished Segment.io request.')

        package_response(client, data, response)

    except requests.ConnectionError as e:
        package_exception(client, data, e)


class FlushThread(threading.Thread):

    def __init__(self, client, url, batches):
        threading.Thread.__init__(self)
        self.client = client
        self.url = url
        self.batches = batches

    def run(self):
        log('debug', 'Flushing thread running ...')

        for data in self.batches:
            request(self.client, self.url, data)

        log('debug', 'Flushing thread done.')


class Client(object):
    """The Client class is a batching asynchronous python wrapper over the
    Segment.io API.

    """

    def __init__(self, api_key=None,
                       log_level=logging.INFO, log=True,
                       flush_at=10, flush_after=datetime.timedelta(0, 10),
                       async=True, max_queue_size=100000,
                       stats=Statistics()):
        """Create a new instance of a Segment.io Client

        :param str api_key: The Segment.io Live or Test API key
        :param logging.LOG_LEVEL log_level: The logging log level for the client
        talks to. Use log_level=logging.DEBUG to troubleshoot
        : param bool log: False to turn off logging completely, True by default
        : param int flush_at: Specicies after how many messages the client will flush
        to the server. Use flush_at=1 to disable batching
        : param datetime.timedelta flush_after: Specifies after how much time
        of no flushing that the server will flush. Used in conjunction with
        the flush_at size policy
        : param bool async: True to have the client flush to the server on another
        thread, therefore not blocking code (this is the default). False to
        enable blocking and making the request on the calling thread.

        """

        self.api_key = api_key

        self.queue = collections.deque()
        self.last_flushed = None

        if not log:
            logging_enabled = False
            # effectively disables the logger
            logger.setLevel(logging.CRITICAL)
        else:
            logger.setLevel(log_level)

        self.async = async

        self.max_queue_size = max_queue_size
        self.max_flush_size = 50

        self.flush_at = flush_at
        self.flush_after = flush_after

        self.stats = stats

        self.flush_lock = threading.Lock()
        self.flushing_thread = None

        self.success_callbacks = []
        self.failure_callbacks = []

    def set_log_level(self, level):
        """Sets the log level for Segment.io client

        :param logging.LOG_LEVEL level: The level at which Segment.io log should talk at

        """
        logger.setLevel(level)

    def _check_for_api_key(self):
        if not self.api_key:
            raise Exception('Please set segmentio.api_key before calling identify or track.')

    def _clean(self, d):
        to_delete = []
        for key in d.iterkeys():
            val = d[key]
            if not isinstance(val, (str, int, long, float, bool, datetime.datetime)):
                log('warn', 'Dictionary values must be strings, integers, longs, floats, booleans, or datetime. Dictioary key\'s "{0}" value {1} of type {2} is unsupported.'.format(key, val, type(val)))
                to_delete.append(key)
        for key in to_delete:
            del d[key]

    def on_success(self, callback):
        self.success_callbacks.append(callback)

    def on_failure(self, callback):
        self.failure_callbacks.append(callback)

    def identify(self, session_id=None, user_id=None, traits={},
        context={}, timestamp=None):

        """Identifying a user ties all of their actions to an ID
        you recognize and records user traits you can segment by.

        :param str session_id: Ta unique id associated with each user's session.
        Most web frameworks provide a session id you can use here, but if you
        don't have one (like if you're sending from a desktop app),
        you can use null.

        :param str user_id: is best as an email, but any unique ID will work.
        This is how you recognize a signed-in user in your system. Note:
        userId can be null if the user is not logged in, but then you must
        provide a sessionId. By explicitly identifying a user, you tie all of
        their actions to their identity. This makes it possible for you to
        run things like segment-based email campaigns.

        : param dict traits: a dictionary with keys like "Subscription Plan"
        or "Favorite Genre". You can segment your users by any trait you record.
        Once you record a trait, no need to send it again, so the traits
        argument is optional. Accepted value types are string, boolean, ints,
        doubles, longs, and datetime.datetime.

        : param dict context: An optional dictionary with additional information
        thats related to the visit. Examples are userAgent, and IP address
        of the visitor.

        : param datetime.datetime timestamp: If this event happened in the past,
        the timestamp   can be used to designate when the identification happened.
        Careful with this one,  if it just happened, leave it None. If you do
        choose to provide a timestamp, make sure it has a timezone.

        """

        self._check_for_api_key()

        if not session_id and not user_id:
            raise Exception('Must supply either a session_id or a user_id (or both).')

        if traits is not None and not isinstance(traits, dict):
            raise Exception('Traits must be a dictionary.')

        if context is not None and not isinstance(context, dict):
            raise Exception('Context must be a dictionary.')

        if timestamp is not None and not isinstance(timestamp, datetime.datetime):
            raise Exception('Timestamp must be a datetime.datetime object.')

        self._clean(traits)

        action = {'sessionId':   session_id,
                  'userId':      user_id,
                  'traits':      traits,
                  'context':     context,
                  'action':     'identify'}

        if timestamp is not None:
            action['timestamp'] = guess_timezone(timestamp).isoformat()

        if self._enqueue(action):
            self.stats.identifies += 1

    def track(self, session_id=None, user_id=None, event=None, properties={},
                timestamp=None):

        """Whenever a user triggers an event on your site, you'll want to track it
        so that you can analyze and segment by those events later.

        :param str session_id: Ta unique id associated with each user's session.
        Most web frameworks provide a session id you can use here, but if you
        don't have one (like if you're sending from a desktop app),
        you can use null.

        :param str user_id: is best as an email, but any unique ID will work.
        This is how you recognize a signed-in user in your system. Note:
        userId can be null if the user is not logged in, but then you must
        provide a sessionId. By explicitly identifying a user, you tie all of
        their actions to their identity. This makes it possible for you to
        run things like segment-based email campaigns.

        : param str event: The event name you are tracking. It is recommended
        that it is in human readable form. For example, "Bought T-Shirt"
        or "Started an exercise"

        : param dict properties: A dictionary with items that describe the event
        in more detail. This argument is optional, but highly recommended -
        you'll find these properties extremely useful later. Accepted value
        types are string, boolean, ints, doubles, longs, and datetime.datetime.

        : param datetime.datetime timestamp: If this event happened in the past,
        the timestamp   can be used to designate when the identification happened.
        Careful with this one,  if it just happened, leave it None. If you do
        choose to provide a timestamp, make sure it has a timezone.

        """

        self._check_for_api_key()

        if not session_id and not user_id:
            raise Exception('Must supply either a session_id or a user_id (or both).')

        if not event:
            raise Exception('Event is a required argument as a non-empty string.')

        if properties is not None and not isinstance(properties, dict):
            raise Exception('Context must be a dictionary.')

        if timestamp is not None and not isinstance(timestamp, datetime.datetime):
            raise Exception('Timestamp must be a datetime.datetime object.')

        self._clean(properties)

        action = {'sessionId':    session_id,
                  'userId':       user_id,
                  'event':        event,
                  'properties':   properties,
                  'timestamp':    timestamp,
                  'action':      'track'}

        if timestamp is not None:
            action['timestamp'] = guess_timezone(timestamp).isoformat()

        if self._enqueue(action):
            self.stats.tracks += 1

    def _should_flush(self):
        """ Determine whether we should sync """

        full = len(self.queue) >= self.flush_at
        stale = self.last_flushed is None

        if not stale:
            stale = datetime.datetime.now() - self.last_flushed > self.flush_after

        return full or stale

    def _enqueue(self, action):

        submitted = False

        if len(self.queue) < self.max_queue_size:
            self.queue.append(action)

            self.stats.submitted += 1

            submitted = True

        else:
            log('warn', 'Segment.io queue is full')

        if self._should_flush():
            self.flush()

        return submitted

    def _on_successful_flush(self, data, response):
        if 'batch' in data:
            for item in data['batch']:
                self.stats.successful += 1
                for callback in self.success_callbacks:
                    callback(data, response)

    def _on_failed_flush(self, data, error):
        if 'batch' in data:
            for item in data['batch']:
                self.stats.failed += 1
                for callback in self.failure_callbacks:
                    callback(data, error)

    def _flush_thread_is_free(self):
        return self.flushing_thread is None or not self.flushing_thread.is_alive()

    def flush(self):
        """ Forces a flush from the queue to the server """

        flushing = False

        url = options.host + options.endpoints['batch']

        if self.async:

            # Flushes on another thread

            with self.flush_lock:

                if self._flush_thread_is_free():

                    log('debug', 'Attempting asynchronous flush ...')

                    batches = self._get_batches()
                    if len(batches) > 0:

                        self.flushing_thread = FlushThread(self,
                            url, batches)

                        self.flushing_thread.start()

                        flushing = True

                else:
                    log('debug', 'The flushing thread is still active, cant flush right now')
        else:

            # Flushes on this thread
            log('debug', 'Starting synchronous flush ...')

            batches = self._get_batches()
            if len(batches) > 0:
                for data in batches:
                    request(self, url, data)
                flushing = True

            log('debug', 'Finished synchronous flush.')

        if flushing:
            self.last_flushed = datetime.datetime.now()
            self.stats.flushes += 1

        return flushing

    def _get_batches(self):

        batches = []

        while len(self.queue) > 0:
            batch = []
            for i in range(self.max_flush_size):
                if len(self.queue) == 0:
                    break
                batch.append(self.queue.pop())

            batches.append({
                'batch':          batch,
                'apiKey':         self.api_key
            })

        return batches
