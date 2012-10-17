from distutils.core import setup

long_description = '''
Segment.io (https://segment.io) is a segmentation-focused analytics platform.
If you haven\'t yet, register for a project at https://segment.io.

This is the official python client that wraps the Segment.io REST API (https://segment.io/docs).

Documentation and more details at https://github.com/segmentio/segment-python
'''


setup(
    name='segment',
    version='0.0.4',
    url='https://github.com/segmentio/segment-python',
    author='Ilya Volodarsky',
    author_email='ilya@segment.io',
    maintainer='Segment.io',
    maintainer_email='friends@segment.io',
    packages=['segment'],
    license='MIT License',
    install_requires=[
        'requests'
    ],
    description='Official Segment.io Python Client',
    long_description=long_description
)
