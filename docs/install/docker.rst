.. include:: ../resources.rst

.. _install-docker:

########################
Installation with Docker
########################


*****
About
*****

This part of the documentation covers the building of Docker images
and running PatZilla within a Docker container.

The provided ``Dockerfile`` is meant to build Docker images for official
releases of PatZilla. The ``patzilla`` package will be installed from
`PatZilla on PyPI`_, so this is not meant for development purposes.


********
Synopsis
********

Acquire sources::

    git clone https://github.com/ip-tools/patzilla
    cd patzilla/docker

Build Docker image::

    docker build --tag local/patzilla .

Test drive::

    docker run --rm -it local/patzilla patzilla --version

Generate PatZilla configuration file::

    docker run --rm -it local/patzilla patzilla make-config production --flavor=docker-compose > patzilla.ini

Please edit the newly created ``patzilla.ini`` according to your needs before
starting PatZilla. Specifically, you will need to set credentials for the OPS
service. More details can be found at :ref:`EPO OPS system-wide configuration
<epo-ops-system-wide>`.

After configuring PatZilla, the easiest way to invoke an instance is by using
the provided Docker Compose configuration::

    docker compose up

Then, navigate to http://localhost:6543/navigator/ in your browser and enjoy
your research.


*****************
Starting manually
*****************

If you don't intend to use the provided Docker Compose configuration, this is
an appropriate snippet that should get you started::

    docker run --rm -it \
        --volume=$PWD/patzilla.ini:/etc/patzilla.ini:ro --publish=6543:6543 \
        local/patzilla \
        pserve /etc/patzilla.ini
