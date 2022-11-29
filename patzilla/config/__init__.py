# -*- coding: utf-8 -*-
# (c) 2017 Andreas Motl <andreas@ip-tools.org>
import pkg_resources
import six


def get_configuration(kind):
    configfile = '{kind}.ini.tpl'.format(kind=kind)
    with pkg_resources.resource_stream('patzilla.config', configfile) as stream:
        return six.ensure_text(stream.read())
