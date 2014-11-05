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

	git diff --quiet --exit-code || git commit \
		Makefile \
		elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/app.min.{js,map} \
		elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/config.min.js \
		elmyra.ip.access.epo/elmyra/ip/access/epo/templates/urlcleaner.min.js \
		-uno --untracked-files=no \
		--message='release: minify javascript resources'

sdist:
	cd elmyra.ip.access.epo; python setup.py sdist
	cd js.jquery_shorten; python setup.py sdist
	cd js.purl; python setup.py sdist
	cd js.underscore_string; python setup.py sdist

upload:
	rsync -auv */dist/elmyra.ip.access.epo-* root@almera.elmyra.de:/root/install/ops-chooser/

setup-maintenance:
	source .venv27/bin/activate; pip install cuisine

install:
	@# make install target=patoffice version=0.29.0
	source .venv27/bin/activate; fab install:target=$(target),version=$(version)

#package-and-install: sdist upload install

bumpversion:
	bumpversion $(bump)

push:
	git push && git push --tags

#release:
#	$(MAKE) js && $(MAKE) bumpversion bump=$(bump) && $(MAKE) push

release: js bumpversion push sdist upload

install-nginx-auth:
	rsync -azuv nginx-auth/* root@almera.elmyra.de:/opt/elmyra/patentsearch/nginx-auth/

test:
	@python runtests.py          \
		--all-modules           \
		--traverse-namespace    \
		--with-doctest          \
		--doctest-tests         \
		--doctest-extension=rst \
		--where=elmyra.ip.access.epo \
		--exclude-dir=elmyra/ip/util/database \
		--exclude-dir=elmyra/ip/access/epo/static \
		--exclude-dir=elmyra/ip/access/epo/templates \
		--doctest-options=doctestencoding=utf-8 \
		$(options)

test-cover:
	$(MAKE) test options="--with-coverage"

test-setup:
	pip install nose==1.3.3 nose-exclude==0.2.0 nose2-cov==1.0a4

nginx_path=/Users/amo/dev/celeraone/sources/c1-ocb-integrator/rem_rp/parts/openresty
nginx-start:
	@$(nginx_path)/nginx/sbin/nginx -p $(nginx_path)/nginx -c `pwd`/nginx-auth/etc/nginx.conf -g "daemon off; error_log /dev/stdout info;"

mongodb-ftpro-export:
	mkdir -p var/tmp/mongodb
	mongoexport --db ipsuite_development --collection ftpro_country > var/tmp/mongodb/ftpro_country.mongodb
	mongoexport --db ipsuite_development --collection ftpro_ipc_class > var/tmp/mongodb/ftpro_ipc_class.mongodb

mongodb-ftpro-import:
	mongoimport --db ipsuite_development --collection ftpro_country < var/tmp/mongodb/ftpro_country.mongodb
	mongoimport --db ipsuite_development --collection ftpro_ipc_class < var/tmp/mongodb/ftpro_ipc_class.mongodb

sloccount:
	sloccount elmyra.ip.access.epo
	sloccount --addlang js elmyra.ip.access.epo/elmyra/ip/access/epo/static/js/app
