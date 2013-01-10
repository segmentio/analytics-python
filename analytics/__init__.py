
import sys

try:
    import requests
except ImportError:
    print >>sys.stderr, 'The Segment.io library requires that you have a Python "requests" library installed. Try running "pip install requests"'

from stats import Statistics
stats = Statistics()

from client import Client


def init(api_key, **kwargs):
    """Create a default instance of a analytics-python client

    :param str api_key: The Segment.io API Key

    Kwargs:

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

    default_client = Client(api_key=api_key, stats=stats, **kwargs)
    import sys
    this_module = sys.modules[__name__]

    setattr(this_module, 'default_client', default_client)

    def proxy(method):
        def proxy_to_default_client(*args, **kwargs):
            func = getattr(default_client, method)
            return func(*args, **kwargs)

        setattr(this_module, method, proxy_to_default_client)

    methods = ['identify', 'track', 'flush', 'on_success', 'on_failure']
    for method in methods:
        proxy(method)
