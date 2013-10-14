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
