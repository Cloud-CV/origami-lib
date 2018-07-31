help:
	@echo "HELP"
	@echo "make create-venv -> create virtual environment"
	@echo "make setup-dev   -> Setup development environment in ./venv"
	@echo "make test        -> Test origami_lib"
	@echo "make install     -> Install origami_lib"
	@echo "make clean       -> Clean setup environment"

create-venv:
	@virtualenv venv

setup-dev: clean create-venv
	@echo ">>> Setting up dev environment"
	@. ./venv/bin/activate && \
		pip install -r dev-requirements.txt && \
		pip install --editable .

test-lint:
	@yapf -r origami/

test: test-lint
	@tox

install:
	@echo ">>> Install Origami-lib"
	@python setup.py install

clean:
	@echo ">>> Cleaning environment"
	@rm -rf venv/


.PHONY: create-venv setup-dev test test-lint install clean help
