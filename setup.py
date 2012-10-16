from distutils.core import setup


setup(
    name='segment',
    version='0.0.1',
    url='https://github.com/segmentio/segment-python',
    packages=['segment'],
    license='MIT License',
    install_requires=[
        'requests'
    ],
    description='Official Segment.io Python Client',
    long_description=open('README.md').read()
)
