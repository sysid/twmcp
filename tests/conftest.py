from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_CONFIG = FIXTURES_DIR / "sample_config.toml"
SAMPLE_CONFIG_OVERRIDES = FIXTURES_DIR / "sample_config_with_overrides.toml"
SAMPLE_CONFIG_PROFILES = FIXTURES_DIR / "sample_config_with_profiles.toml"
SAMPLE_SECRETS = FIXTURES_DIR / "secrets.env"
EXPECTED_DIR = FIXTURES_DIR / "expected"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def sample_config_path():
    return SAMPLE_CONFIG


@pytest.fixture
def sample_config_overrides_path():
    return SAMPLE_CONFIG_OVERRIDES


@pytest.fixture
def sample_config_profiles_path():
    return SAMPLE_CONFIG_PROFILES


@pytest.fixture
def sample_secrets_path():
    return SAMPLE_SECRETS


@pytest.fixture
def expected_dir():
    return EXPECTED_DIR


@pytest.fixture
def sample_config_text():
    return SAMPLE_CONFIG.read_text()
