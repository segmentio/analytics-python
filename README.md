﻿analytics-python
==============

[![Run Python Tests](https://github.com/North-Two-Five/analytics-python/actions/workflows/main.yml/badge.svg)](https://github.com/North-Two-Five/analytics-python/actions/workflows/main.yml)
[![.github/workflows/tests.yml](https://github.com/North-Two-Five/analytics-python/actions/workflows/tests.yml/badge.svg)](https://github.com/North-Two-Five/analytics-python/actions/workflows/tests.yml)



analytics-python is a python client for [Segment](https://segment.com)

<div align="center">
  <img src="https://user-images.githubusercontent.com/16131737/53616895-a1142d80-3b99-11e9-8e0e-594c0b0dcdc9.png"/>
  <p><b><i>You can't fix what you can't measure</i></b></p>
</div>

Analytics helps you measure your users, product, and business. It unlocks insights into your app's funnel, core business metrics, and whether you have a product-market fit.

## 🚀 How to get started
1. **Collect analytics data** from your app(s).
    - The top 200 Segment companies collect data from 5+ source types (web, mobile, server, CRM, etc.).
2. **Send the data to analytics tools** (for example, Google Analytics, Amplitude, Mixpanel).
    - Over 250+ Segment companies send data to eight categories of destinations such as analytics tools, warehouses, email marketing, and remarketing systems, session recording, and more.
3. **Explore your data** by creating metrics (for example, new signups, retention cohorts, and revenue generation).
    - The best Segment companies use retention cohorts to measure product-market fit. Netflix has 70% paid retention after 12 months, 30% after 7 years.

[Segment](https://segment.com) collects analytics data and allows you to send it to more than 250 apps (such as Google Analytics, Mixpanel, Optimizely, Facebook Ads, Slack, Sentry) just by flipping a switch. You only need one Segment code snippet, and you can turn integrations on and off at will, with no additional code. [Sign up with Segment today](https://app.segment.com/signup).

### 🤔 Why?
1. **Power all your analytics apps with the same data**. Instead of writing code to integrate all of your tools individually, send data to Segment, once.

2. **Install tracking for the last time**. We're the last integration you'll ever need to write. You only need to instrument Segment once. Reduce all of your tracking code and advertising tags into a single set of API calls.

3. **Send data from anywhere**. Send Segment data from any device, and we'll transform and send it on to any tool.

4. **Query your data in SQL**. Slice, dice, and analyze your data in detail with Segment SQL. We'll transform and load your customer behavioral data directly from your apps into Amazon Redshift, Google BigQuery, or Postgres. Save weeks of engineering time by not having to invent your data warehouse and ETL pipeline.

    For example, you can capture data on any app:
    ```python
    analytics.track('Order Completed', { price: 99.84 })
    ```
    Then, query the resulting data in SQL:
    ```sql
    select * from app.order_completed
    order by price desc
    ```

## 👨‍💻 Getting Started

Install `segment-analytics-python` using pip:

```bash
pip3 install segment-analytics-python
```

or you can clone this repo:
```bash
git clone https://github.com/segmentio/analytics-python.git

cd analytics-python

sudo python3 setup.py install
```

Now inside your app, you'll want to **set your** `write_key` before making any analytics calls:

```python
import segment.analytics as analytics

analytics.write_key = 'YOUR_WRITE_KEY'
```
**Note** If you need to send data to multiple Segment sources, you can initialize a new Client for each `write_key`

### 🚀 Startup Program
<div align="center">
  <a href="https://segment.com/startups"><img src="https://user-images.githubusercontent.com/16131737/53128952-08d3d400-351b-11e9-9730-7da35adda781.png" /></a>
</div>
If you are part of a new startup  (&lt;$5M raised, &lt;2 years since founding), we just launched a new startup program for you. You can get a Segment Team plan  (up to <b>$25,000 value</b> in Segment credits) for free up to 2 years — <a href="https://segment.com/startups/">apply here</a>!

## Documentation

Documentation is available at [https://segment.com/libraries/python](https://segment.com/libraries/python).

## License

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

Copyright (c) 2013 Segment Inc. <friends@segment.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

[![forthebadge](https://forthebadge.com/images/badges/built-with-love.svg)](https://forthebadge.com)
