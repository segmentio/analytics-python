import logging
import io
import json
import gzip
import uuid
from functools import reduce
from threading import Thread
from datetime import datetime
from queue import Empty

import boto3

import analytics
from analytics.request import get


MB = 1024*1024

class S3Consumer(Thread):
    """Consumes the messages from the client's queue and pushes it to s3."""
    log = logging.getLogger('segment')

    _layouts = (
        ('YYYY', '%Y'),
        ('MM', '%m'),
        ('DD', '%d'),
        ('HH', '%H'),
    )

    def __init__(self, queue, write_key, upload_size=10*MB, on_error=None,
                 endpoint=None, dt=None, key_decorator=lambda x: x):
        """Create a consumer thread.
        upload_size is the size of chunk in bytes.
        """
        Thread.__init__(self)
        # Make consumer a daemon thread so that it doesn't block program exit
        self.daemon = True
        if upload_size < 1*MB:
            raise ValueError("upload_size should be >= {} (1 MB), got {}".format(1*MB, upload_size))
        self.upload_size = upload_size
        self.on_error = on_error
        self.queue = queue

        if dt is None:
            dt = datetime.now()

        self._reset_buffer()
        self.s3 = boto3.client('s3')

        s3_details = S3Consumer._s3_details(write_key, endpoint or analytics.endpoint)

        layouts = [(k, dt.strftime(v)) for (k, v) in self._layouts]
        prefix = key_decorator(
            reduce(lambda a, kv: a.replace(*kv), layouts, s3_details['prefix']))

        # %d token will be preserved for future substitution
        key_template = '{prefix}/{job_id}-part-%d.json.gz'

        self.s3_details = dict(
            bucket=s3_details['bucket'],
            key_template=key_template.format(
                prefix=prefix,
                job_id=str(uuid.uuid4())
            ),
            part=0,  # part of the file to uploaded, incremented on each upload cycle
            meta=s3_details.get('meta', None),
        )
        self.log.debug("s3 details: {}".format(self.s3_details))

        self.encoder = json.JSONEncoder()

        # It's important to set running in the constructor: if we are asked to
        # pause immediately after construction, we might set running to True in
        # run() *after* we set it to False in pause... and keep running forever.
        self.running = True

    def _reset_buffer(self):
        self.buf = io.BytesIO()

    def _writer(self):
        return gzip.GzipFile(fileobj=self.buf, mode='w')

    def _reader(self):
        return gzip.GzipFile(fileobj=self.buf, mode='r')

    @staticmethod
    def _s3_details(write_key, endpoint):
        """
        Goes to endpoint, reads details of the object where data should be uploaded to.
        """
        res = get(write_key, endpoint)
        if not ('s3_bucket' in res and 's3_prefix' in res):
            raise ValueError("Response should contain s3_bucket and s3_prefix keys, got {}".format(res))
        
        meta = None
        meta_raw = res.get('context', {}).get('meta', None)
        if meta_raw is not None:
            meta = dict([token.split('=') for token in meta_raw.split('&')])

        return {
            'bucket': res['s3_bucket'],
            'prefix': res['s3_prefix'],
            'meta': meta,
        }

    def run(self):
        """Runs the consumer."""
        self.log.debug('s3 consumer is running...')
        while self.running:
            self.upload()

        self.log.debug('s3 consumer exited.')

    def pause(self):
        """Pause the consumer."""
        self.running = False

    def upload(self):
        """Upload the next batch of items, return whether successful."""
        success = False
        total_items_to_upload = self.next()
        if total_items_to_upload == 0:
            return False

        try:
            self._upload_request()
            self.s3_details['part'] += 1
            self._reset_buffer()
            success = True
        except Exception as e:
            self.log.error('error uploading: %s', e)
            success = False
            if self.on_error:
                self.on_error(e, self._reader().read())
        finally:
            # mark items as acknowledged from queue
            for _ in range(total_items_to_upload):
                self.queue.task_done()

        return success

    def next(self):
        """Writes the next batch of items from the queue to the buffer."""
        queue = self.queue
        written_bytes = 0
        written_items = 0

        writer = self._writer()

        while written_bytes < self.upload_size or queue.empty():
            try:
                item = queue.get(block=True, timeout=0.5)
                s = self.encoder.encode(item) + '\n'
                written_bytes += writer.write(bytes(s, 'UTF-8'))
                written_items += 1
            except Empty:
                break

        self.log.debug("written {} bytes".format(written_bytes))
        return written_items

    def _upload_request(self, attempt=0):
        """Attempt to upload the data present in the buffer. It will throw Exception on failure."""

        bucket = self.s3_details['bucket']
        key = self.s3_details['key_template'] % (self.s3_details['part'])
        meta = self.s3_details.get('meta', None)

        kwargs = dict(
            ACL='bucket-owner-full-control',
            Bucket=bucket,
            Key=key,
        )
        if meta is not None:
            kwargs['Metadata'] = meta

        self.log.info("Uploading to s3 with args {}".format(kwargs))
        result = self.s3.put_object(
            Body=self.buf.getvalue(),
            **kwargs
        )
        self.log.info("Upload to s3 finished with result: {}".format(result))

        if result['HTTPStatusCode'] != 200:
            raise Exception("S3 upload failed: {}".format(result))
