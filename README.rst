.. image:: https://img.shields.io/badge/Python-2.7-green.svg
    :target: https://github.com/ip-tools/ip-navigator

.. image:: https://img.shields.io/pypi/v/patzilla.svg
    :target: https://pypi.org/project/patzilla/

.. image:: https://img.shields.io/github/tag/ip-tools/ip-navigator.svg
    :target: https://github.com/ip-tools/ip-navigator

|

################################################
PatZilla: Patent information research for humans
################################################


About
=====
PatZilla is a modular patent information research platform and
data integration toolkit. It features a modern user interface
and access to multiple data sources.

The system provides convenient access to the OPS service from EPO and
other professional fulltext patent databases in its standalone version.
You can also use its software components and interfaces for
building arbitrary vendor solutions.


Features
========

- Multiple data source APIs.

  - Use different patent search services with varying coverage.
  - Connect to multiple services for pdf-, image-, bibliographic data and fulltext acquisition.

- User interface. Based on contemporary web technologies and responsive design, it works on multiple devices.
  Use it on PCs, tablets, smartphone devices or as a multi-screen solution. The clear and well-arranged
  design and layout permits efficient screening of large numbers of patent documents.

- Dossier management. Manage different collections of patent documents and apply ratings and comments.

- REST API. Through the extensive REST API, all functionality is available to 3rd-party systems.
  Deep integration has no limits.

- Sharing. Well-designed collaboration features allow efficient sharing of information with your
  colleagues and partners, even across the boundaries of in-house systems.

- Multitenancy. The software can operate on behalf of different vendors. It's easy to apply custom branding.


Screenshot
==========
A picture says a thousand words.

.. image:: https://raw.githubusercontent.com/ip-tools/ip-navigator/master/patzilla-screenshot.png
    :alt: IP Navigator
    :target: https://github.com/ip-tools/ip-navigator


Demos
=====
- The `search demo`_ will run the fixed query::

      txt=(SS7 or (telecommunication or communication or comunicación) or (mobile or Mobilfunknetz) or (network or (security or Sicherung))) and
      pa=(mobil or kommunikation) and
      cl=(H04W12/12 or H04L63/0281 or H04L63/0414)
      not pn=(CN or CA or JP)

  ... against EPO/OPS and display the results.
  You will be able to step through result pages and display fulltext- and family-information,
  but running custom queries will be disabled.

- The `numberlist demo`_ will display the patent documents DE102011075997A1, DE102011076020A1, DE102011076022A1 and DE102011076035A1.
  This is a showcase about how to integrate a link to a list of patent documents into own applications.

- The `document view demo`_ will display the patent document EP0666666A2 without any control elements.
  This is a showcase about how to embed the document view into own applications or
  how to directly link to single documents.

- The `nasa-public-domain demo`_ displays the latest `NASA patents put under the public domain <NASA public domain_>`_.


Data sources
============
The IP Navigator uses different API services for accessing patent information.

Primary data sources:

- `EPO/OPS`_
- `DPMA/DEPATISnet`_
- `IFI Claims`_
- `MTC depa.tech`_

Auxiliary data sources:

- `USPTO/PATIMG`_
- `CIPO`_


Getting started
===============
Getting started with the software or deploying it yourself is quite easy if you are familiar with Python.
We will only cover development here, see the `install documentation`_ page about how to install, configure
and run an instance.
The software should work on any other Linux or BSD distribution, but this is beyond the scope of the README.

It runs on Python 2.7, but is not ready for Python 3.6 yet. Contributions are welcome!


Project information
===================
The source code of the »IP Navigator« is available under an open source license using the brand name »PatZilla«.
For further details, please visit:

- `PatZilla on GitHub <https://github.com/ip-tools/ip-navigator>`_
- `PatZilla documentation <https://docs.ip-tools.org/ip-navigator/>`_
- `PatZilla on the Python Package Index (PyPI) <https://pypi.org/project/patzilla/>`_


History
=======
The software got some applause from professional researchers for its unique user
interface and rich feature set when it was released to the first audience in 2014.
We hear from our users they are still having a great pleasure working with it on a daily basis.

After four years of development, the source code finally gets released under an
open source license in 2017. We are looking forward to opening up the development
process as well, every kind of participation and support is very much welcome.


Contributing
============
We are always happy to receive code contributions, ideas, suggestions
and problem reports from the community.
Spend some time taking a look around, locate a bug, design issue or
spelling mistake and then send us a pull request or create an `issue`_.

Thanks in advance for your efforts, we really appreciate any help or feedback.


License
=======
This software is copyright © 2013-2018 The PatZilla authors. All rights reserved.

It is and will always be **free and open source software**.

Use of the source code included here is governed by the
`GNU Affero General Public License <GNU-AGPL-3.0_>`_ and the
`European Union Public License <EUPL-1.2_>`_.
Please also have a look at the `notices about licenses of third-party components`_.


Support
=======
For enterprises, dedicated commercial support is also available through Elmyra UG.
`Elmyra UG`_ is the software development company that’s spearheading the ongoing
development and as such will ensure continuity for the project.

If you’re using the IP Navigator in your company and you need support or custom development,
feel free to get in touch with us. We are happy to receive respective inquiries at support@elmyra.de.


.. _GNU-AGPL-3.0: https://docs.ip-tools.org/ip-navigator/_static/license/GNU-AGPL-3.0.txt
.. _EUPL-1.2: https://docs.ip-tools.org/ip-navigator/_static/license/EUPL-1.2.txt
.. _notices about licenses of third-party components: https://docs.ip-tools.org/ip-navigator/license/THIRD-PARTY-NOTICES.html
.. _install documentation: https://docs.ip-tools.org/ip-navigator/install/

.. _Elmyra UG: https://elmyra.de/
.. _search demo: https://patentview.ip-tools.io/?op=eyJhbGciOiAiUlMyNTYiLCAidHlwIjogIkpXVCJ9.eyJqdGkiOiAiZDZUT3Ewc3NkRDB6TTVCSGdhOEJrQT09IiwgImRhdGEiOiB7InByb2plY3QiOiAicXVlcnktcGVybWFsaW5rIiwgInF1ZXJ5IjogInR4dD0oU1M3IG9yICh0ZWxlY29tbXVuaWNhdGlvbiBvciBjb21tdW5pY2F0aW9uIG9yIGNvbXVuaWNhY2lcdTAwZjNuKSBvciAobW9iaWxlIG9yIE1vYmlsZnVua25ldHopIG9yIChuZXR3b3JrIG9yIChzZWN1cml0eSBvciBTaWNoZXJ1bmcpKSkgYW5kIHBhPShtb2JpbCBvciBrb21tdW5pa2F0aW9uKSBhbmQgY2w9KEgwNFcxMi8xMiBvciBIMDRMNjMvMDI4MSBvciBIMDRMNjMvMDQxNCkgbm90IHBuPShDTiBvciBDQSBvciBKUCkiLCAibW9kZSI6ICJsaXZldmlldyIsICJjb250ZXh0IjogInZpZXdlciIsICJkYXRhc291cmNlIjogIm9wcyJ9LCAibmJmIjogMTUwNzgyNjYxNywgImV4cCI6IDE2NjMzNDY2MTcsICJpYXQiOiAxNTA3ODI2NjE3fQ.fCl7I5wPd0r48O48UkVQxzw9QOy5PjFaFecmAoYisbM-Her9Z6R0E2hxc82TSdH68gz379jQe5v9eF6g620aG4odTOXtdhyoDrWcb-GJcfR-0BfpiqPRwzLng53ape69
.. _numberlist demo: https://patentview.ip-tools.io/?numberlist=DE102011075997A1%2CDE102011076020A1%2CDE102011076022A1%2CDE102011076035A1&mode=liveview
.. _document view demo: https://patentview.ip-tools.io/view/pn/EP0666666A2
.. _issue: https://github.com/ip-tools/ip-navigator/issues

.. _NASA public domain: https://technology.nasa.gov/latest/public_domain
.. _nasa-public-domain demo: https://patentview.ip-tools.io/?op=eyJhbGciOiAiUlMyNTYiLCAidHlwIjogIkpXVCJ9.eyJqdGkiOiAieWJtZDRWeEtlcDlvcW1YaFM0a2NwQT09IiwgImRhdGEiOiB7InByb2plY3QiOiAibmFzYS1wdWJsaWMtZG9tYWluLXJlY2VudCIsICJkYXRhc291cmNlIjogInJldmlldyIsICJjb250ZXh0IjogInZpZXdlciIsICJ0dGwiOiAiMTU2MzQ4MDAiLCAibW9kZSI6ICJsaXZldmlldyIsICJudW1iZXJsaXN0IjogIlVTNTY4OTAwNCxVUzcwMDg2MDUsVVM3MDIzMTE4LFVTNzQzODAzMCxVUzc3NzMzNjIsVVM3NzkwMTI4LFVTNzgwODM1MyxVUzc5MDA0MzYsVVM3OTMzMDI3LFVTODIxMjEzOCxVUzgyNTkxMDQsVVM4NDA3OTc5LFVTODc2MzM2MixVUzg5Mzg5NzQsVVM5MDE2NjMyLFVTOTAyMTc4MixVUzkwOTE0OTAsVVM5MTk0MzM0In0sICJuYmYiOiAxNTA5NDI4NjI2LCAiZXhwIjogMTUyNTA2MzQyNiwgImlhdCI6IDE1MDk0Mjg2MjZ9.hFx5wWhi-n4w8ZJTVGC7liQeMfqpH8VTpRfmT6twfM4As23MBTwlsmg0u2frfYs0zV6qCsQngwwvQ2Tn6VCju8yf5GBIG5erB3VFyOr_EtZejFJOqTO6A5esEcUtyeXZ

.. _EPO/OPS: https://ops.epo.org/
.. _DPMA/DEPATISnet: https://depatisnet.dpma.de
.. _USPTO/PATIMG: https://www.uspto.gov/
.. _CIPO: http://cipo.gc.ca
.. _IFI Claims: https://www.ificlaims.com/
.. _MTC depa.tech: https://depa.tech/

