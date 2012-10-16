
import sys

try:
    import requests
except ImportError:
    print >>sys.stderr, 'The Segment.io library requires that you have a Python "requests" library installed. Try running "pip install requests"'

from stats import Statistics
stats = Statistics()

from client import Client


def initialize(api_key, **kwargs):
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
