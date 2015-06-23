
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
