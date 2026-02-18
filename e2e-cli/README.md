# analytics-python e2e-cli

E2E test CLI for the [analytics-python](https://github.com/segmentio/analytics-python) SDK. Accepts a JSON input describing events and SDK configuration, sends them through the real SDK, and outputs results as JSON.

## Setup

```bash
cd e2e-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Usage

```bash
e2e-cli --input '{"writeKey":"...", ...}'
```

Or without installing:

```bash
python3 -m src.cli --input '{"writeKey":"...", ...}'
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
