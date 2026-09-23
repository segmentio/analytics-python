# analytics-python e2e-cli

E2E test CLI for the [analytics-python](https://github.com/segmentio/analytics-python) SDK. Accepts a JSON input describing events and SDK configuration, sends them through the real SDK, and outputs results as JSON.

## Running E2E tests

### With devbox (recommended)

```bash
# From repo root — activates Python 3.12 and installs deps automatically
devbox shell

# Then from e2e-cli dir:
./run-e2e.sh
```

### Without devbox

Requires Python 3.9+ and Node.js 18+. Using a virtualenv is strongly recommended since macOS system Python is externally managed.

```bash
python3 -m venv .venv
source .venv/bin/activate
./run-e2e.sh
```

### Override sdk-e2e-tests location

```bash
E2E_TESTS_DIR=../my-e2e-tests ./run-e2e.sh
```

## Manual CLI usage

```bash
e2e-cli --input '{"writeKey":"...", ...}'
```

Or without installing:

```bash
python3 src/cli.py --input '{"writeKey":"...", ...}'
```

## Input Format

```jsonc
{
  "writeKey": "your-write-key",       // required
  "apiHost": "https://...",           // optional — defaults to https://api.segment.io
  "sequences": [                      // required — event sequences to send
    {
      "delayMs": 0,
      "events": [
        { "type": "track", "event": "Test", "userId": "user-1" }
      ]
    }
  ],
  "config": {                         // optional
    "flushAt": 100,                   // upload_size in Python SDK
    "flushInterval": 500,             // ms (auto-converted to seconds if > 100)
    "maxRetries": 10,
    "timeout": 15
  }
}
```

Note: Python is a server-side SDK — there is no CDN settings fetch, so `cdnHost` does not apply.

## Output Format

```json
{ "success": true, "sentBatches": 1 }
```

On failure:

```json
{ "success": false, "error": "description", "sentBatches": 0 }
```
