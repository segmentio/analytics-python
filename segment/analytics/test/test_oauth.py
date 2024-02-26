from datetime import datetime
import threading
import time
import unittest
import mock
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))
from segment.analytics.client import Client
import segment.analytics.oauth_manager
import requests

privatekey = '''-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDVll7uJaH322IN
PQsH2aOXZJ2r1q+6hpVK1R5JV1p41PUzn8pOxyXFHWB+53dUd4B8qywKS36XQjp0
VmhR1tQ22znQ9ZCM6y4LGeOJBjAZiFZLcGQNNrDFC0WGWTrK1ZTS2K7p5qy4fIXG
laNkMXiGGCawkgcHAdOvPTy8m1d9a6YSetYVmBP/tEYN95jPyZFIoHQfkQPBPr9W
cWPpdEBzasHV5d957akjurPpleDiD5as66UW4dkWXvS7Wu7teCLCyDApcyJKTb2Z
SXybmWjhIZuctZMAx3wT/GgW3FbkGaW5KLQgBUMzjpL0fCtMatlqckMD92ll1FuK
R+HnXu05AgMBAAECggEBAK4o2il4GDUh9zbyQo9ZIPLuwT6AZXRED3Igi3ykNQp4
I6S/s9g+vQaY6LkyBnSiqOt/K/8NBiFSiJWaa5/n+8zrP56qzf6KOlYk+wsdN5Vq
PWtwLrUzljpl8YAWPEFunNa8hwwE42vfZbnDBKNLT4qQIOQzfnVxQOoQlfj49gM2
iSrblvsnQTyucFy3UyTeioHbh8q2Xqcxry5WUCOrFDd3IIwATTpLZGw0IPeuFJbJ
NfBizLEcyJaM9hujQU8PRCRd16MWX+bbYM6Mh4dkT40QXWsVnHBHwsgPdQgDgseF
Na4ajtHoC0DlwYCXpCm3IzJfKfq/LR2q8NDUgKeF4AECgYEA9nD4czza3SRbzhpZ
bBoK77CSNqCcMAqyuHB0hp/XX3yB7flF9PIPb2ReO8wwmjbxn+bm7PPz2Uwd2SzO
pU+FXmyKJr53Jxw/hmDWZCoh42gsGDlVqpmytzsj74KlaYiMyZmEGbD7t/FGfNGV
LdLDJaHIYxEimFviOTXKCeKvPAECgYEA3d8tv4jdp1uAuRZiU9Z/tfw5mJOi3oXF
8AdFFDwaPzcTorEAxjrt9X6IjPbLIDJNJtuXYpe+dG6720KyuNnhLhWW9oZEJTwT
dUgqZ2fTCOS9uH0jSn+ZFlgTWI6UDQXRwE7z8avlhMIrQVmPsttGTo7V6sQVtGRx
bNj2RSVekTkCgYAJvy4UYLPHS0jWPfSLcfw8vp8JyhBjVgj7gncZW/kIrcP1xYYe
yfQSU8XmV40UjFfCGz/G318lmP0VOdByeVKtCV3talsMEPHyPqI8E+6DL/uOebYJ
qUqINK6XKnOgWOY4kvnGillqTQCcry1XQp61PlDOmj7kB75KxPXYrj6AAQKBgQDa
+ixCv6hURuEyy77cE/YT/Q4zYnL6wHjtP5+UKwWUop1EkwG6o+q7wtiul90+t6ah
1VUCP9X/QFM0Qg32l0PBohlO0pFrVnG17TW8vSHxwyDkds1f97N19BOT8ZR5jebI
sKPfP9LVRnY+l1BWLEilvB+xBzqMwh2YWkIlWI6PMQKBgGi6TBnxp81lOYrxVRDj
/3ycRnVDmBdlQKFunvfzUBmG1mG/G0YHeVSUKZJGX7w2l+jnDwIA383FcUeA8X6A
l9q+amhtkwD/6fbkAu/xoWNl+11IFoxd88y2ByBFoEKB6UVLuCTSKwXDqzEZet7x
mDyRxq7ohIzLkw8b8buDeuXZ
-----END PRIVATE KEY-----'''

def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, data, status_code):
            self.__dict__['headers'] = {'date': datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")}
            self.__dict__.update(data)
            self.status_code = status_code

        def json(self):
            return self.json_data
    if 'url' not in kwargs:
        kwargs['url'] = args[0]
    if kwargs['url'] == 'http://127.0.0.1:80/token':
        return MockResponse({"json_data" : {"access_token": "test_token", "expires_in": 4000}}, 200)
    elif kwargs['url'] == 'http://127.0.0.1:400/token':
        return MockResponse({"reason": "test_reason", "json_data" : {"error":"unrecoverable", "error_description":"nah"}}, 400)
    elif kwargs['url'] == 'http://127.0.0.1:429/token':
        return MockResponse({"reason": "test_reason", "headers" : {"X-RateLimit-Reset": time.time()*1000 + 2000}}, 429)
    elif kwargs['url'] == 'http://127.0.0.1:500/token':
        return MockResponse({"reason": "test_reason", "json_data" : {"error":"recoverable", "error_description":"nah"}}, 500)
    elif kwargs['url'] == 'http://127.0.0.1:501/token':
        if mocked_requests_get.error_count < 0 or mocked_requests_get.error_count > 0:
            if mocked_requests_get.error_count > 0:
                mocked_requests_get.error_count -= 1
            return MockResponse({"reason": "test_reason", "json_data" : {"error":"recoverable", "message":"nah"}}, 500)
        else: # return the number of errors if set above 0
            mocked_requests_get.error_count = -1
            return MockResponse({"json_data" : {"access_token": "test_token", "expires_in": 4000}}, 200)
    elif kwargs['url'] == 'https://api.segment.io/v1/batch':
        return MockResponse({}, 200)
    print("Unhandled mock URL")
    return MockResponse({'text':'Unhandled mock URL error'}, 404)
mocked_requests_get.error_count = -1

class TestOauthManager(unittest.TestCase):
    @mock.patch.object(requests.Session, 'post', side_effect=mocked_requests_get)
    def test_oauth_success(self, mock_post):
        manager = segment.analytics.oauth_manager.OauthManager("id", privatekey, "keyid", "http://127.0.0.1:80")
        self.assertEqual(manager.get_token(), "test_token")
        self.assertEqual(manager.max_retries, 3)
        self.assertEqual(manager.scope, "tracking_api:write")
        self.assertEqual(manager.auth_server, "http://127.0.0.1:80")
        self.assertEqual(manager.timeout, 15)
        self.assertTrue(manager.thread.is_alive)

    @mock.patch.object(requests.Session, 'post', side_effect=mocked_requests_get)
    def test_oauth_fail_unrecoverably(self, mock_post):
        manager = segment.analytics.oauth_manager.OauthManager("id", privatekey, "keyid", "http://127.0.0.1:400")
        with self.assertRaises(Exception) as context:
            manager.get_token()
        self.assertTrue(manager.thread.is_alive)
        self.assertEqual(mock_post.call_count, 1)
        manager.thread.cancel()

    @mock.patch.object(requests.Session, 'post', side_effect=mocked_requests_get)
    def test_oauth_fail_with_retries(self, mock_post):
        manager = segment.analytics.oauth_manager.OauthManager("id", privatekey, "keyid", "http://127.0.0.1:500")
        with self.assertRaises(Exception) as context:
            manager.get_token()
        self.assertTrue(manager.thread.is_alive)
        self.assertEqual(mock_post.call_count, 3)
        manager.thread.cancel()

    @mock.patch.object(requests.Session, 'post', side_effect=mocked_requests_get)
    @mock.patch('time.sleep', spec=time.sleep) # 429 uses sleep so it won't be interrupted
    def test_oauth_rate_limit_delay(self, mock_sleep, mock_post):
        manager = segment.analytics.oauth_manager.OauthManager("id", privatekey, "keyid", "http://127.0.0.1:429")
        manager._poller_loop()
        self.assertTrue(mock_sleep.call_args[0][0] > 1.9 and mock_sleep.call_args[0][0] <= 2.0)

class TestOauthIntegration(unittest.TestCase):
    def fail(self, e, batch=[]):
        self.failed = True

    def setUp(self):
        self.failed = False

    @mock.patch.object(requests.Session, 'post', side_effect=mocked_requests_get)
    def test_oauth_integration_success(self, mock_post):
        client = Client("write_key", on_error=self.fail, oauth_auth_server="http://127.0.0.1:80",
                        oauth_client_id="id",oauth_client_key=privatekey, oauth_key_id="keyid")
        client.track("user", "event")
        client.flush()
        self.assertFalse(self.failed)
        self.assertEqual(mock_post.call_count, 2)

    @mock.patch.object(requests.Session, 'post', side_effect=mocked_requests_get)
    def test_oauth_integration_failure(self, mock_post):
        client = Client("write_key", on_error=self.fail, oauth_auth_server="http://127.0.0.1:400",
                        oauth_client_id="id",oauth_client_key=privatekey, oauth_key_id="keyid")
        client.track("user", "event")
        client.flush()
        self.assertTrue(self.failed)
        self.assertEqual(mock_post.call_count, 1)

    @mock.patch.object(requests.Session, 'post', side_effect=mocked_requests_get)
    def test_oauth_integration_recovery(self, mock_post):
        mocked_requests_get.error_count = 2 # 2 errors and then success
        client = Client("write_key", on_error=self.fail, oauth_auth_server="http://127.0.0.1:501",
                        oauth_client_id="id",oauth_client_key=privatekey, oauth_key_id="keyid")
        client.track("user", "event")
        client.flush()
        self.assertFalse(self.failed)
        self.assertEqual(mock_post.call_count, 4)

    @mock.patch.object(requests.Session, 'post', side_effect=mocked_requests_get)
    def test_oauth_integration_fail_bad_key(self, mock_post):
        client = Client("write_key", on_error=self.fail, oauth_auth_server="http://127.0.0.1:80",
                        oauth_client_id="id",oauth_client_key="badkey", oauth_key_id="keyid")
        client.track("user", "event")
        client.flush()
        self.assertTrue(self.failed)

if __name__ == '__main__':
    unittest.main()