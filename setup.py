from distutils.core import setup, find_packages

long_description = '''
Segment.io is the simplest way to integrate analytics into your application.
One API allows you to turn on any other analytics service. No more learning
new APIs, repeated code, and wasted development time.

This is the official python client that wraps the Segment.io REST API (https://segment.io).

Documentation and more details at https://github.com/segmentio/analytics-python
'''


setup(
    name='analytics-python',
    version='0.2.2',
    url='https://github.com/segmentio/analytics-python',
    author='Ilya Volodarsky',
    author_email='ilya@segment.io',
    maintainer='Segment.io',
    maintainer_email='friends@segment.io',
    packages=find_packages(),
    license='MIT License',
    install_requires=[
        'requests',
        'python-dateutil'
    ],
    description='The hassle-free way to integrate analytics into any python application.',
    long_description=long_description
)
