#VERSION := $(shell cat patzilla/version.py | awk '{ print $$3 }' | tr -d "'")
#$(error VERSION=$(VERSION))

js:
	# url cleaner
	node_modules/.bin/uglifyjs \
		patzilla/navigator/templates/urlcleaner.js \
		--mangle --compress \
		> patzilla/navigator/templates/urlcleaner.min.js

	-git diff --quiet --exit-code || git commit \
		Makefile \
		patzilla/navigator/templates/urlcleaner.min.js \
		-uno --untracked-files=no \
		--message='release: minify javascript resources'

js-release: js
	@echo Bundling Javascript/CSS resources
	yarn run release

sdist:
	python setup.py sdist

upload:
	rsync -auv ./dist/PatZilla-* root@almera.elmyra.de:/root/install/PatZilla/

setup-test:
	source .venv27/bin/activate; pip install -e .[test]

setup-maintenance:
	source .venv27/bin/activate; pip install -e .[deployment]

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

release: js-release bumpversion push sdist upload

install-nginx-auth:
	rsync -azuv nginx-auth/* root@almera.elmyra.de:/opt/elmyra/patentsearch/nginx-auth/
	# TODO: fab upload_nginx_auth

test:
	@python runtests.py          \
		$(options)              \
		--all-modules           \
		--traverse-namespace    \
		--with-doctest          \
		--doctest-tests         \
		--doctest-extension=rst \
		--doctest-options=doctestencoding=utf-8,+ELLIPSIS,+NORMALIZE_WHITESPACE,+REPORT_UDIFF \
		--exclude-dir=patzilla/navigator/static \
		--exclude-dir=patzilla/navigator/templates \
		--exclude-dir=patzilla/util/database \
		--exclude-dir=patzilla/util/web/uwsgi \
		--nocapture \
		--nologcapture \
		--verbose

# +REPORT_ONLY_FIRST_FAILURE


test-cover:
	$(MAKE) test options="--with-coverage"

nginx_path=/Users/amo/dev/celeraone/sources/c1-ocb-integrator/rem_rp/parts/openresty
nginx-start:
	@$(nginx_path)/nginx/sbin/nginx -p $(nginx_path)/nginx -c `pwd`/nginx-auth/etc/nginx.conf -g "daemon off; error_log /dev/stdout info;"

mongodb-start:
	mkdir -p ./var/lib/mongodb
	mongod --dbpath=./var/lib/mongodb --smallfiles

mongodb-ftpro-export:
	mkdir -p var/tmp/mongodb
	mongoexport --db ipsuite_development --collection ftpro_country > var/tmp/mongodb/ftpro_country.mongodb
	mongoexport --db ipsuite_development --collection ftpro_ipc_class > var/tmp/mongodb/ftpro_ipc_class.mongodb

mongodb-ftpro-import:
	mongoimport --db ipsuite_development --collection ftpro_country < var/tmp/mongodb/ftpro_country.mongodb
	mongoimport --db ipsuite_development --collection ftpro_ipc_class < var/tmp/mongodb/ftpro_ipc_class.mongodb

sloccount:
	sloccount patzilla
	sloccount --addlang js patzilla-ui/{access,common,lib,navigator}

clear-cache:
	mongo beaker --eval 'db.dropDatabase();'

pdf-EP666666:
	/usr/local/bin/wkhtmltopdf \
		--no-stop-slow-scripts --debug-javascript \
		--print-media-type \
		--page-size A4 --orientation portrait --viewport-size 1024 \
		'http://localhost:6543/navigator?query=pn%3DEP666666&mode=print' var/tmp/ipsuite-EP666666.pdf
	# --zoom 0.8

pdf-mammut:
	/usr/local/bin/wkhtmltopdf \
		--no-stop-slow-scripts \
		--print-media-type \
		--page-size A4 --orientation portrait --viewport-size 1024 \
		'http://localhost:6543/navigator?query=pa=mammut&mode=print' var/tmp/ipsuite-mammut.pdf

	#	--debug-javascript \
