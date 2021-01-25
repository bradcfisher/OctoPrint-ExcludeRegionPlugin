
# python2 or python3
PYTHON=python3

SOURCE_DIR=octoprint_excluderegion
TEST_DIR=test

SOURCE_FILES=$(shell find $(SOURCE_DIR) -type f)
TEST_FILES=$(shell find $(TEST_DIR) -type f)
DOC_FILES=$(shell find doc -type f)

BUILD_DIR=build

BUILD_PY_DIR=$(BUILD_DIR)/$(notdir $(PYTHON))

TESTENV=$(BUILD_PY_DIR)/testenv

COMMON_DEPS_INSTALLED=$(BUILD_PY_DIR)/.common-dependencies-installed
TESTENV_DEPS_INSTALLED=$(BUILD_PY_DIR)/.testenv-dependencies-installed
SERVE_DEPS_INSTALLED=$(BUILD_PY_DIR)/.serve-dependencies-installed

ACTIVATE_TESTENV=$(TESTENV)/bin/activate && export BUILD_PY_DIR=$(BUILD_PY_DIR)
COVERAGE_DIR=$(BUILD_PY_DIR)/coverage
COVERAGE_FILE=$(COVERAGE_DIR)/coverage.dat
COVERAGE_PATTERN_FILE=$(COVERAGE_DIR)/last-coverage-pattern

PIP_CACHE_ARGS=--cache-dir $(BUILD_DIR)/pip_cache/$(notdir $(PYTHON))
PIP=pip

TEST_PATTERN=$(or $(PATTERN),test*.py)
UNITTEST=-m unittest discover -v --pattern $(TEST_PATTERN)
LINT_SOURCE_FILES=$(if $(filter undefined,$(origin PATTERN)),$(SOURCE_DIR),$(shell find $(SOURCE_DIR) -type f -name "$(PATTERN)"))
LINT_TEST_FILES=$(if $(filter undefined,$(origin PATTERN)),$(TEST_DIR),$(shell find $(TEST_DIR) -type f -name "$(PATTERN)"))

# Configuration for the `serve` target.
# Version of OctoPrint to run under ("latest" for current or release number (e.g. "1.3.12") for specific release)
OCTOPRINT_VERSION=latest
OCTOPRINT_CONFIG_DIR=~/.octoprint2
OCTOPRINT_PORT=5001

ifeq ($(OCTOPRINT_VERSION),latest)
  OCTOPRINT_URL=https://get.octoprint.org/latest
else
  OCTOPRINT_URL=https://github.com/foosel/OctoPrint/archive/$(OCTOPRINT_VERSION).zip
endif

ifeq ($(PYTHON),python2)
  TEST_REQUIREMENTS=test-py2-requirements.txt
else
  TEST_REQUIREMENTS=test-requirements.txt
endif

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  clean                 Remove build, test and documentation artifacts for the current version of Python"
	@echo "  clean-all             Remove all cache, build, test and documentation artifacts"
	@echo "  serve                 Launch OctoPrint server (version=$(OCTOPRINT_VERSION), port=$(OCTOPRINT_PORT), config dir=$(OCTOPRINT_CONFIG_DIR))"
	@echo "  test                  Run tests"
	@echo "  coverage              Run code coverage"
	@echo "  coverage-report       Generate code coverage reports"
	@echo "  lint                  Execute code analysis"
	@echo "  doc                   Generate documentation"
	@echo "  refresh-dependencies  (re)Run dependency installation"
	@echo "  help                  This help screen"
	@echo
	@echo "For the 'test', 'coverage', and 'coverage-report' targets, you can specify a glob"
	@echo "pattern to filter the tests files executed by assigning it via the PATTERN variable."
	@echo "For example: 'make test PATTERN=\"*Region*.py\"'"
	@echo
	@echo "The 'lint' target also supports PATTERN to filter the source files which are inspected."
	@echo

$(TESTENV):
	$(PYTHON) -m virtualenv --python=$(PYTHON) $(TESTENV)
	. $(ACTIVATE_TESTENV) \
		&& $(PIP) install --upgrade pip

$(COMMON_DEPS_INSTALLED): $(TESTENV)
  # Should be able to remove --no-use-pep517 once pip/setuptools fix the bootstrapping errors caused by PEP 517 in pip >= 19.0 (https://github.com/pypa/setuptools/issues/1644)
	. $(ACTIVATE_TESTENV) \
		&& $(PIP) $(PIP_CACHE_ARGS) install --upgrade -r $(TEST_REQUIREMENTS) --no-use-pep517 \
		&& $(PIP) $(PIP_CACHE_ARGS) install --upgrade $(OCTOPRINT_URL) --no-use-pep517 \
		&& $(PIP) $(PIP_CACHE_ARGS) install -e .
	touch $(COMMON_DEPS_INSTALLED)

$(TESTENV_DEPS_INSTALLED): $(COMMON_DEPS_INSTALLED)
	# pylint doesn't run with future <0.16, so we force an update beyond the version octoprint wants
	. $(ACTIVATE_TESTENV) \
		&& $(PIP) $(PIP_CACHE_ARGS) install --upgrade future
	rm -f $(SERVE_DEPS_INSTALLED)
	touch $(COMMON_DEPS_INSTALLED)
	touch $(TESTENV_DEPS_INSTALLED)

$(SERVE_DEPS_INSTALLED): $(COMMON_DEPS_INSTALLED)
	# Resets the future version back to the one required by octoprint
	. $(ACTIVATE_TESTENV) \
		&& $(PIP) $(PIP_CACHE_ARGS) install octoprint
	rm -f $(TESTENV_DEPS_INSTALLED)
	touch $(COMMON_DEPS_INSTALLED)
	touch $(SERVE_DEPS_INSTALLED)

clear-deps-installed:
	rm -f $(TESTENV_DEPS_INSTALLED)
	rm -f $(SERVE_DEPS_INSTALLED)
	rm -f $(COMMON_DEPS_INSTALLED)

refresh-dependencies: clear-deps-installed $(TESTENV)

test: $(TESTENV_DEPS_INSTALLED) $(SOURCE_FILES) $(TEST_FILES)
	. $(ACTIVATE_TESTENV) \
		&& $(PYTHON) -W default $(UNITTEST)

serve: $(SERVE_DEPS_INSTALLED) $(SOURCE_FILES) $(TEST_FILES)
	. $(ACTIVATE_TESTENV) \
		&& octoprint -b $(OCTOPRINT_CONFIG_DIR) --port $(OCTOPRINT_PORT) serve

clean:
	-rm -f *.pyc $(SOURCE_DIR)/*.pyc $(TEST_DIR)/*.pyc
	-rm -rf $(SOURCE_DIR)/__pycache__ $(TEST_DIR)/__pycache__
	-rm -rf $(BUILD_PY_DIR)

clean-all: clean
	-rm -rf $(BUILD_DIR)

# If the PATTERN is different than the last coverage run, removes the coverage data file
check-coverage-pattern:
	-@if [ -f $(COVERAGE_PATTERN_FILE) ]; then \
	  if [ "`cat $(COVERAGE_PATTERN_FILE)`" != "$(TEST_PATTERN)" ]; then \
	    rm $(COVERAGE_FILE) ; \
	  fi ; \
	else \
	  rm $(COVERAGE_FILE) ; \
	fi

$(COVERAGE_FILE): .coveragerc $(TESTENV_DEPS_INSTALLED) $(SOURCE_FILES) $(TEST_FILES)
	mkdir -p $(COVERAGE_DIR)
	echo -n "$(TEST_PATTERN)" > $(COVERAGE_PATTERN_FILE)
	-. $(ACTIVATE_TESTENV) \
		&& coverage run $(UNITTEST)

coverage: check-coverage-pattern $(COVERAGE_FILE) clean-coverage-report
	. $(ACTIVATE_TESTENV) \
		&& coverage report --fail-under 80

clean-coverage-report:
	-rm -f $(COVERAGE_DIR)/report.txt
	-rm -rf $(COVERAGE_DIR)/html

coverage-report: check-coverage-pattern $(COVERAGE_FILE)
	-. $(ACTIVATE_TESTENV) && coverage report > $(COVERAGE_DIR)/report.txt
	-rm -rf $(COVERAGE_DIR)/html
	-. $(ACTIVATE_TESTENV) && coverage html

doc: $(TESTENV_DEPS_INSTALLED) $(SOURCE_FILES) $(DOC_FILES)
	rm -rf $(BUILD_DIR)/doc
	. $(ACTIVATE_TESTENV) && sphinx-build -b html doc $(BUILD_DIR)/doc

lint: lint-source lint-tests

lint-source: $(TESTENV_DEPS_INSTALLED) $(SOURCE_FILES) $(TEST_FILES)
ifneq ($(strip $(LINT_SOURCE_FILES)),)
	-. $(ACTIVATE_TESTENV) && pylama $(LINT_SOURCE_FILES)
else
	@echo "lint-source: No source files match specified pattern"
endif

lint-tests: $(TESTENV_DEPS_INSTALLED) $(SOURCE_FILES) $(TEST_FILES)
ifneq ($(strip $(LINT_TEST_FILES)),)
	-. $(ACTIVATE_TESTENV) && pylama $(LINT_TEST_FILES)
else
	@echo "lint-tests: No test files match specified pattern"
endif

.PHONY: help clean clean-all test serve clear-deps-installed refresh-dependencies coverage coverage-report clean-coverage-report check-coverage-pattern doc lint lint-source lint-tests
