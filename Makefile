#VERSION := $(shell cat elmyra.ip.access.epo/elmyra/ip/version.py | awk '{ print $$3 }' | tr -d "'")
#$(error VERSION=$(VERSION))

js:
	@#echo bundling javascript for release=$(VERSION)
	node_modules/.bin/uglifyjs \
		elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/ops-*.js \
		--preamble "// (c) 2013,2014 Elmyra UG" \
		--mangle --compress --define \
		--source-map elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/lib/ipsuite-search.min.map \
		--source-map-url /static/js/lib/ipsuite-search.min.map \
		> elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/lib/ipsuite-search.min.js

sdist:
	cd elmyra.ip.access.epo; python setup.py sdist
	cd js.jquery_shorten; python setup.py sdist
	cd js.purl; python setup.py sdist
	cd js.underscore_string; python setup.py sdist

upload:
	rsync -auv */dist/* root@almera.elmyra.de:/root/install/ops-chooser/

upload-config:
	rsync elmyra.ip.access.epo/production.ini root@almera.elmyra.de:/opt/ops-chooser/

install:
	source .venv27/bin/activate; pip install cuisine; fab install:version=$(version)

package-and-install: sdist upload upload-config install
