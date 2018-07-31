version := $(shell head -1 ruv/__version__.py | egrep -o "[0-9]+\.[0-9]+\.[0-9]+")
versionfile := ruv/__version__.py
distfile := dist/ruv-$(version).tar.gz

upload: $(versionfile)

$(versionfile): $(distfile)
	@echo Making version $(version)
	twine upload -r pypi dist/ruv-$(version)*

$(distfile):
	python setup.py sdist bdist_wheel

clean:
	rm -rfv build dist
