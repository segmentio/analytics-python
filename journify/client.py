"""Journify client."""
from datetime import datetime
from uuid import uuid4
import logging
import numbers
import atexit
import json
import hashlib
import queue

from dateutil.tz import tzutc
from journify.utils import guess_timezone, clean
from journify.consumer import Consumer, MAX_MSG_SIZE
from journify.request import post, DatetimeSerializer
from journify.version import VERSION

ID_TYPES = (numbers.Number, str)


class Client:
    """Class representing a Journify client"""
    class DefaultConfig:
        """Class representing default config for a Journify client"""
        write_key = None
        host = None
        on_error = None
        debug = False
        send = True
        sync_mode = False
        max_queue_size = 10000
        gzip = False
        timeout = 15
        max_retries = 10
        proxies = None
        thread = 1
        upload_interval = 0.5
        upload_size = 100

    # Create a new Journify client.
    log = logging.getLogger('journify')

    def __init__(self,
                 write_key=DefaultConfig.write_key,
                 host=DefaultConfig.host,
                 debug=DefaultConfig.debug,
                 max_queue_size=DefaultConfig.max_queue_size,
                 send=DefaultConfig.send,
                 on_error=DefaultConfig.on_error,
                 gzip=DefaultConfig.gzip,
                 max_retries=DefaultConfig.max_retries,
                 sync_mode=DefaultConfig.sync_mode,
                 timeout=DefaultConfig.timeout,
                 proxies=DefaultConfig.proxies,
                 thread=DefaultConfig.thread,
                 upload_size=DefaultConfig.upload_size,
                 upload_interval=DefaultConfig.upload_interval,):
        require('write_key', write_key, str)

        self.queue = queue.Queue(max_queue_size)
        self.write_key = write_key
        self.on_error = on_error
        self.debug = debug
        self.send = send
        self.sync_mode = sync_mode
        self.host = host
        self.gzip = gzip
        self.timeout = timeout
        self.proxies = proxies

        if self.debug:
            self.log.setLevel(logging.DEBUG)

        if sync_mode:
            self.consumers = None
        else:
            # On program exit, allow the consumer thread to exit cleanly.
            # This prevents exceptions and a messy shutdown when the
            # interpreter is destroyed before the daemon thread finishes
            # execution. However, it is *not* the same as flushing the queue!
            # To guarantee all messages have been delivered, you'll still need
            # to call flush().
            if send:
                atexit.register(self.join)
            for _ in range(thread):
                self.consumers = []
                consumer = Consumer(
                    self.queue, write_key, host=host, on_error=on_error,
                    upload_size=upload_size, upload_interval=upload_interval,
                    gzip=gzip, retries=max_retries, timeout=timeout,
                    proxies=proxies,
                )
                self.consumers.append(consumer)

                # if we've disabled sending, just don't start the consumer
                if send:
                    consumer.start()

    def identify(self, user_id=None, traits=None, context=None, timestamp=None,
                 anonymous_id=None, message_id=None):
        traits = traits or {}
        context = context or {}
        require('user_id or anonymous_id', user_id or anonymous_id, ID_TYPES)
        require('traits', traits, dict)

        msg = {
            'anonymousId': anonymous_id,
            'timestamp': timestamp,
            'context': context,
            'type': 'identify',
            'userId': user_id,
            'traits': traits,
            'messageId': message_id,
        }

        return self._enqueue(msg)

    def track(self, user_id=None, event=None, properties=None, context=None,
              timestamp=None, anonymous_id=None, message_id=None):
        properties = properties or {}
        context = context or {}
        require('user_id or anonymous_id', user_id or anonymous_id, ID_TYPES)
        require('properties', properties, dict)
        require('event', event, str)

        msg = {
            'anonymousId': anonymous_id,
            'properties': properties,
            'timestamp': timestamp,
            'context': context,
            'userId': user_id,
            'type': 'track',
            'event': event,
            'messageId': message_id,
        }

        return self._enqueue(msg)

    def group(self, user_id=None, group_id=None, traits=None, context=None,
              timestamp=None, anonymous_id=None, message_id=None):
        traits = traits or {}
        context = context or {}
        require('user_id or anonymous_id', user_id or anonymous_id, ID_TYPES)
        require('group_id', group_id, ID_TYPES)
        require('traits', traits, dict)

        msg = {
            'anonymousId': anonymous_id,
            'timestamp': timestamp,
            'groupId': group_id,
            'context': context,
            'userId': user_id,
            'traits': traits,
            'type': 'group',
            'messageId': message_id,
        }

        return self._enqueue(msg)

    def page(self, user_id=None, category=None, name=None, properties=None,
             context=None, timestamp=None, anonymous_id=None, message_id=None):
        properties = properties or {}
        context = context or {}
        require('user_id or anonymous_id', user_id or anonymous_id, ID_TYPES)
        require('properties', properties, dict)

        if name:
            require('name', name, str)
        if category:
            require('category', category, str)

        msg = {
            'anonymousId': anonymous_id,
            'properties': properties,
            'timestamp': timestamp,
            'category': category,
            'context': context,
            'userId': user_id,
            'type': 'page',
            'name': name,
            'messageId': message_id,
        }

        return self._enqueue(msg)

    def _enqueue(self, msg):
        """Push a new `msg` onto the queue, return `(success, msg)`"""
        timestamp = msg['timestamp']
        if timestamp is None:
            timestamp = datetime.utcnow().replace(tzinfo=tzutc())
        message_id = msg.get('messageId')
        if message_id is None:
            body_hash = hashlib.md5(json.dumps(msg).encode('utf-8')).hexdigest()
            message_id = f"python-{body_hash}-{uuid4()}"

        require('type', msg['type'], str)
        require('timestamp', timestamp, datetime)
        require('context', msg['context'], dict)

        # add common
        timestamp = guess_timezone(timestamp)
        msg['timestamp'] = timestamp.isoformat(timespec='milliseconds')
        msg['messageId'] = stringify_id(message_id)
        msg['writeKey'] = self.write_key
        msg['context']['library'] = {
            'name': 'journify-python-sdk',
            'version': VERSION
        }

        msg['userId'] = stringify_id(msg.get('userId', None))
        msg['anonymousId'] = stringify_id(msg.get('anonymousId', None))

        msg = clean(msg)
        self.log.debug('queueing: %s', msg)

        # Check message size.
        msg_size = len(json.dumps(msg, cls=DatetimeSerializer).encode())
        if msg_size > MAX_MSG_SIZE:
            msg = f'Message exceeds {MAX_MSG_SIZE}kb limit. ({msg})'
            raise RuntimeError(msg)

        # if send is False, return msg as if it was successfully queued
        if not self.send:
            return True, msg

        if self.sync_mode:
            self.log.debug('enqueued with blocking %s.', msg['type'])
            post(self.write_key, self.host, gzip=self.gzip,
                 timeout=self.timeout, proxies=self.proxies, batch=[msg])

            return True, msg

        try:
            self.queue.put(msg, block=False)
            self.log.debug('enqueued %s.', msg['type'])
            return True, msg
        except queue.Full:
            self.log.warning('journify-python-sdk queue is full')
            return False, msg

    def flush(self):
        """Forces a flush from the internal queue to the server"""
        local_queue = self.queue
        size = local_queue.qsize()
        self.log.error('trying to flush %s items', size)
        local_queue.join()
        # Note that this message may not be precise, because of threading.
        self.log.error('successfully flushed about %s items.', size)

    def join(self):
        """Ends the consumer thread once the queue is empty.
        Blocks execution until finished
        """
        for consumer in self.consumers:
            consumer.pause()
            try:
                consumer.join()
            except RuntimeError:
                # consumer thread has not started
                pass

    def shutdown(self):
        """Flush all messages and cleanly shutdown the client"""
        self.flush()
        self.join()


def require(name, field, data_type):
    """Require that the named `field` has the right `data_type`"""
    if not isinstance(field, data_type):
        msg = f'{name} must be a {data_type}, got: {field}'
        raise AssertionError(msg)


def stringify_id(val):
    if val is None:
        return None
    if isinstance(val, str):
        return val
    return str(val)
