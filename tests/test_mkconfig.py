from configparser import ConfigParser

import pytest

from patzilla.config import get_configuration


@pytest.mark.parametrize("kind", ["development", "production"])
def test_mkconfig(kind):
    """
    Proof that `patzilla make-config` works as intended.
    """
    config_payload = get_configuration(kind)
    assert "PatZilla application configuration ({})".format(kind) in config_payload

    config = ConfigParser()
    config.read_string(string=config_payload, source="{}.ini".format(kind))
    assert config.get("main", "include") == "vendors.ini"
    assert config.get("ip_navigator", "vendors") == "patzilla"
    assert config.get("ip_navigator", "datasources") == "ops, depatisnet"
    assert config.get("vendor:patzilla", "organization") == "PatZilla"
    assert config.get("datasource:ops", "api_consumer_key") == "{ops_api_consumer_key}"
    assert config.get("smtp", "hostname") == "{smtp_hostname}"

    expected_keys = ['main', 'ip_navigator', 'vendor:patzilla', 'datasource:ops', 'datasource:depatisconnect',
                     'datasource:ificlaims', 'datasource:depatech', 'smtp', 'email_addressbook', 'email_content']
    effective_keys = config._sections.keys()

    for expected_key in expected_keys:
        assert expected_key in effective_keys
