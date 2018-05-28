
test:
	python setup.py test

dist:
	python setup.py sdist bdist_wheel upload

ci:
	@if [ "$(RUN_E2E_TESTS)" != "true" ]; then \
		echo "Skipping end to end tests."; \
	else \
		pip install analytics; \
		python ./simulator.py --writekey $(SEGMENT_WRITE_KEY) --type identify --userId Kevin; fi

.PHONY: test dist ci