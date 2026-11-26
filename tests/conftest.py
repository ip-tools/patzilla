# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
Configure and bootstrap the test harness.

The most important topics are:

a) bringing up an application environment at runtime.
b) configuring the application object cache at runtime.
"""
import logging
import os

import pytest

from patzilla.boot.cache import configure_cache_backend, get_cache_directory
from patzilla.boot.config import BootConfiguration
from patzilla.boot.framework import setup_environment

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def app_environment():
    """
    Provide and configure an application environment at runtime, a minimal application flavor.
    """
    return setup_environment(bootconfiguration=BootConfiguration(flavor="minimal", datasources=["ops", "ificlaims"]))


@pytest.fixture(scope="session")
def ops_client(app_environment):
    """
    Provide an EPO OPS client, using credentials from environment variables.
    """
    client = app_environment["state"].client("ops")
    if client is None:
        pytest.skip("No OPS credentials provided")
    return client


@pytest.fixture(scope="session")
def web_environment():
    """
    Provide and configure an application environment at runtime, this time the full web application flavor.
    """
    return setup_environment(bootconfiguration=BootConfiguration(flavor="web", datasources=["ops", "ificlaims"]))


WEB_CONFIGURATION = """
[ip_navigator]
vendors = patzilla
datasources = ops, depatisnet, espacenet
development_mode = true

[vendor:patzilla]
organization = PatZilla
productname = PatZilla IP Navigator
productname_html = <span class="header-logo">PatZilla</span>
page_title = Patent search
copyright_html = &copy; The PatZilla Developers
stylesheet_uri = /static/patzilla.css

[auth]
magic_link_enabled = true
magic_link_allow_signup = true
log_magic_link_in_dev = true

[smtp]
hostname = {smtp_hostname}

[email_addressbook]
support = support@example.org
purchase = purchase@example.org

[filter:prefix-middleware]
use = egg:PasteDeploy#prefix

[app:main]
use = egg:patzilla#web
filter-with = prefix-middleware
mongodb.patzilla.uri = mongodb://localhost:27017/patzilla_testing
cache.regions = search, static
cache.search.type = memory
cache.search.expire = 7200
cache.static.type = memory
cache.static.expire = 2592000

[server:main]
host = 127.0.0.1
port = 6543
threads = 8
"""


@pytest.fixture
def web_configfile(tmp_path):
    path = tmp_path / "patzilla.ini"
    path.write_text(WEB_CONFIGURATION)
    return str(path)


@pytest.fixture
def web_app(web_configfile):
    from patzilla.web.app import create_app
    from patzilla.web.settings import WebSettings
    return create_app(WebSettings.from_ini(web_configfile))


@pytest.fixture
def web_client(web_app):
    """A test client for the web application, running its lifespan."""
    from fastapi.testclient import TestClient
    with TestClient(web_app, base_url="http://patzilla.example.org") as client:
        yield client


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
                           Default: `${platformdirs.user_cache_dir}/patzilla/cache`

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
