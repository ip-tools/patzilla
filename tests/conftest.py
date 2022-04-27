# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
Configure and bootstrap the test harness.

The most important topics are:

a) bringing up a Pyramid environment at runtime.
b) configuring the application object cache at runtime.
"""
import logging
import os

import pytest
from pyramid.events import ContextFound, NewRequest

from patzilla.boot.cache import configure_cache_backend, get_cache_directory
from patzilla.boot.config import BootConfiguration
from patzilla.boot.framework import setup_pyramid

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def app_environment():
    """
    Provide and configure a Pyramid environment at runtime, a minimal application flavor.
    """
    return setup_pyramid(bootconfiguration=BootConfiguration(flavor="minimal", datasources=["ops"]))


@pytest.fixture(scope="function")
def app_request(app_environment):

    env = app_environment

    # Get request and registry objects from environment.
    request = env['request']
    registry = env['registry']

    # Run event subscriptions to attach data source client pool objects to request object.
    # FIXME: It will be crucial to invoke all event types, in order emulate
    #        Pyramid's application behaviour thoroughly.
    event = ContextFound(request)
    registry.notify(event)

    event = NewRequest(request)
    registry.notify(event)
    del request.errors[:]

    return request


@pytest.fixture(scope="session")
def web_environment():
    """
    Provide and configure a Pyramid environment at runtime, this time the full web application flavor.
    """
    return setup_pyramid(bootconfiguration=BootConfiguration(flavor="web", datasources=["ops"]))


@pytest.fixture(scope='session', autouse=True)
def enable_app_cache_backend(pyt_options):
    """
    Enable application object cache through a session-wide fixture.
    """
    logger.info("Enabling application object cache backend: {}".format(pyt_options.cache_backend))
    configure_cache_backend(pyt_options.cache_backend, cache_directory=pyt_options.cache_directory, clear_cache=pyt_options.cache_clear)


class PytestOptionWrapper:
    """
    Wrap custom pytest options for easier read access.
    Also provide sensible default values here.
    """

    def __init__(self, config):
        self.config = config

    @property
    def cache_backend(self):
        return self.config.getoption("--app-cache-backend") or "memory"

    @property
    def cache_directory(self):
        return self.config.getoption("--app-cache-directory")

    @property
    def cache_clear(self):
        return self.config.getoption("--app-cache-clear") or False


@pytest.fixture(scope="session")
def pyt_options(request):
    """
    Fixture for providing a PytestOptionWrapper instance.
    """
    return PytestOptionWrapper(request.config)


def pytest_addoption(parser):
    """
    Add custom options to pytest.


    1. Application object cache options

    --app-cache-backend:   Choose application cache backend (memory, filesystem).
                           Default: memory.

    --app-cache-directory: Choose application cache directory (when `filesystem` is selected).
                           Default: `${appdirs.user_cache_dir}/patzilla/cache`

    --app-cache-clear:     Clear the application cache before invoking the test suite.
                           Default: false.

    """
    parser.addoption("--app-cache-backend", type=str, required=False, default="memory",
                     help="Choose application cache backend (memory, filesystem)")
    parser.addoption("--app-cache-directory", type=str, required=False, default=get_cache_directory(testing=True),
                     help="Choose application cache directory (when `filesystem` is selected)")
    parser.addoption("--app-cache-clear", action="store_true", default=False,
                     help="Clear the application cache before invoking the test suite")


def pytest_report_header(config):
    """
    Report about application object cache settings at the beginning of the test suite run.
    """
    options = PytestOptionWrapper(config)
    lines = [
        "app-cache-backend:   {}".format(options.cache_backend),
        "app-cache-directory: {}".format(options.cache_directory),
        "app-cache-clear:     {}".format(options.cache_clear),
    ]
    return lines


# When running software tests, mask specific environment variables.
if "PATZILLA_CONFIG" in os.environ:
    del os.environ["PATZILLA_CONFIG"]
