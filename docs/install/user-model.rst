.. include:: ../resources.rst


.. _user-model:

##########
User model
##########


.. _user-add:

********
Add user
********
After PatZilla is installed, there is the ``patzilla-user`` command line program for adding users.

Configure path to application configuration::

    export PATZILLA_CONFIG=/path/to/patzilla.ini

Simple add::

    patzilla-user add --fullname "John Doe" --username "john.doe@example.org" --password "john123"

Add user, also enabling some modules::

    patzilla-user add \
        --fullname "Max Mustermann" --username "max@example.org" --password "max987" \
        --tags "demo" --modules "keywords-user, family-citations"

Add user with more details::

    patzilla-user add \
        --fullname "Max Mustermann" --username "max@example.org" --password "max987" \
        --tags "demo" --modules "keywords-user, family-citations" \
        --organization "Example Inc." --homepage "https://example.org/" --phone "+49-1234-1234567"

.. note:: For possible values of ``--tags`` and ``--modules``, please refer to the next section.



.. _user-import:

************
Import users
************
You can also import multiple users from a CSV file in batch mode::

    patzilla-user import /path/to/accounts.csv

An example ``accounts.csv`` could look like::

    "fullname","username","password","tags","modules","organization","homepage"
    "John Doe","john.doe@example.org","demo","trial, demo","keywords-user, family-citations","Example Inc.","https://example.org/"
    "Max Mustermann","max.mustermann@example.org","demo",,,,



*******
Details
*******
The current user model is a simple flat list of JSON documents stored in MongoDB_, one for each user.
It contains all information required to control the application behavior and additional fields
used for information only:

- Login credentials: ``username`` and ``password``.
- Tag information: ``tags`` is a list of arbitrary tag labels.
  Add the ``staff`` label for accessing resources which require administrator permissions.
- Module activation: ``modules`` is a list of enabled modules. Choose one or more from:

    - ``keywords-user``: Module to provide a custom list of keywords for highlighting.
    - ``family-citations``: Module to explore the citation environment of family members.
    - ``analytics``: Module to run analytic processes over search results.
    - ``ificlaims``: Enable data source "`IFI Claims`_".
    - ``depatech``: Enable data source "`MTC depa.tech`_".

- Datasource credentials: ``upstream_credentials`` is a dictionary
  containing authentication information for each data source provider:

    - ``ops``: Credentials for accessing Open Patent Services from EPO
    - ``ificlaims``: Credentials for accessing the IFI Claims API
    - ``depatech``: Credentials for accessing the depa.tech API from MTC


*******
Example
*******
This is an example document for a regular user. All credentials are randomly generated for demonstration purposes.
::

    {
        _id: ObjectId("53c3527ba42dde3f51ad84c2"),
        userid: "30cba474-3ff4-499d-a152-1865b3d69988",
        username: "john.doe@example.org",
        password: "$p5k2$1f4$h/9ChodR$BeshyidM.evabNaibeamyoogUkKept42",
        fullname: "John Doe",
        created: ISODate("2016-09-08T11:58:19.397Z"),
        modified: ISODate("2016-09-08T11:58:19.397Z"),
        tags: [
            "custom-group"
        ],
        modules: [
            "keywords-user",
            "family-citations",
            "analytics",
            "ificlaims",
            "depatech"
        ],
        upstream_credentials: {
            ops: {
                consumer_key: "ScirfedyifJiashwOckNoupNecpainLo",
                consumer_secret: "degTefyekDevgew1"
            },
            ificlaims: {
                username: "john.doe",
                password: "Tichbeed"
            },
            depatech: {
                username: "john.doe",
                password: "ogdotdut"
            }
        }
    }
