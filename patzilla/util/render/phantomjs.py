# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import logging
import shlex
import subprocess
from tempfile import NamedTemporaryFile
from pkg_resources import resource_filename

log = logging.getLogger(__name__)

rasterize_js = resource_filename(__name__, 'phantomjs_rasterize.js')


def render_pdf(url):
    tmpfile = NamedTemporaryFile(suffix='.pdf')
    pdf = tmpfile.name
    command = "phantomjs --ignore-ssl-errors=true {rasterize_js} '{url}' {pdf} A4".format(rasterize_js=rasterize_js, url=url, pdf=pdf)
    log.info('Rendering PDF: ' + command)
    subprocess.check_call(shlex.split(command))
    tmpfile.seek(0)
    return tmpfile.read()
