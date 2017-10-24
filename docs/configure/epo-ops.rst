.. _epo-ops-setup:

##############################
EPO Open Patent Services setup
##############################

.. contents::
   :local:
   :depth: 1

----

*****
About
*****
PatZilla uses the Open Patent Services (OPS) provided by the European Patent Office (EPO)
to display bibliographic data of patent documents.

For general information about the EPO OPS service, please refer to :ref:`datasource-epo-ops`.


.. _epo-ops-account-register:

********************
Account registration
********************

In order to use the EPO OPS 3.2 services, you have to register yourself at the `EPO Developer Portal`_
to get authentication credentials for accessing the API. The steps for registration are:

- Apply for account registration at https://developers.epo.org/user/register, fulfill and submit the form.
  Just use the "Non-paying" access method or read below for other options.
- Wait until you receive the email confirmation from the EPO Developer Portal.
- Login to the EPO Developer Portal at https://developers.epo.org/user/login
- Select the option “My Apps” in the upper right corner.
- Register a new application by clicking "Add a new App". Use "PatZilla" or anything you like as an application name.
- The system will return the API credentials named "Consumer Key" and "Consumer Secret".

.. note::

    The "Non-paying" access method offers 3.5 GB of traffic volume per week for free.
    This is usually sufficient even for intensive research work performed by a single person.

    If you really think your usage will exceed this volume, the other option is the
    "Paying" access method which offers unlimited traffic volume for a fee of € 2.800,- per year.

    In any case, users must respect the Fair use charter for the EPO's online patent information products.

    For more information, please have a look at the respective resources provided by the EPO:

    - `New OPS terms of use and Fair use charter from 2018 on <https://forums.epo.org/new-ops-terms-of-use-and-fair-use-charter-from-2018-on-7248>`_
    - `Terms and conditions for use of the EPO's Open Patent Services (OPS) <http://www.epo.org/service-support/ordering/ops-terms-and-conditions.html>`_
    - `Fair use charter for the EPO's online patent information products <http://www.epo.org/searching-for-patents/helpful-resources/fair-use.html>`_
    - `EPO Patent Information Products and Services - Price list <http://documents.epo.org/projects/babylon/eponet.nsf/0/0B52985F1EFEBCBBC12574EC00263E07/$File/epo_patent_information_price-list_01-2018.pdf>`_ on page 15

.. _EPO Developer Portal: https://developers.epo.org/


.. _epo-ops-system-wide:

*************************
System-wide configuration
*************************
For configuring PatZilla with system-wide OPS authentication credentials,
please put the "Consumer Key" and "Consumer Secret" values
obtained from the steps above into the PatZilla configuration file.

You will find the right place at section ``[datasource_ops]``::

    [datasource_ops]

    # Application-wide authentication credentials
    api_consumer_key    = ScirfedyifJiashwOckNoupNecpainLo
    api_consumer_secret = degTefyekDevgew1


.. _epo-ops-per-user:

**********************
Per-user configuration
**********************
PatZilla can use per-user credentials for authenticating against the OPS API.
An example schema for the :ref:`user-model` looks like this::

    upstream_credentials: {
        ops: {
            consumer_key:    "ScirfedyifJiashwOckNoupNecpainLo",
            consumer_secret: "degTefyekDevgew1"
        }
    }


.. _epo-ops-usage:

**********************
Monitor traffic volume
**********************

PatZilla provides the API endpoint "OPS usage interface" for investigating
the current and former traffic volume consumption.

The URL schema is::

    /api/ops/usage/{kind}/{duration}

- ``kind`` may be one of ``current`` or ``ago``.
- ``duration`` may be one of ``day``, ``week``, ``month`` or ``year``.

Example
=======
By accessing ``/api/ops/usage/current/week``, an example response might look like::

    {
        "message-count": 6186.0,
        "response-size": 79273501.0,
        "time-range": "16/10/2017 to 22/10/2017"
    }

The unit of the field ``response-size`` is Bytes, so you have to divide it by 10^9
to get the Gigabytes used throughout the current week.

