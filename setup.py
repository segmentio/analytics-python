
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
Segment is the simplest way to integrate analytics into your application.
One API allows you to turn on any other analytics service. No more learning
new APIs, repeated code, and wasted development time.

This is the official python client that wraps the Segment REST API (https://segment.com).

Documentation and more details at https://github.com/segmentio/analytics-python
'''

install_requires = [
    "requests>=2.7,<3.0",
    "six>=1.5"
]

extras_require={
    ':python_version in "2.6, 2.7"': ['python-dateutil>=1,<2'],
    ':python_version in "3.2, 3.3, 3.4, 3.5"': ['python-dateutil>2']
}

setup(
    name='analytics-python',
    version=VERSION,
    url='https://github.com/segmentio/analytics-python',
    author='Segment',
    author_email='friends@segment.com',
    maintainer='Segment',
    maintainer_email='friends@segment.com',
    test_suite='analytics.test.all',
    packages=['analytics', 'analytics.test'],
    license='MIT License',
    install_requires=install_requires,
    extras_require=extras_require,
    description='The hassle-free way to integrate analytics into any python application.',
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
    ],
)
