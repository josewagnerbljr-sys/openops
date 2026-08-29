import json
import os

import pytest

from openops_core.config import OpenOpsConfig, load_config, ConfigError


def test_defaults_when_nothing_provided():
    config = load_config()
    assert config.environment == "development"
    assert config.log_level == "INFO"
    assert config.database_url is None


def test_loads_from_file(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"environment": "staging", "log_level": "DEBUG"}))

    config = load_config(config_file)

    assert config.environment == "staging"
    assert config.log_level == "DEBUG"


def test_env_vars_override_file(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"environment": "staging"}))
    monkeypatch.setenv("OPENOPS_ENVIRONMENT", "production")

    config = load_config(config_file)

    assert config.environment == "production"


def test_unknown_keys_go_to_extra(monkeypatch):
    monkeypatch.setenv("OPENOPS_CUSTOM_PLUGIN_FLAG", "true")

    config = load_config()

    assert config.extra["custom_plugin_flag"] == "true"


def test_invalid_json_raises_config_error(tmp_path):
    config_file = tmp_path / "broken.json"
    config_file.write_text("{ not valid json")

    with pytest.raises(ConfigError):
        load_config(config_file)


def test_config_is_immutable():
    config = OpenOpsConfig()
    with pytest.raises(Exception):
        config.environment = "production"  # type: ignore[misc]
