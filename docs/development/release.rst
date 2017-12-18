.. include:: ../resources.rst

.. _release:

#######
Release
#######

Prerequisites
=============
Run once to prepare the sandbox environment for release tasks::

    pip install --requirement requirements-release.txt

Cut a new release
=================
This will package the javascript bundles, bump the version number in various files,
tag the repository, push to git origin, build a Python sdist package and upload it
to PyPI. Some configuration steps might be required to achieve this. YMMV.

Use from inside repository, with virtualenv activated.
::

    # Possible increments: major, minor, patch
    make release bump=minor

