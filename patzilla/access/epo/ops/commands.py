# -*- coding: utf-8 -*-
# (c) 2014-2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
About
=====
Run requests to search provider "EPO OPS" from the command line.

Synopsis
========
Direct mode, without configuration file::

    export OPS_API_CONSUMER_KEY=y3A0G86cmcij0OQU69VYGTJ4JGxUN8EVG
    export OPS_API_CONSUMER_SECRET=rrXdr5WA7x9tudmP
    patzilla ops search "txt=(wind or solar) and energy"

Use configuration file::

    export PATZILLA_CONFIG=patzilla/config/development-local.ini
    patzilla ops search "txt=(wind or solar) and energy"
"""
import json
import logging
from datetime import date, timedelta

import click

from patzilla.access.epo.ops.api import OPS_API_URI, OPS_DEVELOPERS_URI, get_ops_client, get_ops_image, inquire_images
from patzilla.boot.config import BootConfiguration
from patzilla.boot.framework import pyramid_setup
from patzilla.util.config import get_configfile_from_commandline
from patzilla.util.data.container import jd


logger = logging.getLogger(__name__)


@click.group(name="ops")
@click.pass_context
def ops_cli(ctx):
    """
    Access the EPO/OPS data source adapter.
    """

    # Create a Pyramid runtime environment.
    env = pyramid_setup(
        configfile=get_configfile_from_commandline(),
        bootconfiguration=BootConfiguration(datasources=["ops"]),
    )

    # Propagate reference to the environment to the Click context.
    ctx.meta["pyramid_env"] = env


date_format_input = "%Y-%m-%d"
date_format_ops = "%d/%m/%Y"
click_date_type = click.DateTime(formats=[date_format_input])


@click.command(name="usage")
@click.option('--date-start', type=click_date_type, default=str(date.today() - timedelta(weeks=1)),
              help="Start date of timerange")
@click.option('--date-end', type=click_date_type, default=str(date.today()),
              help="End date of timerange")
@click.pass_context
def usage(ctx, date_start, date_end):
    """
    Access the OPS data usage API, see OPS handbook section 2.3.4.

    Example::

        {baseuri}/me/stats/usage?timeRange=16/04/2022~20/04/2022
    """
    verbose = ctx.find_root().params.get("verbose", False)
    date_start = date_start.strftime(date_format_ops)
    date_end = date_end.strftime(date_format_ops)

    logger.info("Inquiring OPS usage about date range {date_start}~{date_end}".format(**locals()))
    url = '{baseuri}/me/stats/usage?timeRange={date_start}~{date_end}'.format(baseuri=OPS_DEVELOPERS_URI, **locals())

    # Invoke API and output result.
    response = send_request(url, use_get=True, accept_json=True, verbose=verbose)
    print(response)


@click.command(name="search")
@click.argument("expression", type=str, required=True)
@click.option('--json', "request_json", is_flag=True, type=bool, default=False, required=False,
              help="Request/return data as JSON, otherwise use XML")
@click.pass_context
def search(ctx, expression, request_json):
    """
    Access the OPS bibliographic search API, see OPS handbook section 3.1.

    The `expression` argument accepts the search expression in OPS CQL syntax.

    TODO: Currently, only the first 100 hits will be displayed. Extend range by implementing "crawling".
    """
    verbose = ctx.find_root().params.get("verbose", False)
    url = '{baseuri}/published-data/search/biblio'.format(baseuri=OPS_API_URI, **locals())

    # Invoke API and output result.
    logger.warning("Only the first 100 hits will be displayed. The CLI currently does not employ paging.")
    response = send_request(
        url, parameters={'q': expression, 'Range': '1-100'}, accept_json=request_json, verbose=verbose)
    print(response)


@click.command(name="image-info")
@click.option("--document", type=str, required=True,
              help="The document / patent number")
@click.pass_context
def image_info(ctx, document):
    """
    Access the OPS image info API.
    """
    payload = inquire_images(document)
    print(jd(payload))


@click.command(name="image")
@click.option("--document", type=str, required=True,
              help="The document / patent number")
@click.option('--page', type=int, required=True,
              help="The page number")
@click.option('--kind', type=str, required=False, default="FullDocument",
              help="Which kind. One of `FullDocument` (default) or `FullDocumentDrawing`.")
@click.option('--format', type=str, required=False, default="pdf",
              help="Which format to use. One of `pdf` (default) or `tiff`.")
@click.pass_context
def image(ctx, document, page, kind, format):
    """
    Access the OPS image acquisition API, see OPS handbook section 3.1.3.
    """
    payload = get_ops_image(document, page, kind, format)
    print(payload)


ops_cli.add_command(cmd=usage)
ops_cli.add_command(cmd=search)
ops_cli.add_command(cmd=image_info)
ops_cli.add_command(cmd=image)


def mangle_range_parameter(parameters):
    range_value = parameters.get("Range", "1-10")
    if "Range" in parameters:
        del parameters["Range"]
    return range_value


def send_request(url, parameters=None, use_get=False, accept_json=False, verbose=False):
    """
    Generic wrapper to submit a request to OPS.
    """
    client = get_ops_client()

    parameters = parameters or {}

    # Decode `range` parameter.
    range_value = mangle_range_parameter(parameters)

    # Submit request to OPS.
    accept = "text/xml"
    if accept_json:
        accept = "application/json"
    response = client._make_request(
        url, data=parameters, extra_headers={"X-OPS-Range": range_value, "Accept": accept}, use_get=use_get,
    )

    if verbose:
        logger.info('EPO/OPS response information')
        logger.info('status: %s', response.status_code)
        logger.info('method: %s', response.request.method)
        logger.info('url:    %s', response.request.url)
        logger.info('headers:\n%s', json.dumps(dict(response.headers), indent=2))

    if response.status_code == 200:
        if response.headers["content-type"].startswith("application/json"):
            if verbose:
                logger.info('body:   ')
            return json.dumps(response.json(), indent=2)
        elif response.headers["content-type"].startswith("text/xml"):
            return response.content
    elif response.status_code == 404:
        message = 'Resource not found at EPO/OPS. Parameters={}'.format(url, parameters)
        logger.error(message)
        raise IOError(message)

    message = "An error happened while requesting data from EPO/OPS. " \
              "Status code was: {}. Response was:\n{}".format(response.status_code, response.content)
    raise IOError(message)
