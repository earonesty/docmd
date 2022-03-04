DELETE_ON_ERROR:

env:
	python -mvirtualenv env

requirements:
	pip install -r requirements.txt

readme:
	PYTHONPATH=../docmd python -mdocmd docmd > README.md

lint:
	python -m pylint docmd
	PYTHONPATH=. python -m pylint --rcfile tests/.pylintrc tests/
	black docmd tests

black:
	black docmd tests

test:
	python -mpytest --cov docmd -v tests

publish:
	rm -rf dist
	python3 setup.py bdist_wheel
	twine upload dist/*

install-hooks:
	pre-commit install



PHONY: env requirements readme lint black test publish install-hooks
