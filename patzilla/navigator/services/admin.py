# -*- coding: utf-8 -*-
# (c) 2013-2015 Andreas Motl, Elmyra UG
import logging
import arrow
from cornice.service import Service
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from patzilla.access.epo.ops.api import ops_service_usage
from patzilla.util.date import week_range, month_range, year_range
from patzilla.util.web.identity.store import User

log = logging.getLogger(__name__)

admin_users_emails_service = Service(
    name='admin-users-email-service',
    path='/api/admin/users/emails',
    description="Responds with email addresses of all customers")

@admin_users_emails_service.get()
def admin_users_emails_handler(request):
    tag = request.params.get('tag')
    users = User.objects()
    user_emails = []
    for user in users:
        if '@' not in user.username:
            continue
        if 'email:invalid' in user.tags or 'newsletter:opt-out' in user.tags:
            continue
        if tag and tag not in user.tags:
            continue
        user_emails.append(user.username.lower())

    payload = u'\n'.join(user_emails)

    return Response(payload, content_type='text/plain', charset='utf-8')


ops_usage_service = Service(
    name='ops-usage',
    path='/api/ops/usage/{kind}/{duration}',
    renderer='prettyjson',
    description="OPS usage interface")

@ops_usage_service.get()
def ops_usage_handler(request):
    # TODO: respond with proper 4xx codes if something fails
    kind = request.matchdict['kind']
    duration = request.matchdict['duration']

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
        raise HTTPNotFound('Use /day, /week, /month or /year, /{0}/{1} not implemented'.format(kind, duration))

    date_begin = date_begin.format('DD/MM/YYYY')
    date_end = date_end.format('DD/MM/YYYY')

    response = ops_service_usage(date_begin, date_end)
    return response
