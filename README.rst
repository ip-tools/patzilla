=================
IPSUITE NAVIGATOR
=================

test

Sandbox
=======

::

    virtualenv-2.7 --no-site-packages .venv27
    . .venv27/bin/activate

::

    cd elmyra.ip.access.epo
    python setup.py develop
    pserve --reload development.ini



::

    pip install --allow-external which --allow-external fanstatic --allow-external setuptools --allow-unverified setuptools --allow-unverified which --upgrade fanstatic==1.0a2
    pip install --verbose ~/install/ops-chooser/js.*


Release
=======
::

    make release bump=minor
