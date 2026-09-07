import pytest

from app.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_blank_env_var_falls_back_to_the_default(monkeypatch):
    """A variable saved with an empty value must not take the app down."""
    monkeypatch.setenv("DEMO_DAILY_LIMIT", "")
    assert Settings().demo_daily_limit == 3


def test_blank_string_field_also_falls_back(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "")
    assert Settings().cors_origins == "http://localhost:3000"


def test_a_real_value_still_wins(monkeypatch):
    monkeypatch.setenv("DEMO_DAILY_LIMIT", "10")
    assert Settings().demo_daily_limit == 10


def test_cors_origins_are_split_and_trimmed(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example , https://b.example")
    assert Settings().cors_origin_list == ["https://a.example", "https://b.example"]
