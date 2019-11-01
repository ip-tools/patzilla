.. include:: ../resources.rst

.. _install:

############
Installation
############
This part of the documentation covers the installation of PatZilla.
The first step to using any software package is getting it properly installed.
Please read this section carefully.

After successfully installing the software, you might want to
follow up with its :ref:`configuration`.


.. _installing:

*******************
Installing PatZilla
*******************
The following documentation is for Debian GNU/Linux or derivates.
We appreciate contributions in form of walkthroughs about how to
install PatZilla on other distributions and platforms.


.. _install-minimum-requirements:

Minimum prerequisites
=====================
Foundation: MongoDB_, PDFtk_ and ImageMagick_::

    # Debian Linux
    apt install mongodb-clients mongodb-server pdftk imagemagick unoconv

    # Mac OS X
    # https://github.com/turforlag/homebrew-cervezas
    # https://github.com/spl/homebrew-pdftk (deprecated)
    brew tap turforlag/homebrew-cervezas
    brew install mongodb pdftk imagemagick unoconv

Python stack::

    apt install python2.7 python2.7-dev python-virtualenv build-essential libxml2-dev libxslt1-dev zlib1g-dev

.. note::

    As PatZilla is currently being shipped as Python sdist package only, we need to have
    some build tools and header files installed on the system before running the installation.
    This will change as soon as Debian or other distribution packages will be available.


Distribute & Pip
================
The recommended way to install PatZilla is with `pip <http://www.pip-installer.org/>`_::

    pip install patzilla

You might want to verify the installation actually worked::

    patzilla --version
    patzilla 0.142.5

If you need an older version, please visit
the `release history <https://pypi.org/project/patzilla/#history>`_
of `PatZilla on PyPI <https://pypi.org/project/patzilla/>`_.


.. tip::

    As PatZilla pulls in a significant amount of Python package dependencies,
    you might want to consider installing the software isolated from the system Python
    by using "virtualenv" before proceeding with ``pip install patzilla``::

        virtualenv --python=python2 .venv2
        source .venv2/bin/activate

