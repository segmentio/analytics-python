
test:
	python setup.py test

dist:
	python setup.py sdist bdist_wheel upload

e2e_test:
	@if [ "$(RUN_E2E_TESTS)" != "true" ]; then \
		echo "Skipping end to end tests."; \
	else \
		pip freeze; \
		python ./simulator.py --writekey $(SEGMENT_WRITE_KEY) --type identify --userId Kevin; fi

.PHONY: test dist e2e_test