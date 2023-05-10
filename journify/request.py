from datetime import date, datetime
from io import BytesIO
from gzip import GzipFile
import logging
import json
from requests import sessions

from journify.version import VERSION
from journify.utils import remove_trailing_slash

_session = sessions.Session()


def post(write_key, host=None, gzip=False, timeout=15, proxies=None, batch=None):
    log = logging.getLogger('journify')
    body = {
        'batch': batch,
        'writeKey': write_key,
        'context': {
            'library': {
                'name': 'journify-python-sdk',
                'version': VERSION,
            }
        }
    }

    url = remove_trailing_slash(host or 'https://t.journify.io') + '/v1/batch'
    data = json.dumps(body, cls=DatetimeSerializer)
    log.debug('making request: %s', data)
    headers = {
        'Content-Type': 'application/json',
    }

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
        "timeout": 15,
    }

    if proxies:
        kwargs['proxies'] = proxies

    log.error(f"Making request, url: {url},data: {data}")
    res = _session.post(url, data=data, headers=headers, timeout=timeout)
    log.error(f"res.status_code: {res.status_code}")

    if 200 <= res.status_code <= 299:
        log.debug('data uploaded successfully')
        return res

    try:
        payload = res.json()
        log.debug('received response: %s', payload)
        raise APIError(res.status_code, res.status_code, payload)
    except ValueError as e:
        raise APIError(res.status_code, 'unknown', res.text) from e


class APIError(Exception):

    def __init__(self, status, code, message):
        self.message = message
        self.status = status
        self.code = code

    def __str__(self):
        msg = "[Journify] {0}: {1} ({2})"
        return msg.format(self.code, self.message, self.status)


class DatetimeSerializer(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)
