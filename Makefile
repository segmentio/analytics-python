test:
	pylint --rcfile=.pylintrc --reports=y --exit-zero analytics | tee pylint.out
	# fail on pycodestyle errors on the code change
	git diff origin/master..HEAD analytics | pycodestyle --ignore=E501 --diff --statistics --count
	pycodestyle --ignore=E501 --statistics analytics > pycodestyle.out || true
	coverage run --branch --include=analytics/\* --omit=*/test* setup.py test

release:
	python setup.py sdist bdist_wheel upload

e2e_test:
	.buildscripts/e2e.sh

.PHONY: test release e2e_test
