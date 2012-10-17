from distutils.core import setup

setup(
    name='segment',
    version='0.0.2',
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
    long_description=open('README.md').read()
)
