.. include:: ../resources.rst

.. _install-linux-macos:

##############################
Installation on Linux or macOS
##############################

*****
About
*****

The following documentation outlines the installation of PatZilla on Debian
GNU/Linux or derivates, and macOS.

We appreciate contributions in form of walkthroughs about how to
install PatZilla on other distributions and platforms.


*******************
Installing PatZilla
*******************

.. _install-minimum-requirements:

Minimum prerequisites
=====================
Foundation: MongoDB_, PDFtk_, pdfimages_ and ImageMagick_::

    # Debian Linux
    apt install mongodb-clients mongodb-server pdftk poppler-utils imagemagick unoconv

    # Mac OS X
    # https://github.com/turforlag/homebrew-cervezas
    # https://github.com/spl/homebrew-pdftk (deprecated)
    brew tap turforlag/homebrew-cervezas
    brew install mongodb pdftk poppler imagemagick unoconv

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
