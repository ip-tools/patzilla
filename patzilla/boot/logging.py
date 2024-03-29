# -*- coding: utf-8 -*-
# (c) 2017-2022 Andreas Motl <andreas.motl@ip-tools.org>
from __future__ import absolute_import

import socket
import sys
import logging
import warnings


def boot_logging(options=None):
    log_level = logging.INFO
    if options and (options.get('--debug', False) or options.get('debug', False)):
        log_level = logging.DEBUG
    setup_logging(level=log_level)


def setup_logging(level=logging.INFO):
    #log_format = '%(asctime)-15s [%(name)-25s] %(levelname)-7s: %(message)s'
    log_format = '%(asctime)s %(levelname)-8.8s [%(name)-40s] %(message)s'
    logging.basicConfig(
        format=log_format,
        stream=sys.stderr,
        level=level)


def suppress_warnings():
    """
    Silence specific warnings and log messages.

    - CryptographyDeprecationWarning: Python 2 is no longer supported by the Python core team.
                                      Support for it is now deprecated in cryptography, and will be removed in the next release.
    - WARNING  [waitress.queue]  Task queue depth is X
    """

    # Silence warnings about Python 2 deprecation.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=Warning, message="Python 2 is no longer supported")
        import cryptography

    # Make waitress logging more silent on developer workstations.
    if "sink" in socket.gethostname():
        logging.getLogger("waitress.queue").setLevel(logging.ERROR)
