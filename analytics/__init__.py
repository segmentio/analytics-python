
from analytics.version import VERSION
from analytics.client import Client

__version__ = VERSION

"""Settings."""
write_key = None
host = None
on_error = None
debug = False
send = True
sync_mode = False
upload_size = 100
upload_interval = 0.5
max_queue_size = 10000
gzip = False
timeout = 15
max_retries = 10


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


def shutdown():
    """Flush all messages and cleanly shutdown the client"""
    _proxy('flush')
    _proxy('join')


def _proxy(method, *args, **kwargs):
    """Create an analytics client if one doesn't exist and send to it."""
    global default_client
    if not default_client:
        default_client = Client(write_key, host=host, debug=debug, max_queue_size=max_queue_size,
                                send=send, on_error=on_error, upload_size=upload_size, upload_interval=upload_interval,
                                gzip=gzip, max_retries=max_retries, sync_mode=sync_mode, timeout=timeout)

    fn = getattr(default_client, method)
    fn(*args, **kwargs)
