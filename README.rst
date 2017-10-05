############
IP Navigator
############


About
=====
The IP Navigator is a modular patent information research platform and toolkit
with a modern user interface and access to multiple data sources.

Features:

- Multiple data source APIs.

  - Use different patent search services with varying coverage.
  - Connect to multiple services for pdf-, image-, bibliographic data and fulltext acquisition.

- User interface. Based on contemporary web technologies and responsive design, it works on multiple devices.
  Use it on PCs, tablets, smartphone devices or as a multi-screen solution.

- Dossier management. Manage different collections of patent documents and apply ratings and comments.

- REST API. Through the extensive REST API, all functionality is available to 3rd-party systems.
  Deep integration has no limits.

- Sharing. Well-designed collaboration features allow efficient sharing of information with your colleagues,
  even across the boundaries of in-house systems.

- Multitenancy. The software can operate on behalf of different vendors. It's easy to apply custom branding.


Demos
=====
- The `search demo`_ will run the fixed query::

      Bi=((Greife? OR Grip?) and (rohr or tube or circular)) and pc=(DE or EP) and IC=(B26D? or B23D?)

  ... against DEPATISnet and display the results.
  You will be able to step through result pages and display fulltext- and family-information,
  but running custom queries will be disabled.

- The `document view demo`_ will display the patent document EP0666666A2 without any control elements.
  This is a showcase about how to embed the document view into own applications or
  how to directly link to single documents.



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


Screenshot
==========
.. image:: docs/ip-navigator.png
    :alt: IP Navigator
    :target: https://github.com/ip-tools/ip-navigator


Contributing
============
We are always happy to receive code contributions, ideas, suggestions
and problem reports from the community!
Please use the `issues`_ system for communicating them.


License
=======
The IP Navigator is and will always be **free and open source software**.
Use of the source code included here is governed by the
`GNU Affero General Public License <GNU-AGPL-3.0_>`_ and the
`European Union Public License <EUPL-1.2_>`_.
Please also have a look at the `notices about licenses of third-party components`_.


Support
=======
For enterprises, dedicated commercial support is also available through `Elmyra UG`_.


Setup
=====
See `install docs`_ about how to run an instance in a development sandbox.


.. _GNU-AGPL-3.0: GNU-AGPL-3.0.txt
.. _EUPL-1.2: EUPL-1.2.txt
.. _notices about licenses of third-party components: THIRD-PARTY-NOTICES.rst
.. _install docs: docs/technical/install-development.rst

.. _Elmyra UG: https://elmyra.de/
.. _search demo: https://patentview.ip-tools.io/?op=eyJhbGciOiAiUFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJqdGkiOiAiUmlnSGlLRm91N0daUlVseDdTTTBYRkNXdWlqOUlLNnFoaS1lUnowMUdVOEVqVzFUb1lrWHRGLXdFekJqbTA5WjA3bndmN0JtZmJfcnFfeC1xcUd4Qm5qRl9CN0Zkb1NCOTJoZ25DNXg2aDA2OVBiZGtwRjlKdUhRUzVoZ0RLY212M2VPenFQOVlVTlBqTmdpaGM0Rmo3U25OMHJiS3ExRTByN2EweVk3N19rPSIsICJkYXRhIjogeyJwcm9qZWN0IjogInF1ZXJ5LXBlcm1hbGluayIsICJxdWVyeSI6ICJCaT0oKEdyZWlmZT8gT1IgR3JpcD8pIGFuZCAocm9ociBvciB0dWJlIG9yIGNpcmN1bGFyKSkgYW5kIHBjPShERSBvciBFUCkgYW5kIElDPShCMjZEPyBvciBCMjNEPykiLCAibW9kZSI6ICJsaXZldmlldyIsICJjb250ZXh0IjogInZpZXdlciIsICJkYXRhc291cmNlIjogImRlcGF0aXNuZXQifSwgIm5iZiI6IDE0MDU1MjcwMjMsICJleHAiOiAxNTYxMDQ3MDIzLCAiaWF0IjogMTQwNTUyNzAyM30.Ec0CjI2lLPLAoVxADDrkZlIRgbELqfUAP-0kKtrnWZ6YIm9iUc-KhekqWigyLQ-cSVWCDymLorON-KN79xojgzCvV8D-FZTwXVjMOwREGUJ6osm-7NiCNhXIjDCh1H2X
.. _document view demo: https://patentview.ip-tools.io/view/pn/EP0666666A2
.. _issues: https://github.com/ip-tools/ip-navigator/issues

.. _EPO/OPS: https://ops.epo.org/
.. _DPMA/DEPATISnet: https://depatisnet.dpma.de
.. _USPTO/PATIMG: https://www.uspto.gov/
.. _CIPO: http://cipo.gc.ca
.. _IFI Claims: https://www.ificlaims.com/
.. _MTC depa.tech: https://depa.tech/

