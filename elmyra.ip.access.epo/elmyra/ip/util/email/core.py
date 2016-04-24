# -*- coding: utf-8 -*-
# (c) 2007-2016 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import logging
import smtplib
import mimetypes
from email import encoders
from email.utils import formataddr
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email._parseaddr import AddressList

log = logging.getLogger(__name__)


def build_email(mail_to, subject, body_text, mail_from=u'test@example.org', reply_to=None, attachments=None, mime_headers=None):
    """
    Flexible Multipart MIME message builder.

    Implements message building using the "email" Python standard library
    https://docs.python.org/2/library/email-examples.html

    while following recommendations from
    https://stackoverflow.com/questions/3902455/smtp-multipart-alternative-vs-multipart-mixed

    .. seealso::

        - http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52243
        - http://mail.python.org/pipermail/tutor/1999-June/000259.html
        - http://www.bigbold.com/snippets/posts/show/2038
    """
    attachments = attachments or {}
    mime_headers = mime_headers or {}


    # ------------------------------------------
    #                envelope
    # ------------------------------------------

    message = MIMEMultipart('mixed')
    # TODO: Add text for non MIME-aware MUAs
    #message.preamble = 'You will not see this in a MIME-aware mail reader.\n'

    # Address headers
    address_headers = {
        'To':          fix_addresslist(AddressList(mail_to)),
        'From':        AddressList(mail_from),
        'Reply-To':    AddressList(reply_to),
    }

    # Subject header
    mime_headers.update({u'Subject': Header(s=subject, charset='utf-8')})


    # Add address headers
    for key, item in address_headers.iteritems():
        if isinstance(item, AddressList):

            # v1
            #for address in format_addresslist(item):
            #    message[key] = address

            # v2
            value = ', '.join(format_addresslist(item))
            if value:
                message[key] = value

    # Add more headers
    for key, value in mime_headers.iteritems():
        #message.add_header(key, value)
        if value:
            message[key] = value


    # ------------------------------------------
    #              email body
    # ------------------------------------------
    body_message = MIMEMultipart('alternative')

    # Start off with a text/plain part
    # https://stackoverflow.com/questions/3902455/smtp-multipart-alternative-vs-multipart-mixed
    body_part1 = MIMEText(body_text, _subtype='plain', _charset='utf-8')
    #body_part1.set_payload(body_text)
    #body_part1.set_charset('utf-8')
    body_message.attach(body_part1)
    message.attach(body_message)

    # TODO: Add a text/html part
    #body_part2 = MIMEText(body_html, 'html')


    # ------------------------------------------
    #            multipart attachments
    # ------------------------------------------
    # from https://docs.python.org/2/library/email-examples.html
    for filename, payload in attachments.iteritems():

        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.
        ctype, encoding = mimetypes.guess_type(filename, strict=False)
        #print('ctype, encoding:', ctype, encoding)

        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        #print('maintype, subtype:', maintype, subtype)

        # Create proper MIME part by maintype
        if maintype == 'application' and subtype in ['xml', 'json']:
            part = MIMENonMultipart(maintype, subtype, charset='utf-8')
            part.set_payload(payload.encode('utf-8'), 'utf-8')

        elif maintype == 'text':
            part = MIMEText(payload.encode('utf-8'), _subtype=subtype, _charset='utf-8')
            #part.set_charset('utf-8')

        elif maintype == 'image':
            part = MIMEImage(payload, _subtype=subtype)
        elif maintype == 'audio':
            part = MIMEAudio(payload, _subtype=subtype)
        else:
            part = MIMEBase(maintype, subtype)
            part.set_payload(payload)
            # Encode the payload using Base64 (Content-Transfer-Encoding)
            encoders.encode_base64(part)

        #part = MIMEBase(maintype, subtype, _charset='utf-8')
        # replace forward slashes by dashes
        filename_attachment = filename.lstrip('/\\').replace('/', '-')
        part.add_header('Content-Disposition', 'attachment', filename=filename_attachment.encode('utf-8'))
        #part.set_payload(payload.encode('utf-8'))
        #part.set_charset('utf-8')

        # Encode the payload using Base64 (Content-Transfer-Encoding)
        #encoders.encode_base64(part)

        # Add part to multipart message
        message.attach(part)

    payload = message.as_string()

    return payload


def send_email(mail_to, message, smtp_settings=None, mail_from=u'test@example.org'):

    smtp_settings = smtp_settings or {}
    smtp_settings.setdefault('hostname', u'localhost')
    smtp_settings.setdefault('port', 25)

    # sanity checks
    if not mail_to:
        raise ValueError('"mail_to" must not be empty')

    if not message:
        raise ValueError('"message" must not be empty')

    # setup mailserver session
    smtp = smtplib.SMTP(
        host=smtp_settings.get('hostname'),
        port=smtp_settings.get('port'))

    # debug smtp protocol conversation
    #pprint(smtp_settings)
    #smtp.set_debuglevel(1)

    # starttls
    if 'tls' in smtp_settings and smtp_settings['tls']:
        smtp.starttls()

    # smtp auth
    if 'username' in smtp_settings and 'password' in smtp_settings:
        smtp.login(smtp_settings['username'], smtp_settings['password'])

    # send mail, finally
    to_addrs = format_addresslist(fix_addresslist(AddressList(mail_to)))
    smtp.sendmail(mail_from, to_addrs, message)

    # exit mailserver session
    smtp.quit()

    return True


def format_addresslist(addresslist):
    #print 'addresslist:', addresslist.addresslist
    return map(formataddr, addresslist.addresslist)


def fix_addresslist(addresslist):
    """
    Microsoft Exchange does not accept "pure" email addresses like "test@example.com" for From or To fields
    Let's fix it by making up a name if required, so this will yield "test" <test@example.com>
    """
    amended = []
    for address_pair in addresslist.addresslist:
        (name, address) = address_pair
        if not name:
            name = address.split('@')[0]
        amended.append((name, address))

    addresslist.addresslist = amended

    return addresslist
