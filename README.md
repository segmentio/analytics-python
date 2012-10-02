segmentio-python
=============

[Segment.io](https://segment.io) is a segmentation-focused analytics platform. If you haven't yet,
register for a project [here](https://segment.io).

This is the official python client that wraps the [Segment.io REST API](https://segment.io/docs) .

You can use this driver to identify and track your users' events into your Segment.io project.

## Design

This client uses batching to efficiently record your events in aggregate, rather than making an HTTP
request every time. This means that it is safe to use in your web server controllers, or in back-end services
without worrying that it will make too many HTTP requests and slow down the system.

Check out the source to see how the batching, and async HTTP requests are handled. Feedback is very welcome!

## How to Use

#### Install
```bash
python setup.py install
```

#### Initialize the client

You can create seperate Segmentio clients, but the easiest and recommended way is to use the static Segmentio singleton client.

```python
import segmentio

api_key = live_api_key if is_production else test_api_key
segmentio.init(api_key)
```

#### Identify a User

Identifying a user ties all of their actions to an ID you recognize and records user traits you can segment by.

```python
segmentio.identify('random_session_id', 'ilya@segment.io', {
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
segmentio.track('random_session_id', 'ilya@segment.io', 'Played a Song', {
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

### Advanced

#### Troubleshooting

Use events to receive successful or failed events.
```python
def on_success(data, response):
    print 'Success', response


def on_failure(data, error):
    print 'Failure', error

segmentio.init('fakeid')

segmentio.on_success(on_success)
segmentio.on_failure(on_failure)
```

#### Importing Historical Data

You can import previous data by using the Identify / Track override that accepts a timestamp. If you are tracking things that are
happening now, we prefer that you leave the timestamp out and let our servers timestamp your requests.


#### License

(The MIT License)

Copyright (c) 2012 Segment.io Inc. <friends@segment.io>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.