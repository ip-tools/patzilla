# -*- coding: utf-8 -*-
# (c) 2016-2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import logging
from email.utils import formataddr
from validate_email import validate_email
from pyramid.threadlocal import get_current_request
from elmyra.ip.util.config import read_config, read_list, to_list
from elmyra.ip.util.data.container import SmartBunch
from elmyra.ip.util.email.message import EmailMessage

log = logging.getLogger(__name__)


def message_factory(**kwargs):

    request = get_current_request()
    pyramid_settings = request.registry.settings

    # Read configuration file to get global settings
    # TODO: Optimize: Only read once, not on each request!
    settings = read_config(pyramid_settings['CONFIG_FILE'])

    # EmailMessage builder
    message = EmailMessage(settings['smtp'], settings['email'])

    if 'reply' in settings['email']:
        message.add_reply(read_list(settings['email']['reply']))

    if 'recipients' in kwargs:
        for recipient in kwargs['recipients']:
            if recipient in settings['email-recipients']:
                message.add_recipient(read_list(settings['email-recipients'][recipient]))
            else:
                log.warn('Could not add recipient {}'.format(recipient))

    # Extend "Reply-To" address by email address of user
    # TODO: Maybe add current user also to _recipients_?
    #request.user.username = 'test@example.org'; request.user.fullname = 'Hello World'   # debugging
    if request.user.username:
        username = request.user.username
        if validate_email(username):
            if request.user.fullname:
                pair = (request.user.fullname, username)
            else:
                pair = (None, username)
            try:
                reply_to = formataddr(pair)
                message.add_reply(reply_to)
            except Exception as ex:
                log.warning('Computing "reply_to" failed: Could not decode email address from "{}": {}'.format(username, ex))
        else:
            log.warning('Computing "reply_to" failed: Email address "{}" is invalid'.format(username))

    return message


def email_issue_report(report, recipients):

    recipients = to_list(recipients)

    identifier = None
    if isinstance(report, SmartBunch):
        identifier = report.meta.id

    # Build reasonable subject
    subject = u'Product issue'
    if 'dialog' in report and 'what' in report.dialog:
        subject = u'[{}] '.format(report.dialog.what) + subject
    if identifier:
        subject += u' #' + identifier

    # Build reasonable message
    message = u''
    if 'dialog' in report and 'remark' in report.dialog:
        message = report.dialog.remark

    # Add JSON report as attachment
    files = {u'report.json': report.pretty()}

    email = message_factory(recipients=recipients)
    email.send(
        subject     = subject,
        message     = message,
        files       = files
    )

