.. _install-development:

############################
Install IP Navigator sandbox
############################


.. _run-ip-navigator-from-source:

************
From sources
************

If you plan on contributing, this is the way to go!

This will install every necessary packages to
run a sandbox instance, run the tests,
build the documentation, build the packages, etc.

Setup
=====
Repository::

    git clone https://github.com/ip-tools/ip-navigator.git

Sandbox::

    virtualenv-2.7 --no-site-packages .venv27
    source .venv27/bin/activate

Prerequisites::

    pip install --upgrade pip
    pip install cryptography
    pip install --allow-all-external 'https://github.com/trentm/which/tarball/master#egg=which'
    pip install --allow-all-external js.*/

Application::

    python setup.py develop


::



Configure
=========
::

    cp patzilla/config/development.ini.tpl patzilla/config/development.ini
    # edit patzilla/config/development.ini


Run instance
============
Start database::

    make mongodb-start

Start web server::

    source .venv27/bin/activate
    pserve patzilla/config/development.ini --reload


Run tests
=========
::

    pip install -e .[test]
    make test

    make test options='--where patzilla.access.ificlaims'
    make test options='--where patzilla.access.depatech'
    make test options='--where patzilla.util.numbers.test.test_normalize'

