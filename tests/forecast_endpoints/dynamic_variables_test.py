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
import pytest

import numpy as np

from ojo.services.air_quality_service import AirQualityService
from ojo.services.forecast_service import ForecastService
from ojo.services.pollen_service import PollenService


class DummyController:
  def __init__(self):
    self.name = 'OpenMétéo'


class DummyProvider:
  def __init__(self, client):
    self.name = 'OpenMétéo'
    self.client = client


def test_format_unix_time_applies_utc_offset():
  assert ForecastService.format_unix_time(0, 3600) == '01:00:00'


class FakeOpenMeteoVariable:
  def __init__(self, value, unit=0):
    self.value = value
    self.unit = unit

  def ValuesInt64AsNumpy(self):
    return np.array([self.value], dtype=np.int64)

  def ValuesAsNumpy(self):
    return np.array([self.value])

  def ValuesLength(self):
    return 1

  def Unit(self):
    return self.unit


class FakeOpenMeteoDaily:
  def __init__(self, values):
    self.values = values

  def Variables(self, index):
    return FakeOpenMeteoVariable(self.values[index])

  def VariablesLength(self):
    return len(self.values)

  def Time(self):
    return int(datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

  def Interval(self):
    return 86400


class FakeOpenMeteoResponse:
  def __init__(self, values, utc_offset_seconds):
    self.values = values
    self.utc_offset_seconds = utc_offset_seconds

  def Daily(self):
    return FakeOpenMeteoDaily(self.values)

  def Hourly(self):
    return FakeOpenMeteoDaily(self.values)

  def UtcOffsetSeconds(self):
    return self.utc_offset_seconds


class FakeOpenMeteoClient:
  def __init__(self):
    self.params = None

  def weather_api(self, url, params):
    self.params = params
    return [FakeOpenMeteoResponse([0, 3600, 23], utc_offset_seconds=3600)]


class FakeOpenMeteoCurrentVariable:
  def __init__(self, value, unit):
    self.value = value
    self.unit = unit

  def Value(self):
    return self.value

  def Unit(self):
    return self.unit


class FakeOpenMeteoCurrent:
  def __init__(self, variables):
    self.variables = variables

  def Variables(self, index):
    return self.variables[index]


class FakeOpenMeteoCurrentResponse:
  def __init__(self, variables):
    self.variables = variables

  def Current(self):
    return FakeOpenMeteoCurrent(self.variables)


class FakeOpenMeteoCurrentClient:
  def __init__(self, variables):
    self.variables = variables
    self.params = None

  def weather_api(self, url, params):
    self.params = params
    return [FakeOpenMeteoCurrentResponse(self.variables)]


@pytest.mark.asyncio
async def test_fetch_formats_sun_times_as_local_clock_values():
  client = FakeOpenMeteoClient()
  provider = ForecastService(DummyProvider(client))  # type: ignore[arg-type]

  res = await provider.fetch(
    lon=2.3483915,
    lat=48.8534951,
    timezone='Europe/Paris',
    temperature_unit='celsius',
    daily_variables=['sunrise', 'sunset'],
  )

  assert res.sunrise == '01:00:00'
  assert res.sunset == '02:00:00'


@pytest.mark.asyncio
async def test_forecast_service_dynamic_variables():
  provider = ForecastService(
    DummyProvider(
      FakeOpenMeteoClient(),
    )
  )  # type: ignore[arg-type]

  # Test hourly fetch with specific variables (apparent_temperature, relative_humidity_2m)
  res = await provider.fetch(
    lon=2.3483915,
    lat=48.8534951,
    timezone='Europe/Paris',
    temperature_unit='celsius',
    hourly_variables=['apparent_temperature', 'relative_humidity_2m'],
    daily_variables=['sunrise'],
  )

  # Check that requested variables are present in the response
  assert res.humidity is not None
  assert hasattr(res, 'apparent_temperature')
  assert getattr(res, 'apparent_temperature') is not None
  assert res.sunrise is not None
  # wind_speed was not requested so it shouldn't be present
  assert res.wind_speed is None


@pytest.mark.asyncio
async def test_air_quality_service_dynamic_variables():
  provider = AirQualityService(
    DummyProvider(
      FakeOpenMeteoCurrentClient(
        [
          FakeOpenMeteoCurrentVariable(12.5, 30),
          FakeOpenMeteoCurrentVariable(42, 8),
          FakeOpenMeteoCurrentVariable(50, 38),
        ]
      )
    )
  )  # type: ignore[arg-type]

  # Test fetch with specific variable (pm2_5)
  res = await provider.fetch(lon=2.3483915, lat=48.8534951, variables=['pm2_5'])

  assert res.value is not None
  assert res.level is not None
  assert hasattr(res, 'pm2_5')
  assert getattr(res, 'pm2_5') is not None
  # pm10 was not requested so it shouldn't be present
  assert not hasattr(res, 'pm10')


@pytest.mark.asyncio
async def test_pollen_service_uses_openmeteo_current_values():
  provider = PollenService(
    DummyProvider(
      FakeOpenMeteoCurrentClient(
        [
          FakeOpenMeteoCurrentVariable(0, 14),
          FakeOpenMeteoCurrentVariable(5, 14),
          FakeOpenMeteoCurrentVariable(12, 14),
          FakeOpenMeteoCurrentVariable(0, 14),
          FakeOpenMeteoCurrentVariable(1, 14),
          FakeOpenMeteoCurrentVariable(0, 14),
        ]
      )
    )
  )  # type: ignore[arg-type]

  res = await provider.fetch(lon=2.3483915, lat=48.8534951)

  assert res.dominant_pollen == 'grass'
  assert res.units == 'grains/m³'
  assert res.pollen_names == ['birch', 'grass', 'olive']
  assert res.details['grass'].level == 12
