analytics-python
==============

A Python SDK client for [June](https://june.so), based on [analytics-python by Segment](https://github.com/segmentio/analytics-python).

Analytics helps you measure your users, product, and business. It unlocks insights into your app's funnel, core business metrics, and whether you have product-market fit.

## 🚀 How to get started

For example, you can capture data on any app:
```python
analytics.track('Order Completed', { price: 99.84 })
```

## 👨‍💻 Getting Started

Install `analytics-python` using pip:

```bash
pip3 install june-analytics-python
```

Now inside your app, you'll want to **set your** `write_key` before making any analytics calls:

```python
import analytics

analytics.write_key = 'YOUR_WRITE_KEY'
```
**Note** If you need to send data to multiple Segment sources, you can initialize a new Client for each `write_key`

## Documentation

Documentation is available at [https://www.june.so/docs/python](https://www.june.so/docs/python).

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
