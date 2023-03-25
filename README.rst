################################################
PatZilla: Patent information research for humans
################################################


*****
About
*****

PatZilla is a modular patent information research platform and data integration
toolkit. It provides access to multiple data sources, like the OPS service from
EPO, and other professional fulltext patent databases.

The system features an efficient user interface for convenient data exploration
in its standalone version. Its software components and interfaces can also be
used to build different kinds of vendor solutions.

Currently, PatZilla powers `Europatent PATOffice Navigator`_ and
`Serviva PATselect 4.0`_.


******
Status
******

- **Project status**:

  .. image:: https://img.shields.io/pypi/status/patzilla.svg
        :target: https://pypi.org/project/patzilla/
        :alt: Project status (alpha, beta, stable)

  .. image:: https://img.shields.io/badge/Python-2.7-green.svg
        :target: https://pypi.org/project/patzilla/
        :alt: Supported Python versions

  .. image:: https://img.shields.io/badge/MongoDB-2.x%20--%205.x-blue.svg
        :target: https://github.com/mongodb/mongo
        :alt: Supported MongoDB versions

  .. image:: https://img.shields.io/pypi/v/patzilla.svg
        :target: https://pypi.org/project/patzilla/
        :alt: Package version on PyPI

  .. image:: https://img.shields.io/pypi/l/patzilla.svg
        :target: https://pypi.org/project/patzilla/
        :alt: Project license

  .. image:: https://pepy.tech/badge/patzilla/month
        :target: https://pepy.tech/project/patzilla
        :alt: PyPI downloads per month

- **Code status**:

  .. image:: https://github.com/ip-tools/patzilla/workflows/Tests/badge.svg
        :target: https://github.com/ip-tools/patzilla/actions?workflow=Tests
        :alt: CI outcome

  .. image:: https://codecov.io/gh/ip-tools/patzilla/branch/main/graph/badge.svg
        :target: https://codecov.io/gh/ip-tools/patzilla
        :alt: Test suite code coverage


********
Features
********

- Multiple data source APIs. Connect to different patent search services and APIs for
  the acquisition of bibliographic-, fulltext-, image-, and pdf-data.

- Graphical user interface. Based on contemporary web technologies and responsive design, it works on multiple devices.
  Use it on PCs, tablets, smartphone devices or as a multi-screen solution. The clear and well-arranged
  design and layout permits efficient screening of large numbers of patent documents.

- Command line interface. Functionality for acquiring and processing raw patent data
  is conveniently available on the command line using the ``patzilla`` command.
  It can be used to run ad hoc inquiries to the system and the upstream data sources
  and to build custom scripted solutions and simple automations.

- HTTP API interface. Through the extensive REST API, all functionality is easily
  available to 3rd-party systems. Deep integration has no limits.

- Dossier management. Manage different collections of patent documents and apply ratings and comments.

- Sharing. Well-designed collaboration features allow efficient sharing of information with your
  colleagues and partners, even across the boundaries of in-house systems.

- Multi-tenancy. The software can operate on behalf of different vendors with individual custom branding.


***************
User interfaces
***************

Graphical user interface
========================

A picture says a thousand words.

.. image:: https://raw.githubusercontent.com/ip-tools/patzilla/main/patzilla-screenshot.png
    :alt: PatZilla
    :target: https://github.com/ip-tools/patzilla

Command line interface
======================

The CLI interface offers access to the machinery of PatZilla on your fingertips.

Note that most of the following commands will need appropriate configuration of
corresponding access credentials. For more information, please follow up reading
the `cli documentation`_.

Examples using EPO/OPS::

    # Display usage information of EPO/OPS in JSON format.
    patzilla ops usage

    # Submit search query to EPO/OPS, within "title" and "abstract" texts.
    patzilla ops search "txt=(wind or solar) and energy"

    # Inquire information about pages and images of full document.
    patzilla ops image-info --document EP0666666B1

    # Acquire first page of patent document in PDF format.
    patzilla ops image --document EP0666666B1 --page 1 > EP0666666B1-page1.pdf

    # Acquire first drawing of patent document in PDF format.
    patzilla ops image --document EP0666666B1 --page 1 --kind FullDocumentDrawing > EP0666666B1-drawing1.pdf

Example using IFI CLAIMS::

    patzilla ificlaims search "text:(wind or solar) and energy"


*****
Demos
*****

- The `search demo`_ will run a fixed query on EPO/OPS and display the results.
  ::

      txt=(SS7 or (telecommunication or communication or comunicación) or (mobile or Mobilfunknetz) or (network or (security or Sicherung))) and
      pa=(mobil or kommunikation) and
      cl=(H04W12/12 or H04L63/0281 or H04L63/0414)
      not pn=(CN or CA or JP)

  You will be able to step through result pages and display fulltext- and family-information,
  but running custom queries will be disabled.

- The `numberlist demo`_ will display the patent documents DE102011075997A1, DE102011076020A1, DE102011076022A1 and DE102011076035A1.
  This is a showcase about how to integrate a link to a list of patent documents into own applications.
  The `nasa-public-domain demo`_ is a similar demo, it displays a number of patents of the
  `Public Domain NASA technologies`_.

- The `document view demo`_ will display the patent document EP0666666A2 without any control elements.
  This is a showcase about how to embed the document view into own applications or
  how to directly link to single documents.


************
Data sources
************

PatZilla uses different API services for accessing patent information.

Primary data sources:

- `EPO/OPS`_
- `DPMA/DEPATISnet`_
- `IFI Claims`_
- `MTC depa.tech`_

Auxiliary data sources:

- `USPTO/PATIMG`_
- `CIPO`_


***************
Getting started
***************

Getting started with the software or deploying it yourself is quite easy if
you are familiar with Python or Docker. See the `install documentation`_ page
about how to install, configure and run PatZilla.


*******************
Project information
*******************

The source code of »PatZilla IP Navigator« is available under an open source
license using the brand name »PatZilla«.

For further details, please visit:

- `PatZilla on GitHub <https://github.com/ip-tools/patzilla>`_
- `PatZilla documentation <https://docs.ip-tools.org/patzilla/>`_
- `PatZilla on the Python Package Index (PyPI) <https://pypi.org/project/patzilla/>`_


*******
History
*******

The software got some applause from professional researchers for its unique user
interface and rich feature set when it was released to the first audience in 2014.
We hear from our users they are still having a great pleasure working with it on
a daily basis.

After four years of development, the source code finally gets released under an
open source license in 2017. We are looking forward to opening up the development
process as well, every kind of participation and support is very much welcome.

After a project hiatus from 2020 to 2022, the code base is getting a refresh,
many software tests have been added, and the aim is to finish migration to
Python 3 within the end of the year.


************
Contributing
************

We are always happy to receive code contributions, ideas, suggestions
and problem reports from the community.
Spend some time taking a look around, locate a bug, design issue or
spelling mistake and then send us a pull request or create an `issue`_.

Thanks in advance for your efforts, we really appreciate any help or feedback.


*******
License
*******

This software is copyright © 2013-2022 The PatZilla authors. All rights reserved.

It is and will always be **free and open source software**.

Use of the source code included here is governed by the
`GNU Affero General Public License <GNU-AGPL-3.0_>`_ and the
`European Union Public License <EUPL-1.2_>`_.
Please also have a look at the `notices about licenses of third-party components`_.


*******
Support
*******

For enterprises, dedicated commercial support is also available through
Elmyra UG. `Elmyra UG`_ is the software development company that’s
spearheading the ongoing development and as such will ensure
continuity for the project.

If you are using PatZilla in your company, and you need support or custom
development, feel free to get in touch with us by sending corresponding
inquiries to info@elmyra.de.

In this way, you are contributing to the ongoing maintenance and further
development of PatZilla.


.. _cli documentation: https://docs.ip-tools.org/patzilla/running/cli.html
.. _GNU-AGPL-3.0: https://docs.ip-tools.org/patzilla/_static/license/GNU-AGPL-3.0.txt
.. _install documentation: https://docs.ip-tools.org/patzilla/install/
.. _issue: https://github.com/ip-tools/patzilla/issues
.. _Public Domain NASA technologies: https://web.archive.org/web/20210620125651/https://technology.nasa.gov/publicdomain
.. _notices about licenses of third-party components: https://github.com/ip-tools/patzilla/blob/main/THIRD-PARTY-NOTICES.rst
.. _Elmyra UG: https://elmyra.de/
.. _EUPL-1.2: https://docs.ip-tools.org/patzilla/_static/license/EUPL-1.2.txt
.. _Europatent PATOffice Navigator: https://web.archive.org/web/20210613132912/https://www.europatent.net/software/patofficenavigator/
.. _Serviva PATselect 4.0: https://serviva.com/ps-4-0/

.. _document view demo: https://patentview.ip-tools.io/view/pn/EP0666666A2
.. _nasa-public-domain demo: https://patentview.ip-tools.io/?op=eyJhbGciOiAiUlMyNTYiLCAidHlwIjogIkpXVCJ9.eyJqdGkiOiAiTFFoQzMxbjBzalpLZlU5QUNmRVNMQT09IiwgImRhdGEiOiB7InByb2plY3QiOiAiTkFTQSBQdWJsaWMgRG9tYWluIiwgIm51bWJlcmxpc3QiOiAiVVM1Njg5MDA0LFVTNzAwODYwNSxVUzcwMjMxMTgsVVM3NDM4MDMwLFVTNzc3MzM2MixVUzc3OTAxMjgsVVM3ODA4MzUzLFVTNzkwMDQzNixVUzc5MzMwMjcsVVM4MjEyMTM4LFVTODI1OTEwNCxVUzg0MDc5NzksVVM4NzYzMzYyLFVTODkzODk3NCxVUzkwMTY2MzIsVVM5MDIxNzgyLFVTOTA5MTQ5MCxVUzkxOTQzMzQsVVM5MTk0MzM0QjEiLCAiY29udGV4dCI6ICJ2aWV3ZXIiLCAidHRsIjogIjE1Nzg1MjgwMCIsICJtb2RlIjogImxpdmV2aWV3IiwgImRhdGFzb3VyY2UiOiAicmV2aWV3In0sICJuYmYiOiAxNTUzMDM2MDgxLCAiZXhwIjogMTcxMDg4ODg4MSwgImlhdCI6IDE1NTMwMzYwODF9.gejftmq0JiHZEyjBQbQy0QSsKpjDd0TsGl0Zp8BVhH9IrxPi4YT5sxxXjWOU46I3OASzAANodttMJydzgP2DjeIF7VJnjMA9ZrHeqAL30gk8WOmbEIse7l2ciOfhJtyT
.. _numberlist demo: https://patentview.ip-tools.io/?numberlist=DE102011075997A1%2CDE102011076020A1%2CDE102011076022A1%2CDE102011076035A1&mode=liveview
.. _search demo: https://patentview.ip-tools.io/?op=eyJhbGciOiAiUlMyNTYiLCAidHlwIjogIkpXVCJ9.eyJqdGkiOiAiZDZUT3Ewc3NkRDB6TTVCSGdhOEJrQT09IiwgImRhdGEiOiB7InByb2plY3QiOiAicXVlcnktcGVybWFsaW5rIiwgInF1ZXJ5IjogInR4dD0oU1M3IG9yICh0ZWxlY29tbXVuaWNhdGlvbiBvciBjb21tdW5pY2F0aW9uIG9yIGNvbXVuaWNhY2lcdTAwZjNuKSBvciAobW9iaWxlIG9yIE1vYmlsZnVua25ldHopIG9yIChuZXR3b3JrIG9yIChzZWN1cml0eSBvciBTaWNoZXJ1bmcpKSkgYW5kIHBhPShtb2JpbCBvciBrb21tdW5pa2F0aW9uKSBhbmQgY2w9KEgwNFcxMi8xMiBvciBIMDRMNjMvMDI4MSBvciBIMDRMNjMvMDQxNCkgbm90IHBuPShDTiBvciBDQSBvciBKUCkiLCAibW9kZSI6ICJsaXZldmlldyIsICJjb250ZXh0IjogInZpZXdlciIsICJkYXRhc291cmNlIjogIm9wcyJ9LCAibmJmIjogMTUwNzgyNjYxNywgImV4cCI6IDE2NjMzNDY2MTcsICJpYXQiOiAxNTA3ODI2NjE3fQ.fCl7I5wPd0r48O48UkVQxzw9QOy5PjFaFecmAoYisbM-Her9Z6R0E2hxc82TSdH68gz379jQe5v9eF6g620aG4odTOXtdhyoDrWcb-GJcfR-0BfpiqPRwzLng53ape69

.. _CIPO: http://cipo.gc.ca
.. _DPMA/DEPATISnet: https://depatisnet.dpma.de/DepatisNet/depatisnet?window=1&space=menu&content=index&action=index&switchToLang=en
.. _EPO/OPS: https://ops.epo.org/
.. _IFI Claims: https://www.ificlaims.com/
.. _MTC depa.tech: https://depa.tech/
.. _USPTO/PATIMG: https://www.uspto.gov/
