.. include:: ../resources.rst


.. _user-model:

##########
User model
##########

*****
About
*****
The current user model is a simple flat list of JSON documents stored in MongoDB_, one for each user.
It contains all information required to control the application behavior and additional fields
used for information only:

- Login credentials: ``username`` and ``password``.
- Group information: ``tags`` is a list of tag labels.
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
This is an example document for a user. All credentials are randomly generated for demonstration purposes.
::

    {
        _id: ObjectId("53c3527ba42dde3f51ad84c2"),
        userid: "30cba474-3ff4-499d-a152-1865b3d69988",
        username: "john.doe@example.org",
        password: "$p5k2$1f4$h/9ChodR$BeshyidM.evabNaibeamyoogUkKept42",
        fullname: "John Doe",
        phone: "+49-1234-1234567",
        created: ISODate("2016-09-08T11:58:19.397Z"),
        modified: ISODate("2016-09-08T11:58:19.397Z"),
        tags: [
            "custom-group",
            "staff"
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
