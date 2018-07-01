PYTHON := .env/bin/python

# create virtual environment
.env:
	virtualenv .env -p python3

clean:
	rm -rf .env

# upload to Pypi
pypi: .env
	$(PYTHON) setup.py sdist upload
