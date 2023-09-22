from datetime import date, datetime
from io import BytesIO
from gzip import GzipFile
import logging
import json
from dateutil.tz import tzutc
from requests.auth import HTTPBasicAuth
from requests import sessions

import requests
from urllib.parse import urlencode

CLIENT_ID = "2TlKP068Khdw4jZaCHuWjXmvui2"
CLIENT_SECRET = "2TlKP068Khdw4jZaCHuWjXmvui2"
REDIRECT_URI = "http://api.segment.build"
BASE_API_ENDPOINT = "http://api.segment.build"

from segment.analytics.version import VERSION
from segment.analytics.utils import remove_trailing_slash

_session = sessions.Session()


def post(write_key, host=None, gzip=False, timeout=15, proxies=None, **kwargs):
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
        buf = BytesIO()
        with GzipFile(fileobj=buf, mode='w') as gz:
            # 'data' was produced by json.dumps(),
            # whose default encoding is utf-8.
            gz.write(data.encode('utf-8'))
        data = buf.getvalue()

    kwargs = {
        "data": data,
        "auth": auth,
        "headers": headers,
        "timeout": 15,
    }

    if proxies:
        kwargs['proxies'] = proxies

    res = _session.post(url, data=data, auth=auth,
                        headers=headers, timeout=timeout)

    if res.status_code == 200:
        log.debug('data uploaded successfully')
        return res

    try:
        payload = res.json()
        log.debug('received response: %s', payload)
        raise APIError(res.status_code, payload['code'], payload['message'])
    except ValueError:
        raise APIError(res.status_code, 'unknown', res.text)

class GetOathCode():
    
    def __init__(self, arg):
        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": "scope"
        }

        endpoint = "http://api.segment.build"
        endpoint = endpoint + '?' + urlencode(params)
        response = _session.post(endpoint)
        self.code = response
        return self.code
        

class GetOathToken():

    def __init__(self, arg, code):
        params = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }
        endpoint = "http://api.segment.build/token"
        response = requests.post(endpoint, params=params, headers = {"Accept": "application/json"}).json()
        access_token = response['access_token']
        print("Got Access Token")

        session = requests.session()
        session.headers = {"Authorization": f"token {access_token}"}

        base_api_endpoint = BASE_API_ENDPOINT

        response = session.get(base_api_endpoint)
        print(response)
        

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
