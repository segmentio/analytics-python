
from analytics.version import VERSION
from analytics.client import Client

__version__ = VERSION

"""Settings."""
write_key = None
endpoint = 'https://api.segment.io/v1/batch'
max_queue_size = 10000
upload_size = 100
on_error = None
debug = False
send = True

default_client = None


def track(*args, **kwargs):
    """Send a track call."""
    _proxy('track', *args, **kwargs)

def identify(*args, **kwargs):
    """Send a identify call."""
    _proxy('identify', *args, **kwargs)

def group(*args, **kwargs):
    """Send a group call."""
    _proxy('group', *args, **kwargs)

def alias(*args, **kwargs):
    """Send a alias call."""
    _proxy('alias', *args, **kwargs)

def page(*args, **kwargs):
    """Send a page call."""
    _proxy('page', *args, **kwargs)

def screen(*args, **kwargs):
    """Send a screen call."""
    _proxy('screen', *args, **kwargs)

def flush():
    """Tell the client to flush."""
    _proxy('flush')

def join():
    """Block program until the client clears the queue"""
    _proxy('join')

def _proxy(method, *args, **kwargs):
    """Create an analytics client if one doesn't exist and send to it."""
    global default_client
    if not default_client:
        default_client = Client(write_key, debug=debug, on_error=on_error,
                                send=send, endpoint=endpoint,
                                max_queue_size=max_queue_size,
                                upload_size=upload_size)

    fn = getattr(default_client, method)
    fn(*args, **kwargs)
