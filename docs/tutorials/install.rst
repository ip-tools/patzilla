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

    cd patzilla.access.epo
    python setup.py develop


Production
----------
::

    pip install --allow-external which --allow-external fanstatic --allow-external setuptools --allow-unverified setuptools --allow-unverified which --upgrade fanstatic==1.0a2


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
    pserve patzilla.access.epo/development.ini --reload


Run tests
=========
::

    make test-setup
    make test

    make test options='--where patzilla.access.ftpro'
    make test options='--where patzilla.util.numbers.test.test_normalize'


Release
=======
Cut a new release::

    make release bump=minor         # patch,minor,major

Deploy to server::

    make install target=develop     # develop,staging,prod

