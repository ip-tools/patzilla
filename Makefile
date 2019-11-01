#VERSION := $(shell cat patzilla/version.py | awk '{ print $$3 }' | tr -d "'")
#$(error VERSION=$(VERSION))

$(eval venvpath     := .venv2)
$(eval pip          := $(venvpath)/bin/pip)
$(eval twine        := $(venvpath)/bin/twine)
$(eval python       := $(venvpath)/bin/python)
$(eval bumpversion  := $(venvpath)/bin/bumpversion)
$(eval fab          := $(venvpath)/bin/fab)

$(eval nodeenvpath  := .nodeenv11)
$(eval npx          := $(nodeenvpath)/bin/npx)

js:
	# url cleaner
	npx uglifyjs \
		patzilla/navigator/templates/urlcleaner.js \
		--mangle --compress \
		> patzilla/navigator/templates/urlcleaner.min.js

	-git diff --quiet --exit-code || git commit \
		patzilla/navigator/templates/urlcleaner.min.js \
		-uno --untracked-files=no \
		--message='release: minify javascript resources'

js-release: js
	@echo ------------------------------------------
	@echo Bundling Javascript/CSS resources.
	@echo This might take a while, please stay patient...
	@echo ------------------------------------------
	npx yarn release

sdist:
	$(python) setup.py sdist

upload-legacy:
	rsync -auv ./dist/PatZilla-* ${PATZILLA_HOST}:~/install/patzilla/

upload-pypi:
	@echo ------------------------------------------
	@echo Uploading Python package to PyPI.
	@echo This might take a while, please stay patient...
	@echo ------------------------------------------

	$(eval filename := "dist/patzilla-*.tar.gz")
	@echo Uploading '$(filename)' to PyPI
	$(twine) upload --skip-existing $(filename)

# $(eval version  := $(shell cat setup.py | grep "version='" | sed -rn "s/.*version='(.+?)'.*/\1/p"))
# $(eval filename := "dist/patzilla-$(version).tar.gz")


setup-test:
	$(pip) install -e .[test]

setup-deployment:
	$(pip) install --requirement requirements-deploy.txt

setup-release:
	$(pip) install --requirement requirements-release.txt

install: setup-deployment
	@# make install target=patoffice version=0.29.0
	$(fab) install:target=$(target),version=$(version)

#package-and-install: sdist upload install

bumpversion:
	$(bumpversion) $(bump)

push:
	git push && git push --tags

#release:
#	$(MAKE) js && $(MAKE) bumpversion bump=$(bump) && $(MAKE) push

release: setup-release js-release bumpversion push sdist upload-pypi

install-nginx-auth:
	fab upload_nginx_auth

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
		--exclude-dir=patzilla/access/sip \
		--ignore-files=setup.py \
		--ignore-files=fabfile.py \
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

mongodb-sip-export:
	mkdir -p var/tmp/mongodb
	mongoexport --db patzilla_development --collection sip_country > var/tmp/mongodb/sip_country.mongodb
	mongoexport --db patzilla_development --collection sip_ipc_class > var/tmp/mongodb/sip_ipc_class.mongodb
	mongoexport --db patzilla_development --collection sip_cpc_class > var/tmp/mongodb/sip_cpc_class.mongodb

mongodb-sip-import:
	mongoimport --db patzilla_development --collection sip_country < var/tmp/mongodb/sip_country.mongodb
	mongoimport --db patzilla_development --collection sip_ipc_class < var/tmp/mongodb/sip_ipc_class.mongodb
	mongoimport --db patzilla_development --collection sip_cpc_class < var/tmp/mongodb/sip_cpc_class.mongodb

sloccount:
	sloccount patzilla
	sloccount patzilla-ui/{access,common,lib,navigator}

genlicenses:
	$(pip) install third-party-license-file-generator
	$(pip) freeze > /tmp/requirements.txt
	$(python) -m third_party_license_file_generator --requirements-path /tmp/requirements.txt --python-path $(python) --output-file licenses-backend.txt

clear-cache:
	mongo beaker --eval 'db.dropDatabase();'

docs-virtualenv:
	$(eval venvpath := ".venv_sphinx")
	@test -e $(venvpath)/bin/python || `command -v virtualenv` --python=`command -v python` --no-site-packages $(venvpath)
	@$(venvpath)/bin/pip --quiet install --requirement requirements-docs.txt

docs-html: docs-virtualenv
	$(eval venvpath := ".venv_sphinx")
	touch docs/index.rst
	export SPHINXBUILD="`pwd`/$(venvpath)/bin/sphinx-build"; cd docs; make html

pdf-EP666666:
	/usr/local/bin/wkhtmltopdf \
		--no-stop-slow-scripts --debug-javascript \
		--print-media-type \
		--page-size A4 --orientation portrait --viewport-size 1024 \
		'http://localhost:6543/navigator?query=pn%3DEP666666&mode=print' var/tmp/patzilla-EP666666.pdf
	# --zoom 0.8

pdf-mammut:
	/usr/local/bin/wkhtmltopdf \
		--no-stop-slow-scripts \
		--print-media-type \
		--page-size A4 --orientation portrait --viewport-size 1024 \
		'http://localhost:6543/navigator?query=pa=mammut&mode=print' var/tmp/patzilla-mammut.pdf

	#	--debug-javascript \


# ==========================================
#           ptrace.getkotori.org
# ==========================================

# Don't commit media assets (screenshots, etc.) to the repository.
# Instead, upload them to https://ptrace.getkotori.org/
ptrace_target := www-data@ptrace.ip-tools.org:/srv/www/organizations/ip-tools/ptrace.ip-tools.org/htdocs/
ptrace_http   := https://ptrace.ip-tools.org/
ptrace: check-ptrace-options
	$(eval prefix := $(shell gdate --iso-8601))
	$(eval name   := $(shell basename $(source)))
	$(eval id     := $(prefix)_$(name))

	@# debugging
	@#echo "name: $(name)"
	@#echo "id:   $(id)"

	@scp '$(source)' '$(ptrace_target)$(id)'

	$(eval url    := $(ptrace_http)$(id))
	@echo "Access URL: $(url)"

check-ptrace-options:
	@if test "$(source)" = ""; then \
		echo "ERROR: 'source' not set"; \
		exit 1; \
	fi
