#VERSION := $(shell cat elmyra.ip.access.epo/elmyra/ip/version.py | awk '{ print $$3 }' | tr -d "'")
#$(error VERSION=$(VERSION))

js:
	@#echo bundling javascript for release=$(VERSION)

	# application
	node_modules/.bin/uglifyjs \
		elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/app/*.js \
		elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/app/**/*.js \
		elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/ipsuite/*.js \
		--preamble "// (c) 2013,2014 Elmyra UG - All rights reserved" \
		--mangle --compress \
		--source-map elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/app.min.map \
		--source-map-url /static/js/app.min.map \
		> elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/app.min.js

	# configuration
	node_modules/.bin/uglifyjs \
		elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/config.js \
		--preamble "// (c) 2013,2014 Elmyra UG - All rights reserved" \
		--mangle --compress \
		> elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/config.min.js

	# url cleaner
	node_modules/.bin/uglifyjs \
		elmyra.ip.access.epo/elmyra/ip/access/epo/templates/urlcleaner.js \
		--mangle --compress \
		> elmyra.ip.access.epo/elmyra/ip/access/epo/templates/urlcleaner.min.js

	git commit -uno \
		elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/app.min.{js,map} \
		elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/config.min.js \
		elmyra.ip.access.epo/elmyra/ip/access/epo/templates/urlcleaner.min.js \
		--message='release: minify javascript resources'

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

bumpversion:
	bumpversion $(bump)

push:
	git push && git push --tags

release:
	$(MAKE) js
	$(MAKE) bumpversion bump=$(bump)
	$(MAKE) push
	$(MAKE) package-and-install
