
from stats import Statistics
stats = Statistics()

from client import Client


def init(api_key, **kwargs):
    default_client = Client(api_key=api_key, stats=stats)
    import sys
    this_module = sys.modules[__name__]

    def proxy(method):
        def proxy_to_default_client(*args, **kwargs):
            func = getattr(default_client, method)
            return func(*args, **kwargs)

        setattr(this_module, method, proxy_to_default_client)

    methods = ['identify', 'track', 'flush', 'on_success', 'on_failure']
    for method in methods:
        proxy(method)
