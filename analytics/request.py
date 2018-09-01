from datetime import date, datetime
from dateutil.tz import tzutc
import logging
import json
from gzip import GzipFile
from requests.auth import HTTPBasicAuth
from requests import sessions
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

from analytics.version import VERSION
from analytics.utils import remove_trailing_slash

_session = sessions.Session()


def post(write_key, host=None, gzip=False, **kwargs):
    """Post the `kwargs` to the API"""
    log = logging.getLogger('segment')
    body = kwargs
    body["sentAt"] = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
    url = remove_trailing_slash(host or 'https://api.segment.io') + '/v1/batch'
    auth = HTTPBasicAuth(write_key, '')
    data = json.dumps(body, cls=DatetimeSerializer)
    log.debug('making request: %s', data)
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'analytics-python/' + VERSION
    }
    if gzip:
        headers['Content-Encoding'] = 'gzip'
        buf = StringIO()
        with GzipFile(fileobj=buf, mode='w') as gz:
            gz.write(data.encode())
        data = buf.getvalue()

    res = _session.post(url, data=data, auth=auth, headers=headers, timeout=15)

    if res.status_code == 200:
        log.debug('data uploaded successfully')
        return res

    try:
        payload = res.json()
        log.debug('received response: %s', payload)
        raise APIError(res.status_code, payload['code'], payload['message'])
    except ValueError:
        raise APIError(res.status_code, 'unknown', res.text)


class APIError(Exception):

    def __init__(self, status, code, message):
        self.message = message
        self.status = status
        self.code = code

    def __str__(self):
        msg = "[Segment] {0}: {1} ({2})"
        return msg.format(self.code, self.message, self.status)


class DatetimeSerializer(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)
