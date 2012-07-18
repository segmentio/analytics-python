import datetime
import grequests
import gevent


class Client(object):

    def __init__(self, api_key=None, url='http://segment.io/v2/import',
                    logging=True, pool_size=2, sync_size=100, max_size=100000,
                    timeout=datetime.timedelta(0, 10),
                    environment='production'):

        self.queue = []
        self.last_synced = datetime.datetime.now()
        self.max_size = max_size
        self.sync_size = sync_size
        self.pool = gevent.pool.Pool(pool_size)
        self.logging = logging
        self.url = url
        self.timeout = timeout
        self.environment = environment

    def track(self, session=None, visitor=None, event=None, properties={},
                context={}):

        """ Track call """

        if not visitor and not session:
            raise Exception('Must supply one of session or visitor')

        action = {'visitor':    visitor,
                  'session':    session,
                  'event':      event,
                  'properties': properties,
                  'context':    context,
                  'action':     'track'}

        self.queue.push(action)

        self.sync()

    def identify(self, session=None, visitor=None, traits={}, context={}):

        """ Identify call """

        if not visitor and not session:
            raise Exception('Must supply one of session or visitor')

        action = {'visitor': visitor,
                  'session': session,
                  'traits':  traits,
                  'context': context,
                  'action':  'identify'}

        self.queue.push(action)

        self.sync()

    def sync(self, force=False):

        should_sync = force or self._should_sync()

        if should_sync:

            self._request()

            self.queue = []
            self.last_synced = datetime.datetime.now()

        return should_sync

    def _request(self):
        """ Make a POST to the server """

        data = {'batch':          self.queue,
                'project':        {'apiKey': self.api_key},
                'environment':    self.environment}

        request = grequests.post(self.url, data=data)

        grequests.send(request, self.pool)

    def _should_sync(self):
        """ Determine whether we should sync """

        full = len(self.queue) > self.sync_size
        stale = (datetime.datetime.now() - self.last_synced) > self.timeout

        return full or stale
