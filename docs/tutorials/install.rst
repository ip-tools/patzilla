.. _install:

####################
Install IP Navigator
####################


.. _run-ip-navigator-from-source:

************
From sources
************

If you plan on contributing, this is the way to go!

This will install every necessary packages to run the tests,
build the documentation, build packages, etc.

Setup
=====
Sandbox::

    virtualenv-2.7 --no-site-packages .venv27
    source .venv27/bin/activate
    pip install --upgrade pip

Prerequisites::

    pip install cryptography
    pip install 'https://github.com/trentm/which/tarball/master#egg=which'
    pip install --allow-all-external js.*/

Application::

    cd elmyra.ip.access.epo
    python setup.py develop


Production
----------
::

    pip install --allow-external which --allow-external fanstatic --allow-external setuptools --allow-unverified setuptools --allow-unverified which --upgrade fanstatic==1.0a2


Configure
=========
::

    cp elmyra.ip.access.epo/development.ini.tpl elmyra.ip.access.epo/development.ini
    # edit elmyra.ip.access.epo/development.ini


Run instance
============
Start database::

    make mongodb-start

Start web server::

    source .venv27/bin/activate
    pserve elmyra.ip.access.epo/development.ini --reload


Run tests
=========
::

    make test

    make test options='--where elmyra.ip.access.ftpro'
    make test options='--where elmyra.ip.util.numbers.test.test_normalize'


Release
=======
::

    make release bump=minor

