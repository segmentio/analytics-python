segment-python
=============

[Segment.io](https://segment.io) is a segmentation-focused analytics platform. If you haven't yet,
register for a project [here](https://segment.io).

This is the official python client that wraps the [Segment.io REST API](https://segment.io/docs) .

You can use this driver to identify your users and track their events into your Segment.io project.

## Design

This client is non-blocking, and uses batching to efficiently record your events in aggregate, rather than making
an HTTP request every time. This means that it is safe to use in your web server controllers, or in back-end services
without worrying that it will make too many HTTP requests and slow down the system.

This implementation is optionally batching and optionally asynchronous
(uses another thread to periodically flush the queue).

[Feedback is very welcome!](friends@segment.io)

## How to Use

#### Install
```bash
pip install segment
```

#### Initialize the client

You can create separate Segmentio clients, but the easiest and recommended way is to use the static Segmentio singleton client.

```python
import segment

api_key = live_api_key if is_production else test_api_key
segment.initialize(api_key)
```

#### Identify a User

Identifying a user ties all of their actions to an ID you recognize and records user traits you can segment by.

```python
segment.identify('unique_session_id', 'ilya@segment.io', {
    "Subscription Plan": "Free",
    "Friends": 30
})
```

**sessionId** (string) is a unique id associated with an anonymous user before they are logged in. If the user
is logged in, you can use null here.

**userId** (string) is usually an email, but any unique ID will work. This is how you recognize a signed-in user
in your system. Note: it can be null if the user is not logged in. By explicitly identifying a user, you tie all of
their actions to their identity. This makes it possible for you to run things like segment-based email campaigns.

**traits** (dict) is a dictionary with keys like “Subscription Plan” or “Favorite Genre”. You can segment your
users by any trait you record. Once you record a trait, no need to send it again, so the traits argument is optional.

#### Track an Action

Whenever a user triggers an event on your site, you’ll want to track it so that you can analyze and segment by those events later.

```python
segment.track('unique_session_id', 'ilya@segment.io', 'Played a Song', {
    "Artist": "The Beatles",
    "Song": "Eleanor Rigby"
})

```

**sessionId** (string) is a unique id associated with an anonymous user before they are logged in. If the user
is logged in, you can use null here. Either this or the userId must be supplied.

**userId** (string) is usually an email, but any unique ID will work. This is how you recognize a signed-in user
in your system. Note: it can be null if the user is not logged in. By explicitly identifying a user, you tie all of
their actions to their identity. This makes it possible for you to run things like segment-based email campaigns. Either this or the sessionId must be supplied.

**event** (string) is a human readable description like "Played a Song", "Printed a Report" or "Updated Status". You’ll be able to segment by when and how many times each event was triggered.

**properties** (dict) is a dictionary with items that describe the event in more detail. This argument is optional, but highly recommended—you’ll find these properties extremely useful later.



## Advanced

#### Batching Behavior

By default, the client will flush:

1. the first time it gets a message
1. every 10 messages (control with ```flush_at```)
1. if 10 seconds passes without a flush (control with ```flush_after```)

#### Turn Off Batching

When debugging or in short-lived programs, you might the client to make the
request right away. In this case, you can turn off batching by setting the
flush_at argument to 1.

```python
segment.initialize('API_KEY', flush_at=1)
```

#### Turn Off Asynchronous Flushing

By default, the client will create a new thread to flush the messages to the server.
This is so the calling thread doesn't block, [as is important in server side
environments](http://ivolo.me/batching-rest-apis/).

If you're not running a server or writing performance sensitive code ,
you might want to flush on the same thread that calls identify/track.

In this case, you can disable asynchronous flushing like so:
```python
segment.initialize('API_KEY', async=False)
```

#### Calling Flush Before Program End

If you're using the asynchronous flushing, it's a good idea to call
```python
segment.flush()
```
before your program ends. This prevents your program from turning off with
items still in the queue.

#### Logging

Segment.io client uses the standard python logging module. By default, logging
is enabled and set at the logging.INFO level. If you want it to talk more,

```python
import logging
segment.initialize('API_KEY', log_level=logging.DEBUG)
```

If you hate logging with an undying passion, try this:

```python
segment.initialize('API_KEY', log=False)
```

#### Troubleshooting

**Turn off Async / Batching**

If you're having trouble sending messages to Segment.io, the first thing to try
is to turn off asynchronous flushing and disable batching, like so:

```python
segment.initialize('API_KEY', async=False, flush_at=1)
```

Now the client will flush on every message, and every time you call identify or
track.

**Enable Debug Logging**

```python
segment.initialize('API_KEY', async=False, flush_at=1, log_level=logging.DEBUG)
```

**Success / Failure Events**

Use events to receive successful or failed events.
```python
def on_success(data, response):
    print 'Success', response


def on_failure(data, error):
    print 'Failure', error

segment.on_success(on_success)
segment.on_failure(on_failure)
```

If there's an error, you should receive it as the second argument on the
on_failure event callback.

#### Importing Historical Data

You can import historical data by adding the timestamp argument (of type
datetime.datetime) to the identify / track calls. Note: if you are tracking
things that are happening now, we prefer that you leave the timestamp out and
let our servers timestamp your requests.

Here's an example of someone importing from their server logs:

```python

import dateutil.parser

import segment
segment.initialize('API_KEY', async=False)

for entry in log:


    user_id = entry.user.id # user@gmail.com

    # now find some time in the past
    timestamp_str = entry.timestamp; # 2010-05-08T23:41:54.000Z
    timestamp = dateutil.parser.parse(timestamp_str) # a datetime.datetime object

    segment.track(user_id=user_id, timestamp=timestamp, event='Bought a shirt', properties={
        "color": "Blue",
        "revenue": 17.90
    })

segment.flush()

```

#### Full Client Configuration

If you hate defaults, than you'll love how configurable the Segment.io client is.
Check out these gizmos:

```python

import segment
segment.initialize('API_KEY',
                    log_level=logging.INFO, log=True,
                    flush_at=10, flush_after=datetime.timedelta(0, 10),
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