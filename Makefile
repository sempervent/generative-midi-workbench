.PHONY: docs dev check commit install-hooks version changelog

docs:
	mkdocs build --strict

dev:
	mkdocs serve -a 0.0.0.0:8000

check:
	pre-commit run --all-files

install-hooks:
	pre-commit install --hook-type pre-commit --hook-type commit-msg

commit:
	cz commit

version:
	cz bump --check-consistency

changelog:
	cz changelog

