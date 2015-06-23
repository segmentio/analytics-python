from datetime import datetime
from uuid import uuid4
import logging
import numbers

from dateutil.tz import tzutc
from six import string_types

from analytics.utils import guess_timezone, clean
from analytics.consumer import Consumer
from analytics.version import VERSION

try:
    import queue
except:
    import Queue as queue


ID_TYPES = (numbers.Number, string_types)


class Client(object):
    """Create a new Segment client."""
    log = logging.getLogger('segment')

    def __init__(self, write_key=None, debug=False, max_queue_size=10000,
                 send=True, on_error=None):
        require('write_key', write_key, string_types)

        self.queue = queue.Queue(max_queue_size)
        self.consumer = Consumer(self.queue, write_key, on_error=on_error)
        self.write_key = write_key
        self.on_error = on_error
        self.debug = debug
        self.send = send

        if debug:
            self.log.setLevel(logging.DEBUG)

        # if we've disabled sending, just don't start the consumer
        if send:
            self.consumer.start()

    def identify(self, user_id=None, traits={}, context={}, timestamp=None,
                 anonymous_id=None, integrations={}):
        require('user_id or anonymous_id', user_id or anonymous_id, ID_TYPES)
        require('traits', traits, dict)

        msg = {
            'integrations': integrations,
            'anonymousId': anonymous_id,
            'timestamp': timestamp,
            'context': context,
            'type': 'identify',
            'userId': user_id,
            'traits': traits
        }

        return self._enqueue(msg)

    def track(self, user_id=None, event=None, properties={}, context={},
              timestamp=None, anonymous_id=None, integrations={}):

        require('user_id or anonymous_id', user_id or anonymous_id, ID_TYPES)
        require('properties', properties, dict)
        require('event', event, string_types)

        msg = {
            'integrations': integrations,
            'anonymousId': anonymous_id,
            'properties': properties,
            'timestamp': timestamp,
            'context': context,
            'userId': user_id,
            'type': 'track',
            'event': event
        }

        return self._enqueue(msg)

    def alias(self, previous_id=None, user_id=None, context={}, timestamp=None,
              integrations={}):
        require('previous_id', previous_id, ID_TYPES)
        require('user_id', user_id, ID_TYPES)

        msg = {
            'integrations': integrations,
            'previousId': previous_id,
            'timestamp': timestamp,
            'context': context,
            'userId': user_id,
            'type': 'alias'
        }

        return self._enqueue(msg)

    def group(self, user_id=None, group_id=None, traits={}, context={},
              timestamp=None, anonymous_id=None, integrations={}):
        require('user_id or anonymous_id', user_id or anonymous_id, ID_TYPES)
        require('group_id', group_id, ID_TYPES)
        require('traits', traits, dict)

        msg = {
            'integrations': integrations,
            'anonymousId': anonymous_id,
            'timestamp': timestamp,
            'groupId': group_id,
            'context': context,
            'userId': user_id,
            'traits': traits,
            'type': 'group'
        }

        return self._enqueue(msg)

    def page(self, user_id=None, category=None, name=None, properties={},
             context={}, timestamp=None, anonymous_id=None, integrations={}):
        require('user_id or anonymous_id', user_id or anonymous_id, ID_TYPES)
        require('properties', properties, dict)

        if name:
            require('name', name, string_types)
        if category:
            require('category', category, string_types)

        msg = {
            'integrations': integrations,
            'anonymousId': anonymous_id,
            'properties': properties,
            'timestamp': timestamp,
            'category': category,
            'context': context,
            'userId': user_id,
            'type': 'page',
            'name': name,
        }

        return self._enqueue(msg)

    def screen(self, user_id=None, category=None, name=None, properties={},
               context={}, timestamp=None, anonymous_id=None, integrations={}):
        require('user_id or anonymous_id', user_id or anonymous_id, ID_TYPES)
        require('properties', properties, dict)

        if name:
            require('name', name, string_types)
        if category:
            require('category', category, string_types)

        msg = {
            'integrations': integrations,
            'anonymousId': anonymous_id,
            'properties': properties,
            'timestamp': timestamp,
            'category': category,
            'context': context,
            'userId': user_id,
            'type': 'screen',
            'name': name,
        }

        return self._enqueue(msg)

    def _enqueue(self, msg):
        """Push a new `msg` onto the queue, return `(success, msg)`"""
        timestamp = msg['timestamp']
        if timestamp is None:
            timestamp = datetime.utcnow().replace(tzinfo=tzutc())

        require('integrations', msg['integrations'], dict)
        require('type', msg['type'], string_types)
        require('timestamp', timestamp, datetime)
        require('context', msg['context'], dict)

        # add common
        timestamp = guess_timezone(timestamp)
        msg['timestamp'] = timestamp.isoformat()
        msg['messageId'] = str(uuid4())
        msg['context']['library'] = {
            'name': 'analytics-python',
            'version': VERSION
        }

        msg = clean(msg)
        self.log.debug('queueing: %s', msg)

        if self.queue.full():
            self.log.warn('analytics-python queue is full')
            return False, msg

        self.queue.put(msg)
        self.log.debug('enqueued ' + msg['type'] + '.')
        return True, msg

    def flush(self):
        """Forces a flush from the internal queue to the server"""
        queue = self.queue
        size = queue.qsize()
        queue.join()
        self.log.debug('successfully flushed {0} items.'.format(size))

    def join(self):
        """Ends the consumer thread once the queue is empty. Blocks execution until finished"""
        self.consumer.pause()
        self.consumer.join()



def require(name, field, data_type):
    """Require that the named `field` has the right `data_type`"""
    if not isinstance(field, data_type):
        msg = '{0} must have {1}, got: {2}'.format(name, data_type, field)
        raise AssertionError(msg)
