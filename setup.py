import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Don't import analytics-python module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'segment'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analytics'))
from analytics.version import VERSION

long_description = '''
Segment is the simplest way to integrate analytics into your application.
One API allows you to turn on any other analytics service. No more learning
new APIs, repeated code, and wasted development time.

This is the official python client that wraps the Segment REST API (https://segment.com).

Documentation and more details at https://github.com/segmentio/analytics-python
'''

install_requires = [
    "requests~=2.7",
    "six~=1.5",
    "monotonic~=1.5",
    "backoff~=1.10",
    "python-dateutil~=2.2"
]

tests_require = [
    "mock==2.0.0",
    "pylint==2.8.0",
    "flake8==3.7.9",
]

setup(
    name='segment-analytics-python',
    version=VERSION,
    url='https://github.com/segmentio/analytics-python',
    author='Segment',
    author_email='friends@segment.com',
    maintainer='Segment',
    maintainer_email='friends@segment.com',
    test_suite='analytics.test.all',
    packages=['segment.analytics', 'analytics.test'],
    license='MIT License',
    install_requires=install_requires,
    extras_require={
        'test': tests_require
    },
    description='The hassle-free way to integrate analytics into any python application.',
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
