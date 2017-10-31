.. _running:

#######
Running
#######
This part of the documentation covers the ways to run PatZilla.
Please read this section carefully.

***********
Basic setup
***********

Running MongoDB
===============
If the MongoDB database already is running on your machine, you can skip this step.

You can either install and run it system-wide on Debian GNU/Linux::

    apt install mongodb-clients mongodb-server

... or run it ad-hoc in the current working directory::

    mkdir -p ./var/lib/mongodb
    mongod --dbpath=./var/lib/mongodb --smallfiles


Running PatZilla
================
Start the web server using the :ref:`configuration` file created before::

    pserve /path/to/patzilla.ini

Then, open http://localhost:6543/navigator/

Have fun!


****************
Production setup
****************
For getting an idea about how to install PatZilla in a production environment,
please refer to :ref:`install-production`.

