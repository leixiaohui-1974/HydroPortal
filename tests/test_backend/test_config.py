import importlib

import pytest

from backend import config as config_module


@pytest.fixture
def reloaded_config(monkeypatch):
    def _reload(env: dict[str, str | None]):
        for key, value in env.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)
        return importlib.reload(config_module)

    yield _reload
    importlib.reload(config_module)


def test_demo_auth_defaults_to_enabled_in_development(reloaded_config):
    config = reloaded_config(
        {
            "HYDROPORTAL_ENV": "development",
            "HYDROPORTAL_DEMO_AUTH_ENABLED": None,
            "HYDROPORTAL_ALLOW_DEMO_AUTH_IN_PRODUCTION": None,
            "HYDROPORTAL_JWT_SECRET": None,
        }
    )

    assert config.IS_PRODUCTION is False
    assert config.DEMO_AUTH_ENABLED is True


def test_demo_auth_defaults_to_disabled_in_production(reloaded_config):
    config = reloaded_config(
        {
            "HYDROPORTAL_ENV": "production",
            "HYDROPORTAL_DEMO_AUTH_ENABLED": None,
            "HYDROPORTAL_ALLOW_DEMO_AUTH_IN_PRODUCTION": None,
            "HYDROPORTAL_JWT_SECRET": "non-default-secret",
        }
    )

    assert config.IS_PRODUCTION is True
    assert config.DEMO_AUTH_ENABLED is False
    config.validate_security_settings()


def test_production_demo_auth_override_requires_explicit_allow(reloaded_config):
    config = reloaded_config(
        {
            "HYDROPORTAL_ENV": "production",
            "HYDROPORTAL_DEMO_AUTH_ENABLED": "true",
            "HYDROPORTAL_ALLOW_DEMO_AUTH_IN_PRODUCTION": "true",
            "HYDROPORTAL_JWT_SECRET": "non-default-secret",
        }
    )

    assert config.IS_PRODUCTION is True
    assert config.DEMO_AUTH_ENABLED is True
    assert config.ALLOW_DEMO_AUTH_IN_PRODUCTION is True
    config.validate_security_settings()
