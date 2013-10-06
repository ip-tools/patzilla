
::

    virtualenv-2.7 --no-site-packages .venv27
    . .venv27/bin/activate

::

    cd elmyra.ip.access.epo
    python setup.py develop
    pserve --reload development.ini
