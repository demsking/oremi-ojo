# Copyright 2026 Sébastien Demanou. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import asyncio

from ojo.core.geo import _get_nominatim_http_client
from ojo.core.settings import get_settings
from ojo.core.settings import Settings
from ojo.providers.OpenMeteoProvider import OpenMeteoProvider
from ojo.services.air_quality_service import AirQualityService
from ojo.services.forecast_service import ForecastService
from ojo.services.pollen_service import PollenService


def test_user_agent_setting_can_be_configured_from_environment(monkeypatch):
  monkeypatch.setenv('OREMI_OJO_HTTP_USER_AGENT', 'custom-weather-agent/1.0')

  settings = Settings()

  assert settings.http_user_agent == 'custom-weather-agent/1.0'


def test_http_cache_ttl_can_be_configured_from_environment(monkeypatch):
  monkeypatch.setenv('OREMI_OJO_HTTP_CACHE_TTL_SECONDS', '1800.0')

  settings = Settings()

  assert settings.http_cache_ttl_seconds == 1800.0


def test_openmeteo_provider_uses_configured_requests_cache_expire_after():
  provider = OpenMeteoProvider(Settings(http_cache_ttl_seconds=1800.0))

  assert provider.client.__dict__['_session'].settings.expire_after == 1800.0


def test_openmeteo_services_share_one_client_and_cache_session():
  provider = OpenMeteoProvider(Settings(http_cache_ttl_seconds=1800.0))

  forecast_service = ForecastService(provider)
  air_quality_service = AirQualityService(provider)
  pollen_service = PollenService(provider)

  assert forecast_service.provider.client is air_quality_service.provider.client
  assert forecast_service.provider.client is pollen_service.provider.client
  assert forecast_service.provider.client.__dict__['_session'] is air_quality_service.provider.client.__dict__['_session']
  assert forecast_service.provider.client.__dict__['_session'] is pollen_service.provider.client.__dict__['_session']


def test_nominatim_http_client_uses_configured_user_agent(monkeypatch):
  monkeypatch.setenv('OREMI_OJO_HTTP_USER_AGENT', 'custom-weather-agent/2.0')
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
