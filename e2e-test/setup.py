from setuptools import setup, find_packages

setup(
    name='e2e-cli',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
    ],
    entry_points={
        'console_scripts': [
            'e2e-cli = src.cli:run',
        ],
    },
)
