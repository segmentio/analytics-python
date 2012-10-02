from distutils.core import setup


setup(
    name='segmentio',
    version='0.0.1',
    url='https://github.com/segmentio/segmentio-python',
    packages=['segmentio'],
    license='MIT License',
    install_requires=[
        'grequests'
    ],
    description='Official Segment.io Python Client',
    long_description=open('README.md').read()
)
