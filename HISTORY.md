1.2.9 / 2017-11-28
==================

  * [Fix](https://github.com/segmentio/analytics-python/pull/102): Stringify non-string userIds and anonymousIds.

1.2.8 / 2017-09-20
==================

  * [Fix](https://github.com/segmentio/analytics-python/issues/94): Date objects are removed from event properties.
  * [Fix](https://github.com/segmentio/analytics-python/pull/98): Fix for regression introduced in version 1.2.4.

1.2.7 / 2017-01-31
==================

  * [Fix](https://github.com/segmentio/analytics-python/pull/92): Correctly serialize date objects.

1.2.6 / 2016-12-07
==================

  * dont add messages to the queue if send is false
  * drop py32 support

1.2.5 / 2016-07-02
==================

  * Fix outdated python-dateutil<2 requirement for python2 - dateutil > 2.1 runs is python2 compatible
  * Fix a bug introduced in 1.2.4 where we could try to join a thread that was not yet started

1.2.4 / 2016-06-06
==================

  * Fix race conditions in overflow and flush tests
  * Join daemon thread on interpreter exit to prevent value errors
  * Capitalize HISTORY.md (#76)
  * Quick fix for Decimal to send as a float

1.2.3 / 2016-03-23
==================

  * relaxing requests dep

1.2.2 / 2016-03-17
==================

  * Fix environment markers definition
  * Use proper way for defining conditional dependencies

1.2.1 / 2016-03-11
==================

  * fixing requirements.txt

1.2.0 / 2016-03-11
==================

  * adding versioned requirements.txt file

1.1.0 / 2015-06-23
==================

  * Adding fixes for handling invalid json types
  * Fixing byte/bytearray handling
  * Adding `logging.DEBUG` fix for `setLevel`
  * Support HTTP keep-alive using a Session connection pool
  * Suppport universal wheels
  * adding .sentAt
  * make it really testable
  * fixing overflow test
  * removing .io's
  * Update README.md
  * spacing

1.0.3 / 2014-09-30
==================

 * adding top level send option

1.0.2 / 2014-09-17
==================

 * fixing debug logging levels


1.0.1 / 2014-09-08
==================

 * fixing unicode handling, for write_key and events
 * adding six to requirements.txt and install scripts

1.0.0 / 2014-09-05
==================

 * updating to spec 1.0
 * adding python3 support
 * moving to analytics.write_key API
 * moving consumer to a separate thread
 * adding request retries
 * making analytics.flush() syncrhonous
 * adding full travis tests

0.4.4 / 2013-11-21
==================

 * add < python 2.7 compatibility by removing `delta.total_seconds`

0.4.3 / 2013-11-13
==================

 * added datetime serialization fix (alexlouden)

0.4.2 / 2013-06-26
==================

 * Added history.d change log
 * Merging https://github.com/segmentio/analytics-python/pull/14 to add support for lists and PEP8 fixes. Thanks https://github.com/dfee!
  * Fixing #12, adding static public API to analytics.__init__
