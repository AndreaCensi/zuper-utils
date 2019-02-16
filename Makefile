test-zuper-all:
	rm -f .coverage
	rm -rf cover
	nosetests --cover-html --cover-tests --with-coverage --cover-package=zuper_json zuper_json zuper_schemas  -v


test-zuper-json-verbose:
	rm -f .coverage
	rm -rf cover
	nosetests --cover-html --cover-tests --with-coverage --cover-package=zuper_json  zuper_json   -s -v

