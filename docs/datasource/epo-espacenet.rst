.. _datasource-epo-espacenet:

###################
About EPO Espacenet
###################
PatZilla uses the Espacenet system provided by the European Patent Office (EPO)
to acquire claims and description full-text data that is not available via EPO/OPS.
See also https://worldwide.espacenet.com/ for more information about this service.

.. contents::
   :local:
   :depth: 1

----

.. _epo-espacenet-intro:

************
Introduction
************

With its worldwide coverage and search features, Espacenet offers free access to
information about inventions and technical developments from 1782 to today.

Espacenet is accessible to beginners and experts and is updated daily. It contains
data on more than 150 million patent documents from around the world. Supporting
information can help you understand whether a patent has been granted and if it
is still in force.

You might also want to have a look at some information provided by the EPO:

- `FAQ on Espacenet <https://www.epo.org/en/service-support/faq>`_
- `Fair use charter <https://www.epo.org/en/service-support/ordering/fair-use>`_
- `Coverage, codes and statistics <https://www.epo.org/en/searching-for-patents/data/coverage>`_


*****
Setup
*****

The configuration section name is ``[datasource:espacenet]``::

    [datasource:espacenet]
    fulltext_enabled = true
    fulltext_countries = DE, US

Also enable ``espacenet`` within ``[ip_navigator]``, e.g.::

    [ip_navigator]
    datasources = ops, depatisnet, espacenet

Install MS Edge embedded::

    playwright install msedge
