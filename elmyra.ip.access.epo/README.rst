elmyra.ip.access.epo README
===========================

Getting Started
---------------

- cd <directory containing this file>

- $venv/bin/python setup.py develop

- $venv/bin/pserve development.ini
- pserve development.ini --reload


Tests
-----
::

    make test

    make test options='--where elmyra.ip.access.ftpro'
    make test options='--where elmyra.ip.util.numbers.test.test_normalize'
