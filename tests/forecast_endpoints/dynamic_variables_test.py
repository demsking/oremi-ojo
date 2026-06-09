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
import datetime
import logging
import pytest

from server.core.controller import Controller
from server.providers.OpenMeteoForecastProvider import OpenMeteoForecastProvider
from server.providers.OpenMeteoAirQualityProvider import OpenMeteoAirQualityProvider


class DummyController:
  def __init__(self):
    pass


@pytest.mark.asyncio
async def test_forecast_provider_dynamic_variables():
  logger = logging.getLogger("test")
  controller = DummyController()
  provider = OpenMeteoForecastProvider(controller, logger) # type: ignore

  # Test hourly fetch with specific variables (apparent_temperature, relative_humidity_2m)
  res = await provider.fetch(
    lon=2.3483915,
    lat=48.8534951,
    timezone="Europe/Paris",
    temperature_unit="celsius",
    hourly_variables=["apparent_temperature", "relative_humidity_2m"],
    daily_variables=["sunrise"]
  )

  # Check that requested variables are present in the response
  assert res.humidity is not None
  assert hasattr(res, "apparent_temperature")
  assert getattr(res, "apparent_temperature") is not None
  assert res.sunrise is not None
  # wind_speed was not requested so it shouldn't be present
  assert res.wind_speed is None

  # Test daily fetch with specific variables (apparent_temperature_max, weather_code)
  now = datetime.datetime.now()
  dateinfo = Controller.DateInfo(
    period="daily",
    start=now,
    end=now,
    timezone="Europe/Paris"
  )
  res_daily = await provider.fetch_daily(
    lon=2.3483915,
    lat=48.8534951,
    dateinfo=dateinfo,
    temperature_unit="celsius",
    daily_variables=["apparent_temperature_max", "weather_code"]
  )

  assert res_daily.weather_code is not None
  assert hasattr(res_daily, "apparent_temperature_max")
  assert getattr(res_daily, "apparent_temperature_max") is not None
  # rain_sum was not requested so it shouldn't be present
  assert res_daily.rain_sum is None


@pytest.mark.asyncio
async def test_air_quality_provider_dynamic_variables():
  logger = logging.getLogger("test")
  controller = DummyController()
  provider = OpenMeteoAirQualityProvider(controller, logger) # type: ignore

  # Test fetch with specific variable (pm2_5)
  res = await provider.fetch(
    lon=2.3483915,
    lat=48.8534951,
    variables=["pm2_5"]
  )

  assert res.value is not None
  assert res.level is not None
  assert hasattr(res, "pm2_5")
  assert getattr(res, "pm2_5") is not None
  # pm10 was not requested so it shouldn't be present
  assert not hasattr(res, "pm10")
