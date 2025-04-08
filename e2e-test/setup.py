from setuptools import setup, find_packages

setup(
    name='e2e-test',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click', 'python-dotenv', 'python-dateutil', 'requests', 'PyJWT', 'backoff'
    ],
    entry_points={
        'console_scripts': [
            'e2e-test:run = src.cli:run',
        ],
    },
)
