.. include:: ../resources.rst

.. _install-development:
.. _install-sandbox:
.. _run-patzilla-from-source:

####################
Sandbox installation
####################

About
=====

If you plan to contribute to PatZilla, this is the way to go!

This section of the documentation will guide you through the process of setting
up a development sandbox in order to get hands on with the source code.



Prerequisites
=============

Running PatZilla from source has the same baseline requirements as the basic
setup, so please follow :ref:`install-minimum-requirements` for satisfying
these dependencies beforehand.

For building PatZilla from source, more programs are needed.


Acquire sources
===============

Get the source code by using ``git``::

    git clone https://github.com/ip-tools/patzilla
    cd patzilla


Setup
=====

Python sandbox
--------------
Create a Python virtual environment holding the sandbox installation::

    apt install python-virtualenv
    make setup


.. _build-javascript-bundles:

JavaScript sandbox
------------------

Create a Node.js environment using specific software versions and install the
application's dependencies::

    # Yes it's outdated but c'est la vie.
    export NODEJS_VERSION=11.15.0
    export NPM_VERSION=6.14.15
    export YARN_VERSION=1.22.18
    source /dev/stdin <<<"$(curl -s https://raw.githubusercontent.com/cicerops/supernode/main/supernode)"

    # Install all module dependencies.
    yarn install

Launch bundler in development mode, reloading files when changed on disk::

    make jswatch


Configure
=========
Use a configuration template::

    cp patzilla/config/development.ini.tpl patzilla/config/development-local.ini

Then, edit ``patzilla/config/development-local.ini`` according to your needs.


Run instance
============

Application
-----------
Start database::

    make mongodb

Launch application in development mode, reloading files when changed on disk::

    make pywatch

Then, navigate to http://localhost:6543/navigator/ in your browser.


Nginx
-----
::

    make nginx


Go to http://localhost:6544


Software tests
==============

Run all tests::

    make test


Run tests, advanced
===================

Run test suite with coverage reporting::

    make test-coverage

In order to improve performance, the test harness employs the same resource
caching subsystem as the main application. By default, it will be enabled.
To disable that, use the ``--app-cache-backend=memory`` option, e.g. like::

    make test-coverage options="--app-cache-backend=memory"

Run selected tests::

    make test options='-k patzilla/access/ificlaims'
    make test options='-k patzilla/access/depatech'
    make test options='-k test_normalize'

Or run ``pytest`` directly, like::

    pytest -vvv --cov -k normalize

In order to skip tests making upstream network requests, or which are otherwise
slow, use::

    pytest -vvv -m "not slow"

.. note::

    Please note that by default, test cases needing access to upstream data
    sources will be skipped. In order to run them, you will have to properly
    configure respective access credentials by setting corresponding
    environment variables before invoking the test suite. The documentation
    about the :ref:`cli` shows how to do that.
