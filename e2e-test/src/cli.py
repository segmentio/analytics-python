import click
from dotenv import load_dotenv
import os
import sys
import logging
import json
from collections.abc import Iterable

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import segment.analytics as analytics  # noqa: E402 (ignore autopep8)


@click.command()
@click.option('--writeKey', type=str, help='Segment write key')
@click.option('--apiHost', type=str, help='Custom host')
@click.option('--payload', type=str, help='A JSON string that specifies the event payload.')
def run(writekey, payload, apihost=None):
    analytics.write_key = writekey

    if apihost is not None:
        analytics.host = apihost  # Set custom host

    analytics.debug = os.getenv('DEBUG_MODE')
    analytics.send = os.getenv('SEND_EVENTS')
    logger = log_config()

    try:
        # Decode the JSON payload
        decodedJson = json.loads(payload)
        dataObject = json.loads(decodedJson)

        # To ensure for loop do not raise exception when individual JSON is passed
        # we are converting the payload to a List having a single Dictionary as its item

        if not isinstance(dataObject, Iterable):  # Check if dataObject is non-iterable
            dataObject = [dataObject]
        elif isinstance(dataObject, dict):  # Check if dataObject is a dictionary
            dataObject = [dataObject]

        # Iterate over each item in the payload JSON
        for data in dataObject:

            specType = data.get('type') if data.get('type') is not None else None
            messageId = data.get('messageId') if data.get('messageId') is not None else None
            userId = data.get('userId') if data.get('userId') is not None else ''
            eventName = data.get('event') if data.get('event') is not None else None
            traits = data.get('traits') if data.get('traits') is not None else None
            properties = data.get('properties') if data.get('properties') is not None else None
            context = data.get('context') if data.get('context') is not None else None
            integrations = data.get('integrations') if data.get('integrations') is not None else None
            groupId = data.get('groupId') if data.get('groupId') is not None else None
            pageOrScreenName = data.get('name') if data.get('name') is not None else None
            pageOrScreenCategory = data.get('category') if data.get('category') is not None else None
            timestamp = data.get('timestamp') if data.get('timestamp') is not None else None
            anonymousId = data.get('anonymousId') if data.get('anonymousId') is not None else ''
            previousId = data.get('previousId') if data.get('previousId') is not None else None

            if specType == 'identify':
                analytics.identify(userId, traits, context, timestamp, anonymousId, integrations, messageId)
            elif specType == 'track':
                analytics.track(userId, eventName, properties, context, timestamp, anonymousId, integrations, messageId)
            elif specType == 'page':
                analytics.page(userId, pageOrScreenCategory, pageOrScreenName, properties,
                               context, timestamp, anonymousId, integrations, messageId)
            elif specType == 'screen':
                analytics.screen(userId, pageOrScreenCategory, pageOrScreenName, properties,
                                 context, timestamp, anonymousId, integrations, messageId)
            elif specType == 'alias':
                analytics.alias(previousId, userId, context, timestamp, integrations, messageId)
            elif specType == 'group':
                analytics.group(userId, groupId, traits, context, timestamp, anonymousId, integrations, messageId)
            else:
                raise Exception
    except Exception as e:
        logger.exception(e)
    finally:
        analytics.flush()


def log_config():
    # Create a logger object
    logger = logging.getLogger(os.getenv('APP_NAME'))
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    # Define the log message format
    formatter = logging.Formatter(os.getenv('LOG_FORMAT'))
    handler.setFormatter(formatter)

    # Attach the handler to the logger
    logger.addHandler(handler)

    return logger


if __name__ == '__main__':
    run()
