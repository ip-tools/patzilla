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

Distribute & Pip
================
The recommended way to install PatZilla is with `pip <http://www.pip-installer.org/>`_::

    $ pip install https://github.com/ip-tools/ip-navigator/tarball/master#egg=PatZilla

Future reference::

    $ pip install PatZilla

.. note::

    This will currently only install the Python sdist core package without the
    Javascript bundles required for running the user interface. YMMV.
    See also :ref:`install-development` for building the Javascript bundles.


*******************
Download the Source
*******************

You can also install PatZilla from source. The latest release (|version|) is available from GitHub.

* tarball_
* zipball_

Once you have a copy of the source, you can embed it in your Python package, or install it into your site-packages easily. ::

    $ python setup.py install

.. _tarball: https://github.com/ip-tools/ip-navigator/tarball/master
.. _zipball: https://github.com/ip-tools/ip-navigator/zipball/master


**********
Contribute
**********
For contributing to PatZilla, you might want to consider cloning the git repository
and prepare the software for being run in a sandbox environment::

    git clone https://github.com/ip-tools/ip-navigator.git

See also :ref:`install-development`.


****************
Production setup
****************
For getting an idea about how to install PatZilla in a production environment,
please refer to :ref:`install-production`.
