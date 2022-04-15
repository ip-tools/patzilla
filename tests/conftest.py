# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import warnings

import pytest

from patzilla.util.cache.backend import configure_cache_backend, get_cache_directory

logger = logging.getLogger(__name__)


def suppress_warnings():
    """
    Silence specific warnings.

    - DeprecationWarning: Importing from numpy.testing.nosetester is deprecated since 1.15.0, import from numpy.testing instead.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        import pandas.util.nosetester


suppress_warnings()


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


@pytest.fixture(scope='session', autouse=True)
def enable_app_cache_backend(pyt_options):
    """
    Enable application object cache through a session-wide fixture.
    """
    logger.info("Enabling application object cache backend: {}".format(pyt_options.cache_backend))
    configure_cache_backend(pyt_options.cache_backend, cache_directory=pyt_options.cache_directory, clear_cache=pyt_options.cache_clear)


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
