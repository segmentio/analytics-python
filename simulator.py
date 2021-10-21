import logging
import argparse
import json
import segment.analytics as analytics

__name__ = 'simulator.py'
__version__ = '0.0.1'
__description__ = 'scripting simulator'


def json_hash(str):
    if str:
        return json.loads(str)

# analytics -method=<method> -segment-write-key=<segmentWriteKey> [options]


parser = argparse.ArgumentParser(description='send a segment message')

parser.add_argument('--writeKey', help='the Segment writeKey')
parser.add_argument('--type', help='The Segment message type')

parser.add_argument('--userId', help='the user id to send the event as')
parser.add_argument(
    '--anonymousId', help='the anonymous user id to send the event as')
parser.add_argument(
    '--context', help='additional context for the event (JSON-encoded)')

parser.add_argument('--event', help='the event name to send with the event')
parser.add_argument(
    '--properties', help='the event properties to send (JSON-encoded)')

parser.add_argument(
    '--name', help='name of the screen or page to send with the message')

parser.add_argument(
    '--traits', help='the identify/group traits to send (JSON-encoded)')

parser.add_argument('--groupId', help='the group id')

options = parser.parse_args()


def failed(status, msg):
    raise Exception(msg)


def track():
    analytics.track(options.userId, options.event, anonymous_id=options.anonymousId,
                    properties=json_hash(options.properties), context=json_hash(options.context))


def page():
    analytics.page(options.userId, name=options.name, anonymous_id=options.anonymousId,
                   properties=json_hash(options.properties), context=json_hash(options.context))


def screen():
    analytics.screen(options.userId, name=options.name, anonymous_id=options.anonymousId,
                     properties=json_hash(options.properties), context=json_hash(options.context))


def identify():
    analytics.identify(options.userId, anonymous_id=options.anonymousId,
                       traits=json_hash(options.traits), context=json_hash(options.context))


def group():
    analytics.group(options.userId, options.groupId, json_hash(options.traits),
                    json_hash(options.context), anonymous_id=options.anonymousId)


def unknown():
    print()


analytics.write_key = options.writeKey
analytics.on_error = failed
analytics.debug = True

log = logging.getLogger('segment')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

switcher = {
    "track": track,
    "page": page,
    "screen": screen,
    "identify": identify,
    "group": group
}

func = switcher.get(options.type)
if func:
    func()
    analytics.shutdown()
else:
    print("Invalid Message Type " + options.type)
