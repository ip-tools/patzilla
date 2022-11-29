.. include:: ../resources.rst

.. _install-development:
.. _install-sandbox:

#############
Sandbox setup
#############


.. _run-patzilla-from-source:

************
From sources
************

If you plan on contributing, this is the way to go!

This will install every necessary packages to
run a sandbox instance, run the tests,
build the documentation, build the packages, etc.


Satisfy prerequisites
=====================
Setting up PatZilla from source has the same requirements as with the basic setup,
so please follow :ref:`install-minimum-requirements` for satisfying these.

Additionally, PatZilla requires the Yarn_ package manager for setting up the
environment used for bundling the Javascript packages. Please read how to :ref:`setup-yarn`.


Get the Source
==============

Using git
---------
Get the source code::

    git clone https://github.com/ip-tools/patzilla.git
    cd patzilla


Using download
--------------
You can also install PatZilla from source. The latest release (|version|) is available from GitHub.

* tarball_
* zipball_

Once you have a copy of the source, you can embed it in your Python package, or install it into your site-packages easily::

    $ python setup.py install

.. _tarball: https://github.com/ip-tools/patzilla/tarball/main
.. _zipball: https://github.com/ip-tools/patzilla/zipball/main

.. note::

    Please note that both variants do **not** contain the bundled Javascript packages,
    so the user interface will not work out of the box before running webpack on it.
    See also :ref:`build-javascript-bundles` for building the Javascript bundles.


Setup
=====

Python sandbox
--------------
Create a virtual environment holding the sandbox installation::

    apt install python-virtualenv
    virtualenv --python=python2 .venv2
    source .venv2/bin/activate

Install/upgrade some prerequisites::

    pip install --upgrade pip

Fetch module dependencies and install application::

    pip install --editable=.[test]


.. _build-javascript-bundles:

Javascript sandbox
------------------

Create a Node.js environment::

    export NODEJS_VERSION=11.15.0
    export NPM_VERSION=6.14.15
    export YARN_VERSION=1.22.18

    source /dev/stdin <<<"$(curl -s https://raw.githubusercontent.com/cicerops/supernode/main/supernode)"

Fetch all module dependencies::

    yarn install

Bundle application and all required assets::

    yarn build

Rebundle on file change::

    yarn watch


Configure
=========
Use a configuration template::

    cp patzilla/config/development.ini.tpl patzilla/config/development-local.ini

Then, edit ``patzilla/config/development-local.ini`` according to your needs.


Run instance
============

Application container
---------------------
Start database::

    make mongodb-start

Start web server::

    source .venv2/bin/activate
    export HUPPER_DEFAULT_MONITOR=hupper.watchdog.WatchdogFileMonitor
    pserve --reload patzilla/config/development-local.ini

Then, navigate to http://localhost:6543/navigator/ in your browser.


Nginx
-----
::

    make nginx-start


Go to http://localhost:6544


Run tests
=========
Setup::

    make setup-test

Run all tests::

    make test

Run selected test suite::

    make test options='-k patzilla/access/ificlaims'
    make test options='-k patzilla/access/depatech'
    make test options='-k test_normalize'

Run test suite with coverage reporting::

    make test-coverage


***************
Troubleshooting
***************

Missing gmp on macOS
====================
When encountering error like::

    src/_fastmath.c:36:11: fatal error: 'gmp.h' file not found

make sure you have gmp installed::

    brew install gmp

and that it's available to your environment::

    export LDFLAGS=-L/usr/local/opt/gmp/lib
    export CPPFLAGS=-I/usr/local/opt/gmp/include
