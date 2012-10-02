
import json
import threading
import datetime
import collections

import gevent
from gevent import monkey
monkey.patch_thread()
import gevent.pool

import requests

from stats import Statistics
from errors import ApiError, BatchError

import options


def package_exception(client, data, e):
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
    print 'Request started'
    try:
        response = requests.post(url, data=json.dumps(data),
            headers={'content-type': 'application/json'})
        package_response(client, data, response)
    except requests.ConnectionError as e:
        package_exception(client, data, e)


class FlushThread(threading.Thread):

    def __init__(self, client, url, batches, pool_size=2):
        threading.Thread.__init__(self)
        self.client = client
        self.url = url
        self.batches = batches
        self.pool = gevent.pool.Pool(pool_size)

    def run(self):
        print 'Flushing thread started'
        for data in self.batches:
            self.pool.spawn(request, self.client, self.url, data)

        self.pool.join()


class Client(object):

    def __init__(self, api_key=None, logging=True, pool_size=2, flush_size=10,
                    max_size=100000, flush_size_trigger=50,
                    flush_time_trigger=datetime.timedelta(0, 10),
                    stats=Statistics()):

        self.api_key = api_key

        self.queue = collections.deque()
        self.last_flushed = None

        self.pool_size = pool_size
        self.logging = logging

        self.max_size = max_size
        self.flush_size = flush_size

        self.flush_size_trigger = flush_size_trigger
        self.flush_time_trigger = flush_time_trigger

        self.stats = stats

        self.flush_lock = threading.Lock()
        self.flushing_thread = None

        self.success_callbacks = []
        self.failure_callbacks = []

    def _check_for_api_key(self):
        if not self.api_key:
            raise Exception('Please set segmentio.api_key before calling identify or track.')

    def _clean(self, dict):
        pass

    def on_success(self, callback):
        self.success_callbacks.append(callback)

    def on_failure(self, callback):
        self.failure_callbacks.append(callback)

    def identify(self, session_id=None, user_id=None, traits={},
        context={}, timestamp=None):

        """ Identify call """

        self._check_for_api_key()

        if not session_id and not user_id:
            raise Exception('Must supply either a session_id or a user_id (or both).')

        if traits is not None and not isinstance(traits, dict):
            raise Exception('Traits must be a dictionary.')

        if context is not None and not isinstance(context, dict):
            raise Exception('Context must be a dictionary.')

        if timestamp is not None and not isinstance(timestamp, datetime.date):
            raise Exception('Timestamp must be a datetime.date object.')

        self._clean(traits)

        action = {'sessionId':   session_id,
                  'userId':      user_id,
                  'traits':      traits,
                  'context':     context,
                  'action':     'identify'}

        if timestamp is not None:
            action['timestamp'] = timestamp.isoformat()

        if self._enqueue(action):
            self.stats.identifies += 1

    def track(self, session_id=None, user_id=None, event=None, properties={},
                context={}, timestamp=None):

        """ Track call """

        self._check_for_api_key()

        if not session_id and not user_id:
            raise Exception('Must supply either a session_id or a user_id (or both).')

        if not event:
            raise Exception('Event is a required argument as a non-empty string.')

        if properties is not None and not isinstance(properties, dict):
            raise Exception('Context must be a dictionary.')

        if timestamp is not None and not isinstance(timestamp, datetime.date):
            raise Exception('Timestamp must be a datetime.date object.')

        self._clean(properties)

        action = {'sessionId':    session_id,
                  'userId':       user_id,
                  'event':        event,
                  'properties':   properties,
                  'timestamp':    timestamp,
                  'action':      'track'}

        if timestamp is not None:
            action['timestamp'] = timestamp.isoformat()

        if self._enqueue(action):
            self.stats.tracks += 1

    def _should_flush(self):
        """ Determine whether we should sync """

        full = len(self.queue) >= self.flush_size_trigger
        stale = self.last_flushed is None

        if not stale:
            stale = datetime.datetime.now() - self.last_flushed > self.flush_time_trigger

        return full or stale

    def _enqueue(self, action):

        submitted = False

        if len(self.queue) < self.max_size:
            self.queue.append(action)

            self.stats.submitted += 1

            submitted = True

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
        return self.flushing_thread is None or self.flushing_thread.is_alive()

    def flush(self):
        """ Flushes a batch to the server """

        flushing = False

        with self.flush_lock:

            if self._flush_thread_is_free():

                batches = []

                while len(self.queue) > 0:
                    batch = []
                    for i in range(self.flush_size):
                        if len(self.queue) == 0:
                            break
                        batch.append(self.queue.pop())

                    batches.append({
                        'batch':          batch,
                        'apiKey':         self.api_key
                    })

                if len(batches) > 0:

                    url = options.host + options.endpoints['batch']

                    self.flushing_thread = FlushThread(self,
                        url, batches, self.pool_size)

                    self.flushing_thread.start()

                    self.last_synced = datetime.datetime.now()

                    self.stats.flushes += 1

                    flushing = True

        return flushing
