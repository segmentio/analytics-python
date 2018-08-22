
test:
	python setup.py test

dist:
	python setup.py sdist bdist_wheel upload

e2e_test:
	if [ "$(RUN_E2E_TESTS)" != "true" ]; then \
		echo "Skipping end to end tests."; \
	else \
		set -e; \
		echo "Running end to end tests..."; \
		wget https://github.com/segmentio/library-e2e-tester/releases/download/0.1.1/tester_linux_amd64; \
		chmod +x tester_linux_amd64; \
		chmod +x e2e_test.sh; \
		./tester_linux_amd64 -segment-write-key="$SEGMENT_WRITE_KEY" -runscope-token="$RUNSCOPE_TOKEN" -runscope-bucket="$RUNSCOPE_BUCKET" -path='./e2e_test.sh'; \
		echo "End to end tests completed!"; \
	fi

.PHONY: test dist e2e_test
