
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
This is an unofficial fork of Segment's analytics SDK. This fork is 100% 
compatible with Segment's official SDK (it passes all the tests of the official
version), but it supports configuring the backend HTTPS endpoint to which the
events are delivered.

For more information on Segment go to https://segment.com.

Documentation and more details at https://github.com/findhotel/analytics-python
'''

install_requires = [
    "requests>=2.7,<3.0",
    "six>=1.7",
    "python-dateutil>2.1",
    "retrying>=1.3.3"
]

setup(
    name='analytics-python-findhotel',
    version=VERSION,
    url='https://github.com/findhotel/analytics-python',
    author='FindHotel BV',
    author_email='german@findhotel.net',
    maintainer='FindHotel BV',
    maintainer_email='german@findhotel.net',
    test_suite='analytics.test.all',
    packages=['analytics', 'analytics.test'],
    license='MIT License',
    install_requires=install_requires,
    description='FindHotel\'s fork of Segment\'s Python SDK.',
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
)
