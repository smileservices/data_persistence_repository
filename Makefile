publish-to-pypi:
	@echo "Building distribution..."
	python setup.py sdist bdist_wheel
	@echo "Uploading to PyPI..."
	twine upload -u __token__ -p $PYPI_TOKEN dist/*
