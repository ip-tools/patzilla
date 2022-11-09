# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
About
=====
Run requests to USPTO data servers from the command line.

Synopsis
========
::

    patzilla peds search \
        --app-status=PATENTED --app-entity-status='NOT "UNDISCOUNTED"' \
        --patent-issue-date-begin="2012-01-01T00:00:00" --order-by=patent_issue_date \
        --attributes="app_status,patent_title,patent_number,patent_issue_date,assignments,applicants" \
        --transaction-codes="ALLOWANCE_NOTICE_VERIFICATION_COMPLETED, ALLOWANCE_NOTICE_MAILED, ISSUANCE_CONSIDERED_READY, ISSUANCE_NOTIFICATION_MAILED"

    cat output.json | jq -s '. | length'

"""
import logging

import click
import tqdm

from patzilla.access.uspto.peds.api import UsptoPedsAppStatus, UsptoPedsClient
from patzilla.boot.config import BootConfiguration
from patzilla.boot.framework import pyramid_setup
from patzilla.util.cli import EnumChoice
from patzilla.util.config import get_configfile_from_commandline

logger = logging.getLogger(__name__)


@click.group(name="peds")
@click.pass_context
def peds_cli(ctx):
    """
    Access the USPTO PEDS data source adapter.
    """

    # Create a Pyramid runtime environment.
    env = pyramid_setup(
        configfile=get_configfile_from_commandline(),
        bootconfiguration=BootConfiguration(datasources=["peds"]),
    )

    # Propagate reference to the environment to the Click context.
    ctx.meta["pyramid_env"] = env


def splitter(_, __, data):
    return [p.strip() for p in data.split(",")]


@click.command(name="search")
@click.option("--app-status", type=EnumChoice(UsptoPedsAppStatus), required=False)
@click.option("--app-entity-status", type=str, required=False)
@click.option("--patent-issue-date-begin", type=click.DateTime(), required=False)
@click.option("--patent-issue-date-end", type=click.DateTime(), required=False)
@click.option("--order-by", type=str, required=False)
@click.option("--attributes", type=str, callback=splitter, required=False)
@click.option("--transaction-codes", type=str, callback=splitter, required=False)
@click.pass_context
def search(
    ctx,
    app_status,
    app_entity_status,
    patent_issue_date_begin,
    patent_issue_date_end,
    order_by,
    attributes,
    transaction_codes,
):
    """
    Access the USPTO PEDS HTTP API.
    """

    # Get hold of data source client utility.
    client = UsptoPedsClient()

    # Invoke API and output result.
    response = client.query(
        app_status=app_status,
        app_entity_status=app_entity_status,
        patent_issue_date_begin=patent_issue_date_begin,
        patent_issue_date_end=patent_issue_date_end,
        order_by=order_by,
    )
    logger.info(f"Hit count: {response.count}")
    records = response.project(attributes=attributes, transaction_codes=transaction_codes)

    progress = tqdm.tqdm(total=response.count)
    for record in records:
        progress.update()
        print(response.to_json(record))


peds_cli.add_command(cmd=search)
