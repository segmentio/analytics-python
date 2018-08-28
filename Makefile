PYTHON := .env/bin/python

test:
	python setup.py test

# create virtual environment
.env:
	virtualenv .env -p python3

test:	# create virtual environment
	python setup.py test

clean:
	rm -rf .env

# upload to Pypi
pypi: .env
	$(PYTHON) setup.py sdist upload
