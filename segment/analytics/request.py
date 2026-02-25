from datetime import date, datetime
from io import BytesIO
from gzip import GzipFile
import logging
import json
import base64
from dateutil.tz import tzutc

from requests import sessions

from segment.analytics.version import VERSION
from segment.analytics.utils import remove_trailing_slash

_session = sessions.Session()

# Maximum Retry-After delay to respect (5 minutes)
MAX_RETRY_AFTER_SECONDS = 300


def parse_retry_after(response):
    """
    Parse Retry-After header from response.
    Returns the delay in seconds, or None if header is not present or invalid.
    Caps the value at MAX_RETRY_AFTER_SECONDS.
    """
    retry_after = response.headers.get('Retry-After')
    if not retry_after:
        return None

    try:
        # Try parsing as integer (delay in seconds)
        delay = int(retry_after)
        # Ensure delay is non-negative before applying upper bound
        return min(max(delay, 0), MAX_RETRY_AFTER_SECONDS)
    except ValueError:
        # Could be HTTP-date format, but for simplicity we'll skip that
        # Most APIs use integer seconds
        return None


def post(write_key, host=None, gzip=False, timeout=15, proxies=None, oauth_manager=None, retry_count=0, **kwargs):
    """Post the `kwargs` to the API"""
    log = logging.getLogger('segment')
    body = kwargs
    if not "sentAt" in body.keys():
        body["sentAt"] = datetime.now(tz=tzutc()).isoformat()
    body["writeKey"] = write_key
    url = remove_trailing_slash(host or 'https://api.segment.io') + '/v1/batch'
    auth = None
    if oauth_manager:
        auth = oauth_manager.get_token()
    data = json.dumps(body, cls=DatetimeSerializer)
    log.debug('making request: %s', data)
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'analytics-python/' + VERSION,
        'X-Retry-Count': str(retry_count)
    }

    # Add Authorization header - prefer OAuth Bearer token, fallback to Basic auth
    if auth:
        headers['Authorization'] = 'Bearer {}'.format(auth)
    else:
        # Basic auth with write key (format: "writeKey:" encoded in base64)
        credentials = '{}:'.format(write_key)
        encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers['Authorization'] = 'Basic {}'.format(encoded)

    if gzip:
        headers['Content-Encoding'] = 'gzip'
        buf = BytesIO()
        with GzipFile(fileobj=buf, mode='w') as gz:
            # 'data' was produced by json.dumps(),
            # whose default encoding is utf-8.
            gz.write(data.encode('utf-8'))
        data = buf.getvalue()

    kwargs = {
        "data": data,
        "headers": headers,
        "timeout": timeout,
    }

    if proxies:
        kwargs['proxies'] = proxies

    try:
        res = _session.post(url, **kwargs)
    except Exception as e:
        raise e

    if res.status_code == 200:
        log.debug('data uploaded successfully')
        return res

    if oauth_manager and res.status_code in [400, 401, 403, 511]:
        oauth_manager.clear_token()

    try:
        payload = res.json()
        log.debug('received response: %s', payload)
        raise APIError(res.status_code, payload['code'], payload['message'], res)
    except (ValueError, KeyError):
        log.error('Unknown error: [%s] %s', res.status_code, res.reason)
        raise APIError(res.status_code, 'unknown', res.text, res)


class APIError(Exception):

    def __init__(self, status, code, message, response=None):
        self.message = message
        self.status = status
        self.code = code
        self.response = response

    def __str__(self):
        msg = "[Segment] {0}: {1} ({2})"
        return msg.format(self.code, self.message, self.status)


class DatetimeSerializer(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)
