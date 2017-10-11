# -*- coding: utf-8 -*-
# (c) 2014-2017 Andreas Motl, Elmyra UG
import logging
import logging.config
from pyramid.events import ContextFound
from pyramid.paster import bootstrap

logger = logging.getLogger(__name__)

def setup_commandline_pyramid(configfile):

    # http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/commandline.html#writing-a-script
    # https://stackoverflow.com/questions/6206556/running-scripts-within-pyramid-framework-ie-without-a-server
    # https://stackoverflow.com/questions/12510133/share-pyramid-configuration-with-a-cli-script

    # Setup logging, manually
    logging.config.fileConfig(configfile)
    logger.setLevel(logging.DEBUG)

    # Bootstrap a Pyramid script
    # http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/commandline.html#writing-a-script
    env = bootstrap(configfile)

    # Get request and registry objects from environment
    request = env['request']
    registry = env['registry']

    # Run event subscriptions to attach data source client pool objects to request object
    event = ContextFound(request)
    registry.notify(event)

    return env
