
test:
	python setup.py test

dist:
	python setup.py sdist bdist_wheel upload

e2e_test:
	@if [ "$(RUN_E2E_TESTS)" != "true" ]; then \
		echo "Skipping end to end tests."; \
	else \
		python ./simulator.py --writekey $(SEGMENT_WRITE_KEY) --type identify --userId Kevin; \
		python ./simulator.py --writekey $(SEGMENT_WRITE_KEY) --type track --userId Kevin --event "Python E2E Test Event"; \
		python ./simulator.py --writekey $(SEGMENT_WRITE_KEY) --type page --userId Kevin --name analytics-python --properties '{ \"url\": \"https://app.segment.com\" }'
		python ./simulator.py --writekey $(SEGMENT_WRITE_KEY) --type group --userId Kevin --group Developer; \
		python ./simulator.py --writekey $(SEGMENT_WRITE_KEY) --type screen --userId Kevin --name analytics-python; \
		fi

.PHONY: test dist e2e_test