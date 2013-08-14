import json
from datetime import datetime
from dateutil.tz import tzlocal, tzutc


def is_naive(dt):
    """ Determines if a given datetime.datetime is naive. """
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


def guess_timezone(dt):
    """ Attempts to convert a naive datetime to an aware datetime """
    if is_naive(dt):
        # attempts to guess the datetime.datetime.now() local timezone
        # case, and then defaults to utc

        delta = datetime.now() - dt
        if delta.total_seconds() < 5:
            # this was created using datetime.datetime.now()
            # so we are in the local timezone
            return dt.replace(tzinfo=tzlocal())
        else:
            # at this point, the best we can do (I htink) is guess UTC
            return dt.replace(tzinfo=tzutc())

    return dt

class DatetimeSerializer(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)
