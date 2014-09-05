from threading import Thread
import logging

from analytics.version import VERSION
from analytics.request import post


class Consumer(Thread):
    """Consumes the messages from the client's queue."""
    log = logging.getLogger('segment')

    def __init__(self, queue, write_key, upload_size=100, on_error=None):
        """Create a consumer thread."""
        Thread.__init__(self)
        self.daemon = True # set as a daemon so the program can exit
        self.upload_size = upload_size
        self.write_key = write_key
        self.on_error = on_error
        self.queue = queue
        self.retries = 3

    def run(self):
        """Runs the consumer."""
        self.log.debug('consumer is running...')

        self.running = True
        while self.running:
            self.upload()

        self.log.debug('consumer exited.')

    def pause(self):
        """Pause the consumer."""
        self.running = False

    def upload(self):
        """Upload the next batch of items, return whether successful."""
        success = False
        batch = self.next()
        if len(batch) == 0:
            return False

        try:
            self.request(batch)
            success = True
        except Exception as e:
            self.log.error('error uploading: %s', e)
            success = False
            if self.on_error:
                self.on_error(e, batch)
        finally:
            # cleanup
            for item in batch:
                self.queue.task_done()

            return success

    def next(self):
        """Return the next batch of items to upload."""
        queue = self.queue
        items = []
        item = self.next_item()
        if item is None:
            return items

        items.append(item)
        while len(items) < self.upload_size and not queue.empty():
            item = self.next_item()
            if item:
                items.append(item)

        return items

    def next_item(self):
        """Get a single item from the queue."""
        queue = self.queue
        try:
            item = queue.get(block=True, timeout=5)
            return item
        except Exception:
            return None

    def request(self, batch, attempt=0):
        """Attempt to upload the batch and retry before raising an error """
        try:
            post(self.write_key, batch=batch)
        except:
            if attempt > self.retries:
                raise
            self.request(batch, attempt+1)
