import asyncio

from weather.core.geo import _get_nominatim_http_client
from weather.core.settings import Settings
from weather.core.settings import get_settings


def test_user_agent_setting_can_be_configured_from_environment(monkeypatch):
  monkeypatch.setenv('OREMI_WEATHER_USER_AGENT', 'custom-weather-agent/1.0')

  settings = Settings()

  assert settings.user_agent == 'custom-weather-agent/1.0'


def test_nominatim_http_client_uses_configured_user_agent(monkeypatch):
  monkeypatch.setenv('OREMI_WEATHER_USER_AGENT', 'custom-weather-agent/2.0')
  get_settings.cache_clear()
  _get_nominatim_http_client.cache_clear()

  client = None
  try:
    client = _get_nominatim_http_client()

    assert client.headers['User-Agent'] == 'custom-weather-agent/2.0'
  finally:
    if client is not None:
      asyncio.run(client.aclose())
    _get_nominatim_http_client.cache_clear()
    get_settings.cache_clear()
