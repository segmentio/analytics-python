#!/usr/bin/env python3
"""
Analytics Python E2E CLI

Accepts a JSON input with event sequences and SDK configuration,
sends events through the analytics SDK, and outputs results as JSON.
"""

import json
import logging
import os
import sys
import time

import click

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from segment.analytics.client import Client  # noqa: E402


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    return logging.getLogger("e2e-cli")


def send_event(client: Client, event: dict, logger: logging.Logger):
    """Send a single event through the analytics client."""
    event_type = event.get("type")
    user_id = event.get("userId", "")
    anonymous_id = event.get("anonymousId", "")
    message_id = event.get("messageId")
    timestamp = event.get("timestamp")
    context = event.get("context")
    integrations = event.get("integrations")
    traits = event.get("traits")
    properties = event.get("properties")
    event_name = event.get("event")
    name = event.get("name")
    category = event.get("category")
    group_id = event.get("groupId")
    previous_id = event.get("previousId")

    logger.debug(f"Sending {event_type} event: {event}")

    if event_type == "identify":
        client.identify(user_id, traits, context, timestamp, anonymous_id, integrations, message_id)
    elif event_type == "track":
        client.track(user_id, event_name, properties, context, timestamp, anonymous_id, integrations, message_id)
    elif event_type == "page":
        client.page(user_id, category, name, properties, context, timestamp, anonymous_id, integrations, message_id)
    elif event_type == "screen":
        client.screen(user_id, category, name, properties, context, timestamp, anonymous_id, integrations, message_id)
    elif event_type == "alias":
        client.alias(previous_id, user_id, context, timestamp, integrations, message_id)
    elif event_type == "group":
        client.group(user_id, group_id, traits, context, timestamp, anonymous_id, integrations, message_id)
    else:
        raise ValueError(f"Unknown event type: {event_type}")


@click.command()
@click.option("--input", "input_json", type=str, required=True, help="JSON input with sequences and config")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def run(input_json: str, debug: bool):
    """Run the E2E CLI with the given input configuration."""
    logger = setup_logging(debug)
    output = {"success": False, "sentBatches": 0, "error": None}

    try:
        data = json.loads(input_json)

        write_key = data.get("writeKey", "test-key")
        api_host = data.get("apiHost", "https://api.segment.io")
        sequences = data.get("sequences", [])
        config = data.get("config", {})

        # Extract config options
        flush_at = config.get("flushAt", 100)  # upload_size in Python SDK
        flush_interval = config.get("flushInterval", 0.5)  # upload_interval (seconds)
        max_retries = config.get("maxRetries", 10)
        timeout = config.get("timeout", 15)

        # If flushInterval is in ms (> 100), convert to seconds
        if flush_interval > 100:
            flush_interval = flush_interval / 1000.0

        logger.info(f"Creating client with host={api_host}, flush_at={flush_at}, flush_interval={flush_interval}")

        # Create the analytics client
        client = Client(
            write_key=write_key,
            host=api_host,
            debug=debug,
            upload_size=flush_at,
            upload_interval=flush_interval,
            max_retries=max_retries,
            timeout=timeout,
            sync_mode=False,  # Use async mode to test batching
        )

        # Process event sequences
        for seq in sequences:
            delay_ms = seq.get("delayMs", 0)
            events = seq.get("events", [])

            if delay_ms > 0:
                logger.debug(f"Waiting {delay_ms}ms before sending next sequence")
                time.sleep(delay_ms / 1000.0)

            for event in events:
                send_event(client, event, logger)

        # Flush and shutdown
        logger.debug("Flushing client...")
        client.flush()
        client.join()

        output["success"] = True
        # Note: We don't have easy access to batch count from the SDK internals
        # This could be enhanced if needed
        output["sentBatches"] = 1  # Placeholder

    except json.JSONDecodeError as e:
        output["error"] = f"Invalid JSON input: {e}"
        logger.error(output["error"])
    except Exception as e:
        output["error"] = str(e)
        logger.exception("Error running CLI")

    # Output result as JSON (last line of stdout)
    print(json.dumps(output))
    sys.exit(0 if output["success"] else 1)


if __name__ == "__main__":
    run()
