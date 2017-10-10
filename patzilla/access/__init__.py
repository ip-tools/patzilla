# -*- coding: utf-8 -*-
# (c) 2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
from ConfigParser import NoOptionError

def includeme(config):

    try:
        datasources = config.registry.application_settings.ip_navigator.datasources
    except:
        raise NoOptionError('datasources', 'ip_navigator')

    if 'ops' in datasources:
        config.include("patzilla.access.epo.ops.client")

    if 'depatisconnect' in datasources:
        config.include("patzilla.access.dpma.depatisconnect")

    if 'ificlaims' in datasources:
        config.include("patzilla.access.ificlaims.clientpool")

    if 'depatech' in datasources:
        config.include("patzilla.access.depatech.clientpool")

    config.include('.office')
    config.scan()
