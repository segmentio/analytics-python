
test:
	python setup.py test

dist:
	python setup.py sdist bdist_wheel upload

.PHONY: test dist