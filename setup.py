import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
# Don't import journify-python-sdk module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'journify'))
from version import VERSION

long_description = '''
Journify lets marketers unify customer data and deliver personalized experiences – no code or engineering favors required.

This is the official python client that wraps the Journify REST API (https://journify.io).

Documentation and more details at https://github.com/journifyio/journify-python-sdk
'''

install_requires = [
    "requests~=2.7",
    "monotonic~=1.5",
    "backoff~=2.1",
    "python-dateutil~=2.2"
]

tests_require = [
    "pylint==2.8.0",
]

setup(
    name='journify-python-sdk',
    version=VERSION,
    url='https://github.com/journifyio/journify-python-sdk',
    author='Journify',
    author_email='integrations@journify.io',
    maintainer='Journify',
    maintainer_email='integrations@journify.io',
    test_suite='journify.test.all',
    packages=['journify', 'journify.test'],
    python_requires='>=3.6.0',
    license='MIT License',
    install_requires=install_requires,
    extras_require={
        'test': tests_require
    },
    description='The hassle-free way to integrate Journify into any python application.',
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
