publish-to-pypi:
	@echo "Building distribution..."
	python setup.py sdist bdist_wheel
	@echo "Uploading to PyPI..."
	twine upload -u __token__ -p $PYPI_TOKEN dist/*


clear-docker:
	docker stop $(docker ps -a -q) && docker rm $(docker ps -a -q)
build-test:
	DOCKER_BUILDKIT=1 docker build -f _TEST/dockerfile -t repository-test .
run-test:
	docker-compose -f _TEST/docker-compose.yaml run --rm repository-test
