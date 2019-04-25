
PYTHON=python2

SOURCE_DIR=octoprint_excluderegion
TEST_DIR=test

SOURCE_FILES=$(shell find $(SOURCE_DIR) -type f)
TEST_FILES=$(shell find $(TEST_DIR) -type f)
DOC_FILES=$(shell find doc -type f)

BUILD_DIR=build

TESTENV=$(BUILD_DIR)/testenv

COMMON_DEPS_INSTALLED=$(BUILD_DIR)/.common-dependencies-installed
TESTENV_DEPS_INSTALLED=$(BUILD_DIR)/.testenv-dependencies-installed
SERVE_DEPS_INSTALLED=$(BUILD_DIR)/.serve-dependencies-installed

ACTIVATE_TESTENV=$(TESTENV)/bin/activate
COVERAGE_DIR=$(BUILD_DIR)/coverage
COVERAGE_FILE=$(COVERAGE_DIR)/coverage.dat

PIP_CACHE_DIR=$(BUILD_DIR)/pip_cache
PIP=pip --cache-dir $(PIP_CACHE_DIR)

# Configuration for the `serve` target.
OCTOPRINT_CONFIG_DIR=~/.octoprint2
OCTOPRINT_PORT=5001

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  clean                 Remove build, test and documentation artifacts"
	@echo "  test                  Run all tests"
	@echo "  coverage              Run code coverage"
	@echo "  coverage-report       Generate code coverage reports"
	@echo "  documentation         Generate documentation"
	@echo "  refresh-dependencies  (re)Run dependency installation"

$(TESTENV):
	$(PYTHON) -m virtualenv $(TESTENV)

$(COMMON_DEPS_INSTALLED): $(TESTENV)
	. $(ACTIVATE_TESTENV) \
		&& $(PIP) install --upgrade -r test-requirements.txt \
		&& $(PIP) install -e .
	touch $(COMMON_DEPS_INSTALLED)

$(TESTENV_DEPS_INSTALLED): $(COMMON_DEPS_INSTALLED)
	# pylint doesn't run with future <0.16, so we force an update beyond the version octoprint wants
	. $(ACTIVATE_TESTENV) \
		&& $(PIP) install --upgrade future
	rm -f $(SERVE_DEPS_INSTALLED)
	touch $(COMMON_DEPS_INSTALLED)
	touch $(TESTENV_DEPS_INSTALLED)

$(SERVE_DEPS_INSTALLED): $(COMMON_DEPS_INSTALLED)
	# Resets the future version back to the one required by octoprint
	. $(ACTIVATE_TESTENV) \
		&& pip install octoprint
	rm -f $(TESTENV_DEPS_INSTALLED)
	touch $(COMMON_DEPS_INSTALLED)
	touch $(SERVE_DEPS_INSTALLED)

clear-deps-installed:
	rm -f $(TESTENV_DEPS_INSTALLED)
	rm -f $(SERVE_DEPS_INSTALLED)

refresh-dependencies: clear-deps-installed $(TESTENV)

test: $(TESTENV_DEPS_INSTALLED) $(SOURCE_FILES) $(TEST_FILES)
	. $(ACTIVATE_TESTENV) \
		&& $(PYTHON) -W default -m unittest discover -v

serve: $(SERVE_DEPS_INSTALLED) $(SOURCE_FILES) $(TEST_FILES)
	. $(ACTIVATE_TESTENV) \
		&& octoprint -b $(OCTOPRINT_CONFIG_DIR) --port $(OCTOPRINT_PORT) serve

clean:
	-rm -f *.pyc $(SOURCE_DIR)/*.pyc $(TEST_DIR)/*.pyc
	-rm -rf $(BUILD_DIR)

$(COVERAGE_FILE): .coveragerc $(TESTENV_DEPS_INSTALLED) $(SOURCE_FILES) $(TEST_FILES)
	mkdir -p $(COVERAGE_DIR)
	-. $(ACTIVATE_TESTENV) \
		&& coverage run -m unittest discover -v

coverage: $(COVERAGE_FILE) clean-coverage-report
	. $(ACTIVATE_TESTENV) \
		&& coverage report --fail-under 80

clean-coverage-report:
	-rm -f $(COVERAGE_DIR)/report.txt
	-rm -rf $(COVERAGE_DIR)/html

coverage-report: $(COVERAGE_FILE)
	-. $(ACTIVATE_TESTENV) && coverage report > $(COVERAGE_DIR)/report.txt
	-rm -rf $(COVERAGE_DIR)/html
	-. $(ACTIVATE_TESTENV) && coverage html

doc: $(TESTENV_DEPS_INSTALLED) $(SOURCE_FILES) $(DOC_FILES)
	rm -rf $(BUILD_DIR)/doc
	. $(ACTIVATE_TESTENV) && sphinx-build -b html doc $(BUILD_DIR)/doc

lint: $(TESTENV_DEPS_INSTALLED) $(SOURCE_FILES) $(TEST_FILES)
	. $(ACTIVATE_TESTENV) && pylama $(SOURCE_DIR)
	#--report $(BUILD_DIR)/pylama_report.txt

.PHONY: help clean test serve clear-deps-installed refresh-dependencies coverage coverage-report clean-coverage-report doc lint
