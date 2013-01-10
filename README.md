analytics-python
==============

analytics-python is a python client for [Segment.io](https://segment.io). It's the sister API of the popular [analytics.js](https://github.com/segmentio/analytics.js).

### Python Analytics Made Simple

[Segment.io](https://segment.io) is the simplest way to integrate analytics into your python application. One API allows you to turn on any other analytics service. No more learning new APIs, repeated code, and wasted development time.

```python
import analytics
analytics.init(api_key)
analytics.track(user_id='ilya@segment.io', event='Played a Song')
```

and turn on integrations with just one click at [Segment.io](https://segment.io).

![](http://img62.imageshack.us/img62/892/logosls.png)

... and many more.

### High Performance

This client uses an internal queue to efficiently send your events in aggregate, rather than making an HTTP
request every time. This means that it is safe to use in your high scale web server controllers, or in your backend services
without worrying that it will make too many HTTP requests and slow down the program. You no longer need to use a message queue to have analytics.

### Feedback

[Feedback is very welcome!](mailto:friends@segment.io)

## How to Use

#### Install
```bash
pip install analytics-python
```

#### Initialize the client

You can create separate analytics-python clients, but the easiest and recommended way is to use the static analytics-python singleton client.

```python
import analytics
analytics.init(api_key)
```

#### Identify a User

Whenever a user triggers an event, you’ll want to track it.

```python
analytics.identify(session_id='ajsk2jdj29fj298', user_id='ilya@segment.io', {
    "subscriptionPlan": "Free",
    "friends": 30
})
```

**sessionId** (string) is a unique id associated with an anonymous user **before** they are logged in. Even if the user
is logged in, you can still send us the **sessionId** or you can just use `null`.

**userId** (string) is the user's id **after** they are logged in. It's the same id as which you would recognize a signed-in user in your system. Note: you must provide either a `sessionId` or a `userId`.

**traits** (dict) is a dictionary with keys like `subscriptionPlan` or `favoriteGenre`. This argument is optional, but highly recommended—you’ll find these properties extremely useful later.

**timestamp** (datetime, optional) is a datetime object representing when the identify took place. If the event just happened, leave it `None` and we'll use the server's time. If you are importing data from the past, make sure you provide this argument.

#### Track an Action

Whenever a user triggers an event on your site, you’ll want to track it so that you can analyze and segment by those events later.

```python
analytics.track(session_id='skdj2jj2dj2j3i5', user_id='calvin@segment.io', event='Made a Comment', properties={
    "thatAided": "No-One",
    "comment":   "its 4AM!"
})

```


**sessionId** (string) is a unique id associated with an anonymous user **before** they are logged in. Even if the user
is logged in, you can still send us the **sessionId** or you can just use `null`.

**userId** (string) is the user's id **after** they are logged in. It's the same id as which you would recognize a signed-in user in your system. Note: you must provide either a `sessionId` or a `userId`.

**event** (string) describes what this user just did. It's a human readable description like "Played a Song", "Printed a Report" or "Updated Status".

**properties** (dict) is a dictionary with items that describe the event in more detail. This argument is optional, but highly recommended—you’ll find these properties extremely useful later.

**timestamp** (datetime, optional) is a datetime object representing when the identify took place. If the event just happened, leave it `None` and we'll use the server's time. If you are importing data from the past, make sure you provide this argument.


## Advanced

#### Batching Behavior

By default, the client will flush:

1. the first time it gets a message
1. every 20 messages (control with ```flush_at```)
1. if 10 seconds passes without a flush (control with ```flush_after```)

#### Turn Off Batching

When debugging or in short-lived programs, you might the client to make the
request right away. In this case, you can turn off batching by setting the
flush_at argument to 1.

```python
analytics.init('API_KEY', flush_at=1)
```


#### Turn Off Asynchronous Flushing

By default, the client will create a new thread to flush the messages to the server.
This is so the calling thread doesn't block, [as is important in server side
environments](http://ivolo.me/batching-rest-apis/).

If you're not running a server or writing performance sensitive code ,
you might want to flush on the same thread that calls identify/track.

In this case, you can disable asynchronous flushing like so:
```python
analytics.init('API_KEY', async=False)
```

#### Calling Flush Before Program End

If you're using the batching, it's a good idea to call
```python
analytics.flush(async=False)
```
before your program ends. This prevents your program from turning off with
items still in the queue.

#### Logging

analytics-python client uses the standard python logging module. By default, logging
is enabled and set at the logging.INFO level. If you want it to talk more,

```python
import logging
analytics.init('API_KEY', log_level=logging.DEBUG)
```

If you hate logging with an undying passion, try this:

```python
analytics.init('API_KEY', log=False)
```

#### Troubleshooting

**Turn off Async / Batching**

If you're having trouble sending messages to Segment.io, the first thing to try
is to turn off asynchronous flushing and disable batching, like so:

```python
analytics.init('API_KEY', async=False, flush_at=1)
```

Now the client will flush on every message, and every time you call identify or
track.

**Enable Debug Logging**

```python
analytics.init('API_KEY', async=False, flush_at=1, log_level=logging.DEBUG)
```

**Success / Failure Events**

Use events to receive successful or failed events.
```python
def on_success(data, response):
    print 'Success', response


def on_failure(data, error):
    print 'Failure', error

analytics.on_success(on_success)
analytics.on_failure(on_failure)
```

If there's an error, you should receive it as the second argument on the
on_failure event callback.

#### Importing Historical Data

You can import historical data by adding the timestamp argument (of type
datetime.datetime) to the identify / track calls. Note: if you are tracking
things that are happening now, we prefer that you leave the timestamp out and
let our servers timestamp your requests.

##### Example

```python
import datetime
from dateutil.tz import tzutc

when = datetime.datetime(2538, 10, 17, 0, 0, 0, 0, tzinfo=tzutc())
analytics.track(user_id=user_id, timestamp=when, event='Bought a game', properties={
        "game": "Duke Nukem Forever",
})
```

##### Python and Timezones

Python's standard datetime object is broken because it
[loses timezone information](http://stackoverflow.com/questions/2331592/datetime-datetime-utcnow-why-no-tzinfo).

```python
>>> import datetime
>>> print datetime.datetime.now().isoformat()
2012-10-17T11:51:17.351481
>>> print datetime.datetime.utcnow().isoformat()
2012-10-17T18:51:17.919517
>>> print datetime.datetime.now().tzinfo
None
>>> print datetime.datetime.utcnow().tzinfo
None
````

You'll notice that a utcnow() and a now() date are very different (since I'm
in PDT, they are exactly -7:00 hours different). However, by default, Python
doesn't  retain timezone information with the datetime object. This means that
our code can only guess about what timezone you were referring to.

If you have an ISO format timestamp string that contains timezone information, you
can do the following:
```python
>>> import dateutil.parser
>>> dateutil.parser.parse('2012-10-17T18:58:57.911Z')
datetime.datetime(2012, 10, 17, 18, 58, 57, 911000, tzinfo=tzutc())
```

Or if you're not parsing a string, make sure to
supply timezone information using [pytz](http://pytz.sourceforge.net/):
```python
from pytz import timezone
eastern = timezone('US/Eastern')
loc_dt = eastern.localize(datetime(2002, 10, 27, 6, 0, 0))
```

Whatever your method, please include the timezone information in your datetime objects or
else your data may be in the incorrect time.
```python
# checks that dt has a timezone
assert dt.tzinfo
```

##### Server Logs Example

```python

import dateutil.parser

import analytics
analytics.init('fakeid', async=False)

log = [
    '2012-10-17T18:58:57.911Z ilya@segment.io /purchased/tshirt'
]

for entry in log:

    (timestamp_str, user_id, url) = entry.split(' ')

    timestamp = dateutil.parser.parse(timestamp_str)  # datetime.datetime object has a timezone

    # have a timezone? check yo'self
    assert timestamp.tzinfo

    analytics.track(user_id=user_id, timestamp=timestamp, event='Bought a shirt', properties={
        "color": "Blue",
        "revenue": 17.90
    })

analytics.flush(async=False)


```

#### Full Client Configuration

If you hate defaults, than you'll love how configurable the Segment.io client is.
Check out these gizmos:

```python

import analytics
analytics.init('API_KEY',
                    log_level=logging.INFO, log=True,
                    flush_at=20, flush_after=datetime.timedelta(0, 10),
                    async=True
                    max_queue_size=100000)

```


* **log_level** (logging.LOG_LEVEL): The logging log level for the client talks to. Use log_level=logging.DEBUG to troubleshoot.
* **log** (bool): False to turn off logging completely, True by default
* **flush_at** (int): Specicies after how many messages the client will flush to the server. Use flush_at=1 to disable batching
* **flush_after** (datetime.timedelta): Specifies after how much time of no flushing that the server will flush. Used in conjunction with the flush_at size policy
* **async** (bool): True to have the client flush to the server on another thread, therefore not blocking code (this is the default). False to enable blocking and making the request on the calling thread.
* **max_queue_size** (int): Maximum number of elements allowed in the queue. If this condition is ever reached, that means you're identifying / tracking faster than you can flush. If this happens, let us know!

#### Testing

```bash
python test.py
```

#### License

```
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

Copyright (c) 2012 Segment.io Inc. <friends@segment.io>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.