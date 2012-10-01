
from stats import Statistics

host = 'https://api.segmentio.io'

endpoints = {
    'track': '/v2/track',
    'identify': '/v2/identify',
    'batch': '/v2/import'
}

api_key = None

stats = Statistics()
