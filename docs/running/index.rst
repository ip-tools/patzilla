.. _running:

#######
Running
#######
This part of the documentation covers the ways to run PatZilla.
Please read this section carefully.

Running MongoDB
===============
If the MongoDB database already is running on your machine, you can skip this step.

You can either install and run it system-wide on Debian GNU/Linux::

    apt install mongodb-clients mongodb-server

... or run it ad-hoc in the current working directory::

    mkdir -p ./var/lib/mongodb
    mongod --dbpath=./var/lib/mongodb


Running PatZilla
================
Start the web server using the :ref:`configuration` file created before::

    patzilla serve /path/to/patzilla.ini

Then, open http://localhost:6543/navigator/

Have fun!

The web application is an ASGI application based on FastAPI, served by uvicorn.
Host, port, and the number of worker threads are configured within the
``[server:main]`` section of the configuration file, and can be overridden on the
command line, see ``patzilla serve --help``.

When running behind a reverse proxy, the ``filter-with = prefix-middleware`` setting
within the ``[app:main]`` section evaluates the ``X-Forwarded-Proto`` and ``X-Forwarded-For``
headers it submits, and ``prefix = /path`` serves the application below a path prefix.

Alternatively, run the application using any ASGI server, for example::

    export PATZILLA_CONFIG=/path/to/patzilla.ini
    uvicorn --factory patzilla.web.app:app_factory --host=0.0.0.0 --port=6543


.. toctree::
    :maxdepth: 1
    :hidden:

    cli
