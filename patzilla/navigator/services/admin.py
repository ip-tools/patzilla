# -*- coding: utf-8 -*-
# (c) 2013-2015 Andreas Motl, Elmyra UG
import logging
import typing as t

import arrow
import simplejson
from fastapi import APIRouter, HTTPException, Response
from patzilla.access.epo.ops.api import ops_service_usage
from patzilla.util.date import week_range, month_range, year_range
from patzilla.util.web.identity.store import User
from patzilla.web.dependencies import OpsClient

log = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


@router.get("/api/admin/users/emails", name="admin-users-email-service",
            summary="Responds with email addresses of all customers")
def admin_users_emails_handler(tag: t.Optional[str] = None):
    users = User.objects()  # ty: ignore[unresolved-attribute]
    user_emails = []
    for user in users:
        if '@' not in user.username:
            continue
        if 'email:invalid' in user.tags or 'newsletter:opt-out' in user.tags:
            continue
        if tag and tag not in user.tags:
            continue
        user_emails.append(user.username.lower())

    payload = '\n'.join(user_emails)

    return Response(payload, media_type='text/plain')


@router.get("/api/ops/usage/{kind}/{duration}", name="ops-usage", summary="OPS usage interface")
def ops_usage_handler(kind: str, duration: str, client: OpsClient):
    # TODO: respond with proper 4xx codes if something fails

    now = arrow.utcnow()

    date_begin = None
    date_end = None

    if kind == 'ago':
        if duration == 'day':
            date_begin = now.replace(days=-1)
            date_end = now

        elif duration == 'week':
            date_begin = now.replace(weeks=-1)
            date_end = now

        elif duration == 'month':
            date_begin = now.replace(months=-1)
            date_end = now

        elif duration == 'year':
            date_begin = now.replace(years=-1)
            date_end = now

    elif kind == 'current':
        if duration == 'day':
            date_begin = now.replace(days=-1)
            date_end = now

        elif duration == 'week':
            date_begin, date_end = week_range(now)

        elif duration == 'month':
            date_begin, date_end = month_range(now)

        elif duration == 'year':
            date_begin, date_end = year_range(now)

    if not date_begin or not date_end:
        raise HTTPException(404, 'Use /day, /week, /month or /year, /{0}/{1} not implemented'.format(kind, duration))

    date_begin = date_begin.format('DD/MM/YYYY')
    date_end = date_end.format('DD/MM/YYYY')

    response = ops_service_usage(client, date_begin, date_end)
    return Response(simplejson.dumps(response, use_decimal=True, sort_keys=True, indent=4), media_type='application/json')
