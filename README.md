# analytics-python

[![Build Status](https://travis-ci.org/FindHotel/analytics-python.svg?branch=master)](https://travis-ci.org/FindHotel/analytics-python)

analytics-python is a python client is a slightly modified version of [Segment's Python client library][segmentsdk]. This fork of Segment's `analytics-python` is fully compliant with the original Segment's SDK API, but it allows delivering the recorded events to a custom HTTP endpoint.

[segmentsdk]: https://github.com/segmentio/analytics-python

## Usage

You can package directly, in this case default `http` transport will be used:

```python
import analytics

# This key will be passed in the `x-api-key` header of every request
analytics.write_key='AWS_API_GATEWAY_KEY'

# The custom endpoint to where the events will be delivered to
analytics.endpoint='https://segment.fih.io/v1/[endpoint-key]'

analytics.track('kljsdgs99', 'SignedUp', {'plan': 'Enterprise'})
analytics.flush()
```

Use client with custom error handling function:

```python

import analytics

ANALYTICS_WRITE_KEY='AWS_API_GATEWAY_KEY'
ANALYTICS_ENDPOINT='https://segment.fih.io/v1/[endpoint-key]'

def log_error(e, batch):
  print("exception: {}, batch: {}".format(e, batch), flush=True)

client = analytics.Client(
  endpoint=ANALYTICS_ENDPOINT,
  write_key=ANALYTICS_WRITE_KEY,
  debug=analytics.debug,
  on_error=log_error,
  send=analytics.send,
  max_queue_size=analytics.max_queue_size,
  upload_size=analytics.upload_size
)

client.track(...)
client.flush()
```

### Using S3 transport

When using `s3` transport SDK will upload data directly to AWS S3 bypassing http interface.

```python

MB = 1024*1024

c = Client(
     write_key="write-key",
     endpoint="https://segment.fih.io/v1/[endpoint-key]",
     upload_size=1*MB,
     transport='s3',
     max_queue_size=1000000,
)

for i in range(30000):
     c.track(
          user_id='pavel',
          event='UUIDGenerated',
          properties=dict(id=str(uuid.uuid4()), counter=i)
     )
     if i % 10000 == 0:
          c.flush()

c.flush()
assert False
```

## More information

The documentation for Segment's Python SDK that this repository is based on is available at [https://segment.com/libraries/python](https://segment.com/libraries/python). You can use Segment's docs to get familiar with the API.

## License

```txt
WWWWWW||WWWWWW
 W W W||W W W
      ||
    ( OO )__________
     /  |           \
    /o o|    MIT     \
    \___/||_||__||_|| *
         || ||  || ||
        _||_|| _||_||
       (__|__|(__|__|
```

(The MIT License)

Copyright (c) 2013 Segment Inc. <friends@segment.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

