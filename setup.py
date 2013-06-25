
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Don't import analytics-python module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analytics'))
from version import VERSION

long_description = '''
Segment.io is the simplest way to integrate analytics into your application.
One API allows you to turn on any other analytics service. No more learning
new APIs, repeated code, and wasted development time.

This is the official python client that wraps the Segment.io REST API (https://segment.io).

Documentation and more details at https://github.com/segmentio/analytics-python
'''

setup(
    name='analytics-python',
    version=VERSION,
    url='https://github.com/segmentio/analytics-python',
    author='Ilya Volodarsky',
    author_email='ilya@segment.io',
    maintainer='Segment.io',
    maintainer_email='friends@segment.io',
    packages=['analytics'],
    license='MIT License',
    install_requires=[
        'requests',
        'python-dateutil'
    ],
    description='The hassle-free way to integrate analytics into any python application.',
    long_description=long_description
)
