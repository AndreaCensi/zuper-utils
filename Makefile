test-zuper-all:
	rm -f .coverage
	rm -rf cover
	nosetests --cover-html --cover-tests --with-coverage --cover-package=zuper_json zuper_json   -v

test-zuper-schemas:
	rm -f .coverage
	rm -rf cover
	nosetests --cover-html --cover-tests --with-coverage --cover-package=zuper_json zuper_json zuper_schemas  -v


test-zuper-json-verbose:
	rm -f .coverage
	rm -rf cover
	nosetests --cover-html --cover-tests --with-coverage --cover-package=zuper_json  zuper_json zuper_schemas  -s -v


docker-36-build:
	docker build -f Dockerfile.python3.6 -t python36 .

test-it:
	docker run -it -v $(PWD):$(PWD) -w $(PWD) python36 /bin/bash
