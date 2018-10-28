from datetime import date, datetime
from dateutil.tz import tzutc
import logging
import json
import time

from requests.auth import HTTPBasicAuth
from requests import sessions
from retrying import retry

_session = sessions.Session()


@retry(wait_exponential_multiplier=500, wait_exponential_max=5000,
       stop_max_delay=20000)
def post(write_key, endpoint, **kwargs):
    """Post the `kwargs` to the API"""
    log = logging.getLogger('segment')
    body = kwargs
    #body["sentAt"] = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
    body["sentAt"] = int(time.time()*1000)
    auth = HTTPBasicAuth(write_key, '')
    data = json.dumps(body, cls=DatetimeSerializer)
    headers = { 'content-type': 'application/json', 'x-api-key': write_key }
    log.debug('making request: %s', data)
    res = _session.post(endpoint, data=data, auth=auth, headers=headers, timeout=15)

    if res.status_code == 200:
        log.debug('data uploaded successfully')
        return res

    try:
        payload = res.json()
        log.debug('received response: %s', payload)
        raise APIError(
            res.status_code,
            payload.get('code', '???'),
            payload.get('message', '???'))
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
