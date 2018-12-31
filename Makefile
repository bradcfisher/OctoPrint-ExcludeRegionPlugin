
PYTHON=python2
PIP=pip

SOURCE_DIR=octoprint_excluderegion
TEST_DIR=test

SOURCE_FILES=$(shell find $(SOURCE_DIR) -type f)
TEST_FILES=$(shell find $(TEST_DIR) -type f)
DOC_FILES=$(shell find doc -type f)

BUILD_DIR=build

TESTENV=$(BUILD_DIR)/testenv
TESTENV_DEPS_INSTALLED=$(BUILD_DIR)/.testenv-dependencies-installed

ACTIVATE_TESTENV=$(TESTENV)/bin/activate
COVERAGE_DIR=$(BUILD_DIR)/coverage
COVERAGE_FILE=$(COVERAGE_DIR)/coverage.dat

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

$(TESTENV_DEPS_INSTALLED): $(TESTENV)
	# pylint doesn't run with future <0.16, so we force an update beyond the version octoprint wants
	. $(ACTIVATE_TESTENV) \
		&& $(PIP) install --upgrade -r test-requirements.txt \
		&& $(PIP) install -e . \
		&& $(PIP) install --upgrade future
	touch $(TESTENV_DEPS_INSTALLED)

#		&& $(PIP) install --upgrade coverage
#		&& $(PIP) install --upgrade sphinx
#		&& $(PIP) install --upgrade future <0.16
#		&& $(PIP) install --upgrade pylint
#		&& $(PIP) install --upgrade pylama
#		&& $(PIP) install https://get.octoprint.org/latest

clear-testenv-deps-installed:
	rm -f $(TESTENV_DEPS_INSTALLED)

refresh-dependencies: clear-testenv-deps-installed $(TESTENV_DEPS_INSTALLED)

test: $(TESTENV_DEPS_INSTALLED) $(SOURCE_FILES) $(TEST_FILES)
	. $(ACTIVATE_TESTENV) \
		&& $(PYTHON) -W default -m unittest discover -v

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

.PHONY: help clean test clear-testenv-deps-installed refresh-dependencies coverage coverage-report clean-coverage-report doc lint
