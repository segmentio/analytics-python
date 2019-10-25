import math
import sys
import os
import time
import uuid
from analytics import Client

def on_error(error, items):
    print("An error occurred:", error)

writeKey = os.getenv('writeKey', None)
events = os.getenv('events', 500000)

assert writeKey is not None, "Please configure a write key using the writeKey environment variable"

print(f'Sending {events} events to write key "{writeKey}"')

analytics = Client(
    writeKey,
    debug=True,
    on_error=on_error,
    max_queue_size=math.inf,
    upload_size=math.inf,
    upload_interval=1
)

start = time.time()

for it in range(events):
    sys.stdout.write(f"\rProgress: {round(it / events * 100, 1)}%")
    analytics.track('test', f'Iterated-{it}', {
        'plan': it
    })

print()
print('Shutting down..')
analytics.shutdown()

elapsed = time.time() - start

print(f'elapsed: {elapsed} seconds')
print(f'{round(events / elapsed)}rps average')