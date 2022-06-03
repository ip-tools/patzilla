.. _cli:

#####################################
PatZilla command line interface (CLI)
#####################################


************
Introduction
************

PatZilla can be used on the command line as a powerful "Swiss Army knife"-like
utility for patent data acquisition and processing.


*************
Configuration
*************

You can either use it with your well-known PatZilla configuration file, like::

    export PATZILLA_CONFIG=patzilla/config/development-local.ini
    patzilla ops usage
    patzilla ops search "txt=(wind or solar) and energy"

You can also invoke it without any configuration file at all by providing
essential options configuring access to data sources on the command line::

    # For accessing "EPO OPS".
    export OPS_API_CONSUMER_KEY=y3A0G86cmcij0OQU69VYGTJ4JGxUN8EVG
    export OPS_API_CONSUMER_SECRET=rrXdr5WA7x9tudmP
    patzilla ops usage
    patzilla ops search "txt=(wind or solar) and energy"

    # For accessing "IFI CLAIMS Direct".
    export IFICLAIMS_API_URI=https://cdws21.ificlaims.com
    export IFICLAIMS_API_USERNAME=acme
    export IFICLAIMS_API_PASSWORD=10f8GmWTz
    patzilla ificlaims search "text:(wind or solar) and energy"

    # For accessing "depa.tech".
    export DEPATECH_API_URI=https://api.depa.tech
    export DEPATECH_API_USERNAME=example.org
    export DEPATECH_API_PASSWORD=PkT326X5LAZkfgRp
    patzilla depatech lalala

When both kinds of configuration variants apply, the first one takes precedence.
So, if ``PATZILLA_CONFIG`` is set on your environment, it will be used and other
settings will not be taken into account. Use, for example, ``unset
PATZILLA_CONFIG`` in order to remove the setting from your environment again.


********
Examples
********

::

    # Inquire usage information about the last seven days.
    patzilla ops usage

    # Inquire usage information about specific date range.
    patzilla ops usage --date-start=2022-04-01 --date-end=2022-04-07

    # Submit simple query to OPS published-data search interface.
    # Display either in XML or JSON format.
    patzilla ops search pn=EP666666 | xmllint --format -
    patzilla ops search pn=EP666666 --json | jq

    # Submit query searching EPO/OPS title and abstract texts.
    patzilla ops search "txt=(wind or solar) and energy"
