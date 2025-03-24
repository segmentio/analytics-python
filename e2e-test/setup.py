from setuptools import setup

setup(
    name='e2e-test',
    version='0.1.0',
    py_modules=['e2e-test'],
    install_requires=[
        'click', 'python-dotenv', 'python-dateutil', 'requests', 'PyJWT', 'backoff'
    ],
    entry_points={
        'console_scripts': [
            'e2e-test:run = src.cli:run',
        ],
    },
)
