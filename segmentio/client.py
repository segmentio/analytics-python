import datetime
import grequests
import gevent


class Client(object):

    def __init__(self, logging=True, pool_size=2, sync_size=100,
                    max_size=100000, timeout=datetime.timedelta(0, 10)):

        self.queue = []
        self.last_synced = datetime.datetime.now()
        self.max_size = max_size
        self.sync_size = sync_size
        self.pool = gevent.pool.Pool(pool_size)
        self.logging = logging
        self.timeout = timeout

    def identify(self, sessionId=None, userId=None, traits={},
        context={}, timestamp=None):

        """ Identify call """

        if not userId and not sessionId:
            raise Exception('Must supply either a sessionId or a userId (or both).')

        action = {'sessionId':   sessionId,
                  'userId':   userId,
                  'traits':    traits,
                  'context':   context,
                  'timestamp': timestamp,
                  'action':    'identify'}

        self.queue.push(action)

        self.sync()

    def track(self, sessionId=None, userId=None, event=None, properties={},
                context={}, timestamp=None):

        """ Track call """

        if not userId and not sessionId:
            raise Exception('Must supply either a sessionId or a userId (or both).')

        action = {'sessionId':    sessionId,
                  'userId':       userId,
                  'event':        event,
                  'properties':   properties,
                  'timestamp':    timestamp,
                  'action':      'track'}

        self.queue.push(action)

        self.sync()

    def _should_sync(self):
        """ Determine whether we should sync """

        full = len(self.queue) > self.sync_size
        stale = (datetime.datetime.now() - self.last_synced) > self.timeout

        return full or stale

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
