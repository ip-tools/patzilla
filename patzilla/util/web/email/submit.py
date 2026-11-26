# -*- coding: utf-8 -*-
# (c) 2016-2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import logging
from email.utils import formataddr
from validate_email import validate_email
from patzilla.util.config import read_config, read_list, to_list
from patzilla.util.data.container import SmartMunch
from patzilla.util.email.message import EmailMessage

log = logging.getLogger(__name__)


def message_factory(smtp_settings, vendor, user, **kwargs):

    # EmailMessage builder
    message = EmailMessage(smtp_settings, vendor.email)

    if 'reply' in vendor.email.addressbook:
        message.add_reply(read_list(vendor.email.addressbook.reply))

    is_support_email = False
    if 'recipients' in kwargs:
        for recipient in kwargs['recipients']:
            if recipient == 'support':
                is_support_email = True
            if recipient in vendor.email.addressbook:
                message.add_recipient(read_list(vendor.email.addressbook[recipient]))
            else:
                log.warning('Could not add recipient {}'.format(recipient))

    # Extend "To" and "Reply-To" addresses by email address of user
    if user is not None and user.username:
        username = user.username
        if validate_email(username):
            if user.fullname:
                pair = (user.fullname, username)
            else:
                pair = (None, username)

            try:
                user_email = formataddr(pair)
            except Exception as ex:
                log.warning('Computing "user_email" failed: Could not decode email address from "{}": {}'.format(username, ex))
                return message

            # Add user email as "Reply-To" address
            message.add_reply(user_email)

            # If it's a support email, also add user herself as a recipient
            if is_support_email:
                message.add_recipient(user_email)

        else:
            log.warning('Computing "user_email" failed: Email address "{}" is invalid'.format(username))

    return message


def email_issue_report(report, recipients, smtp_settings, vendor, user):

    recipients = to_list(recipients)

    identifier = None
    if isinstance(report, SmartMunch):
        identifier = report.meta.id

    # Build reasonable subject
    subject = 'Product issue'
    if 'dialog' in report and 'what' in report.dialog:
        subject = '[{}] '.format(report.dialog.what) + subject
    if identifier:
        subject += ' #' + identifier

    # Build reasonable message
    message = ''
    if 'dialog' in report and 'remark' in report.dialog:
        message = report.dialog.remark

    # Add JSON report as attachment
    files = {'report.json': report.pretty()}

    email = message_factory(smtp_settings, vendor, user, recipients=recipients)
    email.send(
        subject     = subject,
        message     = message,
        files       = files
    )

