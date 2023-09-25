from datetime import date, datetime
import logging
import threading 
import time
import uuid
from requests import sessions
import jwt

_session = sessions.Session()

class OauthManager(object):
    def __init__(self,
                 client_id,
                 client_key,
                 key_id,
                 auth_server,
                 scope,
                 timeout,
                 max_retries):
        self.client_id = client_id
        self.client_key = client_key
        self.key_id = key_id
        self.auth_server = auth_server
        self.scope = scope
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_count = 0
        self.thread = None
        self.token_mutex = threading.Lock()
        self.token = None
        self.error = None

    def get_token(self):
        with self.token_mutex:
            if self.token:
                return self.token
        # No good token, start the loop
        self.thread = threading.Thread(target=self._poller_loop)
        self.thread.start()

        while True:
            # Wait for a token or error
            with self.token_mutex:
                if self.token:
                    return self.token
                if self.error:
                    error = self.error
                    self.error = None
                    raise Exception(error)
            if self.thread:
                self.thread.join()
    
    def clear_token(self):
        with self.token_mutex:
            self.token = None

    def _request_token(self):
        jwt_body = {
            "iss": self.client_id,
            "sub": self.client_id,
            "aud": "https://oauth2.segment.io",
            "iat": time.time(),
            "exp": time.time() + 60,
            "jti": uuid.uuid4()
        }

        signed_jwt = jwt.encode(
            payload=jwt_body,
            key=self.client_key,
            algorithm="RS256",
            headers={"kid": self.key_id},
        )

        request_body = f'grant_type=client_credentials&client_assertion_type='\
            'urn:ietf:params:oauth:client-assertion-type:jwt-bearer&'\
            'client_assertion={signed_jwt}&scope={self.scope}'
        
        token_endpoint = f'{self.auth_server}/token'

        res = _session.post(token_endpoint, data=request_body, timeout=self.timeout,
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})
        return res
    
    def _poller_loop(self):
        refresh_timer_ms = 25
        response = None

        try:
            response = self._request_token()
        except Exception as e:
            logging.error(e)
            self.retry_count += 1
            if self.retry_count < self.max_retries:
                self.thread = threading.Timer(refresh_timer_ms / 1000.0, self._poller_loop)
                self.thread.setDaemon(True)
                self.thread.start()
                return
            # Too many retries, giving up
            self.error = e
            return

        if response.status_code == 200:
            data = None
            try:
                data = response.json()
            except Exception as e:
                self.retry_count += 1
                if self.retry_count < self.max_retries:
                    self.thread = threading.Timer(refresh_timer_ms / 1000.0, self._poller_loop)
                    self.thread.setDaemon(True)
                    self.thread.start()
                    return
                # Too many retries, giving up
                self.error = e
                return
            try:
                with self.token_mutex:
                    self.token = data['access_token']
                # success!
                self.retry_count = 0
            except Exception as e:
                # No access token in response?
                logging.log(e)
            try:
                refresh_timer_ms = int(data['expires_in']) / 2 * 1000
            except Exception as e:
                refresh_timer_ms = 60 * 1000

        elif response.status_code == 429:
            self.retry_count += 1
            rate_limit_reset_time = None
            try:
                rate_limit_reset_time = int(response.headers.get("X-RateLimit-Reset"))
            except Exception as e:
                logging.log(e)
            if rate_limit_reset_time:
                refresh_timer_ms = rate_limit_reset_time - time.time() * 1000
            else:
                refresh_timer_ms = 5 * 1000
        elif response.status_code in [400, 401, 415]:
            # unrecoverable errors
            self.retry_count = 0
            self.error = Exception(f'[{response.status_code}] {response.reason}')
            logging.log(self.error)
            return
        else:
            # any other error
            logging.log(f'[{response.status_code}] {response.reason}')
            self.retry_count += 1

        if self.retry_count % self.max_retries == 0:
            # every time we pass the retry count, put up an error to release any waiting token requests
            self.error = Exception(f'[{response.status_code}] {response.reason}')

        # loop
        self.thread = threading.Timer(refresh_timer_ms / 1000.0, self._poller_loop)
        self.thread.setDaemon(True)
        self.thread.start()
