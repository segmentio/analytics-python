
import version

VERSION = version.VERSION
__version__ = VERSION

import sys
this_module = sys.modules[__name__]

from stats import Statistics
stats = Statistics()


def init(secret, **kwargs):
    """Create a default instance of a analytics-python client

    :param str secret: The Segment.io API Secret

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
    from client import Client

    # if we have already initialized, no-op
    if hasattr(this_module, 'default_client'):
        return

    default_client = Client(secret=secret, stats=stats, **kwargs)

    setattr(this_module, 'default_client', default_client)


def _get_default_client():
    default_client = None
    if hasattr(this_module, 'default_client'):
        default_client = getattr(this_module, 'default_client')
    else:
        sys.stderr.write('Please call analytics.init(secret) ' +
                         'before calling analytics methods.\n')
    return default_client


def identify(user_id=None, traits={}, context={}, timestamp=None):
    """Identifying a user ties all of their actions to an id, and
    associates user traits to that id.

    :param str user_id: the user's id after they are logged in. It's the
    same id as which you would recognize a signed-in user in your system.

    : param dict traits: a dictionary with keys like subscriptionPlan or
    age. You only need to record a trait once, no need to send it again.
    Accepted value types are string, boolean, ints,, longs, and
    datetime.datetime.

    : param dict context: An optional dictionary with additional
    information thats related to the visit. Examples are userAgent, and IP
    address of the visitor.

    : param datetime.datetime timestamp: If this event happened in the
    past, the timestamp  can be used to designate when the identification
    happened.  Careful with this one,  if it just happened, leave it None.
    If you do choose to provide a timestamp, make sure it has a timezone.
    """
    default_client = _get_default_client()
    if default_client:
        default_client.identify(user_id=user_id, traits=traits,
                                context=context, timestamp=timestamp)


def track(user_id=None, event=None, properties={}, context={},
          timestamp=None):
    """Whenever a user triggers an event, you'll want to track it.

    :param str user_id:  the user's id after they are logged in. It's the
    same id as which you would recognize a signed-in user in your system.

    :param str event: The event name you are tracking. It is recommended
    that it is in human readable form. For example, "Bought T-Shirt"
    or "Started an exercise"

    :param dict properties: A dictionary with items that describe the
    event in more detail. This argument is optional, but highly recommended
    - you'll find these properties extremely useful later. Accepted value
    types are string, boolean, ints, doubles, longs, and datetime.datetime.

    :param dict context: An optional dictionary with additional information
    thats related to the visit. Examples are userAgent, and IP address
    of the visitor.

    :param datetime.datetime timestamp: If this event happened in the past,
    the timestamp   can be used to designate when the identification
    happened.  Careful with this one,  if it just happened, leave it None.
    If you do choose to provide a timestamp, make sure it has a timezone.

    """
    default_client = _get_default_client()
    if default_client:
        default_client.track(user_id=user_id, event=event,
                             properties=properties, context=context,
                             timestamp=timestamp)


def alias(from_id, to_id, context={}, timestamp=None):
    """Aliases an anonymous user into an identified user

    :param str from_id: the anonymous user's id before they are logged in

    :param str to_id: the identified user's id after they're logged in

    :param dict context: An optional dictionary with additional information
    thats related to the visit. Examples are userAgent, and IP address
    of the visitor.

    :param datetime.datetime timestamp: If this event happened in the past,
    the timestamp   can be used to designate when the identification
    happened.  Careful with this one,  if it just happened, leave it None.
    If you do choose to provide a timestamp, make sure it has a timezone.
    """
    default_client = _get_default_client()
    if default_client:
        default_client.alias(from_id=from_id, to_id=to_id, context=context,
                             timestamp=timestamp)


def flush(async=None):
    """ Forces a flush from the internal queue to the server

    :param bool async: True to block until all messages have been flushed
    """
    default_client = _get_default_client()
    if default_client:
        default_client.flush(async=async)


def on_success(callback):
    """
    Assign a callback to fire after a successful flush

    :param func callback: A callback that will be fired on a flush success
    """
    default_client = _get_default_client()
    if default_client:
        default_client.on_success(callback)


def on_failure(callback):
    """
    Assign a callback to fire after a failed flush

    :param func callback: A callback that will be fired on a failed flush
    """
    default_client = _get_default_client()
    if default_client:
        default_client.on_failure(callback)
