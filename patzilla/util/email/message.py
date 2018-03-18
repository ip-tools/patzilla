# -*- coding: utf-8 -*-
# (c) 2007-2018 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import time
import json
import jinja2
import logging
import textwrap
from copy import deepcopy
from core import build_email, send_email
from patzilla.util.config import read_config, to_list

log = logging.getLogger(__name__)

class EmailMessage(object):

    def __init__(self, smtp_settings, email_settings, options=None):
        self.smtp_settings  = dict(smtp_settings)
        self.email_settings = dict(email_settings)
        self.email_settings.setdefault('addressbook', {})
        self.email_settings.setdefault('content', {})
        self.options = options and dict(options) or {}
        self.recipients = []
        self.reply_to = []

        # Merge some settings from options into regular ones
        if 'subject_prefix' in self.options:
            self.email_settings['content']['subject_prefix'] = self.options['subject_prefix']
        if 'signature' in self.options:
            self.email_settings['content']['signature'] = self.options['signature']

    def add_recipient(self, address):
        for address in to_list(address):
            self.recipients.append(address)

    def add_reply(self, address):
        for address in to_list(address):
            self.reply_to.append(address)

    def send(self, subject='', message='', files=None):

        recipients = u', '.join(self.recipients)
        reply_to = u', '.join(self.reply_to)
        files = files or {}

        # get smtp addressing information from settings
        smtp_host = self.smtp_settings.get('hostname', u'localhost')
        mail_from = self.email_settings['addressbook'].get('from', u'test@example.org')

        # log smtp settings
        smtp_settings_log = deepcopy(self.smtp_settings)
        if 'password' in smtp_settings_log:
            del smtp_settings_log['password']
        log.info(u'Sending email to "{recipients}". smtp settings: {smtp_settings}'.format(
            recipients=recipients, smtp_settings=smtp_settings_log))

        # build subject
        event_date = time.strftime('%Y-%m-%d')
        event_time = time.strftime('%H:%M:%S')
        subject_real = u''
        if 'subject_prefix' in self.email_settings['content']:
            prefix = self.email_settings['content'].get('subject_prefix')
            if not prefix.endswith(' '):
                prefix += ' '
            subject_real += prefix

        #subject_real += u'{subject} on {event_date} at {event_time}'.format(**locals())
        subject_real += u'{}'.format(subject)

        filenames = u'\n'.join([u'- ' + entry for entry in files.keys()])

        body_template = textwrap.dedent(self.email_settings['content'].get('body', '')).strip()

        if 'signature' in self.email_settings['content']:
            body_template += u'\n\n--\n' + textwrap.dedent(self.email_settings['content']['signature']).strip()

        body_template = body_template.replace('\\n', '\r')

        tplvars = deepcopy(locals())
        del tplvars['self']
        body = jinja2.Template(body_template).render(**tplvars).strip()

        # debugging
        #print body
        #print('from:', mail_from)
        #print('recipients:', self.recipients)

        try:
            message = build_email(
                recipients,
                subject=subject_real, body_text=body,
                mail_from=mail_from, reply_to=reply_to,
                attachments=files)

            # TODO: catch exceptions when sending emails, e.g.::
            #
            #   smtplib.SMTPServerDisconnected: Connection unexpectedly closed
            #
            send_email(recipients, message, smtp_settings=self.smtp_settings, mail_from=mail_from)
            log.info(u'Email to recipients "{recipients}" sent successfully'.format(recipients=recipients))

        except Exception as ex:
            # TODO: catch traceback when running in commandline mode
            log.error(u'Error sending email: {failure}'.format(failure=ex))
            raise


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    settings = read_config('development.ini')

    signature = """
    ACME Corp.
    Example South 78
    12345 Somewhere

    Email: example@example.com
    Web: example.com
"""

    #message = EmailMessage(settings['smtp'], settings['email'], {'subject_prefix': 'acme-product', 'signature': signature})
    message = EmailMessage(settings['smtp'], settings['email'], {'subject_prefix': 'acme-product'})
    message.add_recipient('test@example.org')
    message.send(
        subject     = u'Self-test email from Räuber Hotzenplotz',
        message     = u'Self-test email from Räuber Hotzenplotz',
        files       = {
            u'test.txt':  u'☠☠☠ SKULL AND CROSSBONES ☠☠☠',
            u'test.json': json.dumps(u'☠☠☠ SKULL AND CROSSBONES ☠☠☠'),
            }
    )
