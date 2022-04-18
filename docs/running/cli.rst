.. _cli:

#####################################
PatZilla command line interface (CLI)
#####################################

PatZilla is well suited to be used on the command line as a powerful "Swiss
Army knife"-like utility for patent data acquisition and mangling.

You can use it with your well-known PatZilla configuration file like::

    export PATZILLA_CONFIG=patzilla/config/development-local.ini
    patzilla lalala

You can also invoke it without any configuration file at all by providing
essential options configuring access to data sources on the command line::

    # For accessing "EPO OPS".
    export OPS_API_CONSUMER_KEY=y3A0G86cmcij0OQU69VYGTJ4JGxUN8EVG
    export OPS_API_CONSUMER_SECRET=rrXdr5WA7x9tudmP
    patzilla ops lalala

    # For accessing "IFI CLAIMS Direct".
    export IFICLAIMS_API_URI=https://cdws21.ificlaims.com
    export IFICLAIMS_API_USERNAME=acme
    export IFICLAIMS_API_PASSWORD=10f8GmWTz
    patzilla ificlaims lalala

    # For accessing "depa.tech".
    export DEPATECH_API_URI=https://api.depa.tech
    export DEPATECH_API_USERNAME=example.org
    export DEPATECH_API_PASSWORD=PkT326X5LAZkfgRp
    patzilla depatech lalala

