create-venv:
	@virtualenv venv

setup-dev: clean create-venv
	@echo ">>> Setting up dev environment"
	@. ./venv/bin/activate && \
		pip install -r requirements-dev.txt && \
		pip install --editable .

test-lint:
	@yapf -r origami/

test: test-lint

install:
	@echo ">>> Install Origami-lib"
	@python setup.py install

clean:
	@echo ">>> Cleaning environment"
	@rm -rf venv/


.PHONY: create-venv setup-dev test test-lint install clean
