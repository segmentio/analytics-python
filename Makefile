test:
	pylint --rcfile=.pylintrc --reports=y --exit-zero analytics | tee pylint.out
	# fail on pycodestyle errors on the code change
	git diff origin/master..HEAD analytics | pycodestyle --ignore=E501 --diff --statistics --count
	pycodestyle --ignore=E501 --statistics analytics > pycodestyle.out || true
	coverage run --branch --include=analytics/\* --omit=*/test* setup.py test

release:
	python setup.py sdist bdist_wheel upload

e2e_test:
	if [ "$(RUN_E2E_TESTS)" != "true" ]; then \
		echo "Skipping end to end tests."; \
	else \
		set -e; \
		echo "Running end to end tests..."; \
		wget https://github.com/segmentio/library-e2e-tester/releases/download/0.2.0/tester_linux_amd64; \
		chmod +x tester_linux_amd64; \
		chmod +x e2e_test.sh; \
		./tester_linux_amd64 -segment-write-key="$(SEGMENT_WRITE_KEY)" -webhook-auth-username="$(WEBHOOK_AUTH_USERNAME)" -webhook-bucket="$(WEBHOOK_BUCKET)" -path='./e2e_test.sh'; \
		echo "End to end tests completed!"; \
	fi

.PHONY: test dist e2e_test
