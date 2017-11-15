.. include:: ../resources.rst

.. _setup-yarn:

##########
Setup Yarn
##########


************
Introduction
************
The Yarn_ package manager is based on the Javascript runtime `Node.js`_.

This documentation describes how to setup the required packages
on Debian GNU/Linux system and derivates like Ubuntu.

.. seealso:: https://nodejs.org/en/download/package-manager/#debian-and-ubuntu-based-linux-distributions


*****
Setup
*****
::

    # Add Node.js package repository
    curl -sL https://deb.nodesource.com/setup_6.x | bash -

    # Install Node.js
    apt install --yes nodejs

    # Install Yarn package manager (globally)
    npm install --global yarn

