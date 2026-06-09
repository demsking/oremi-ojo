# Copyright 2024-2025 Sébastien Demanou. All Rights Reserved.
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
import datetime  # use implicit import to enable datatime mocking
import logging
from datetime import timedelta
from typing import Literal

import openmeteo_requests
import requests_cache
from retry_requests import retry

from ..core.config import CACHE_DIR
from ..core.controller import Controller
from ..core.http import HttpClient
from ..core.provider import Provider
from ..models.forecast import DailyForecastData
from ..models.forecast import Forecast
from ..models.forecast import ForecastData

TemperatureUnit = Literal['celsius', 'fahrenheit']


class OpenMeteoForecastProvider(Provider):
  format: str = '%Y-%m-%dT%H:%M'

  def __init__(self, controller: Controller, logger: logging.Logger) -> None:
    super().__init__('Open-Météo', controller, logger)
    self.client = HttpClient(
      base_url='https://api.open-meteo.com',
      expire_after=timedelta(minutes=30),
      logger=logger,
    )

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(CACHE_DIR, expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    self.openmeteo = openmeteo_requests.Client(session=retry_session)

  @staticmethod
  def get_wind_direction(wind_direction: int) -> str:
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    angle_per_direction = 360 / len(directions)
    index = round(wind_direction / angle_per_direction) % len(directions)

    return directions[index]

  async def fetch_daily(
    self,
    *,
    lon: float,
    lat: float,
    dateinfo: Controller.DateInfo,
    temperature_unit: TemperatureUnit,
    daily_variables: list[str] | None = None,
  ):
    self.logger.info(f'Fetching forecast for geo ({lon}, {lat})')

    allowed_daily = {
      'weather_code',
      'temperature_2m_max',
      'temperature_2m_min',
      'apparent_temperature_max',
      'apparent_temperature_min',
      'sunrise',
      'sunset',
      'daylight_duration',
      'sunshine_duration',
      'uv_index_max',
      'uv_index_clear_sky_max',
      'rain_sum',
      'showers_sum',
      'snowfall_sum',
      'precipitation_sum',
      'precipitation_hours',
      'precipitation_probability_max',
      'wind_speed_10m_max',
      'wind_gusts_10m_max',
      'wind_direction_10m_dominant',
      'shortwave_radiation_sum',
      'et0_fao_evapotranspiration',
    }

    if daily_variables is not None:
      daily_vars = [var for var in daily_variables if var in allowed_daily]
    else:
      daily_vars = []

    if not daily_vars:
      daily_vars = [
        'weather_code',
        'temperature_2m_max',
        'temperature_2m_min',
        'sunrise',
        'sunset',
        'rain_sum',
        'uv_index_max',
        'wind_speed_10m_max',
        'wind_direction_10m_dominant',
        'wind_gusts_10m_max',
      ]

    url = 'https://api.open-meteo.com/v1/forecast'
    params = {
      'latitude': lat,
      'longitude': lon,
      'daily': daily_vars,
      'timezone': dateinfo.timezone,
      'start_date': dateinfo.start_date,
      'end_date': dateinfo.end_date,
      'temperature_unit': temperature_unit,
    }

    responses = self.openmeteo.weather_api(url, params=params)

    # Process daily data. The order of variables needs to be the same as requested.
    daily = responses[0].Daily()
    daily_data = {}

    for i, var_name in enumerate(daily_vars):
      variable = daily.Variables(i)  # type: ignore
      if var_name in ('sunrise', 'sunset'):
        values = variable.ValuesInt64AsNumpy()  # type: ignore
      else:
        values = variable.ValuesAsNumpy()  # type: ignore

      daily_data[var_name] = values[0].item() if len(values) > 0 else None

    return DailyForecastData(**daily_data)

  async def _fetch_hourly(
    self,
    *,
    lon: float,
    lat: float,
    timezone: str | None,
    temperature_unit: TemperatureUnit,
    hourly_variables: list[str] | None = None,
    daily_variables: list[str] | None = None,
  ) -> tuple[int, int, Forecast, list[str], list[str]]:
    self.logger.info(f'Fetching forecast for geo ({lon}, {lat})')

    allowed_hourly = {
      'temperature_2m',
      'relative_humidity_2m',
      'dew_point_2m',
      'apparent_temperature',
      'precipitation_probability',
      'precipitation',
      'rain',
      'showers',
      'snowfall',
      'snow_depth',
      'snowfall_water_equivalent',
      'snow_depth_water_equivalent',
      'weather_code',
      'pressure_msl',
      'surface_pressure',
      'cloud_cover',
      'cloud_cover_low',
      'cloud_cover_mid',
      'cloud_cover_high',
      'visibility',
      'evapotranspiration',
      'et0_fao_evapotranspiration',
      'vapour_pressure_deficit',
      'runoff',
      'precipitation_type',
      'rain_probability',
      'snowfall_probability',
      'freezing_rain_probability',
      'ice_pellets_probability',
      'thunderstorm_probability',
      'wind_speed_10m',
      'wind_speed_20m',
      'wind_speed_30m',
      'wind_speed_40m',
      'wind_speed_50m',
      'wind_speed_70m',
      'wind_speed_80m',
      'wind_speed_100m',
      'wind_speed_120m',
      'wind_speed_140m',
      'wind_speed_150m',
      'wind_speed_160m',
      'wind_speed_180m',
      'wind_speed_200m',
      'wind_direction_10m',
      'wind_direction_20m',
      'wind_direction_30m',
      'wind_direction_40m',
      'wind_direction_50m',
      'wind_direction_70m',
      'wind_direction_80m',
      'wind_direction_100m',
      'wind_direction_120m',
      'wind_direction_140m',
      'wind_direction_150m',
      'wind_direction_160m',
      'wind_direction_180m',
      'wind_direction_200m',
      'wind_gusts_10m',
      'uv_index',
      'uv_index_clear_sky',
      'is_day',
      'sunshine_duration',
    }

    allowed_daily = {'sunrise', 'sunset'}

    name_mapping = {
      'relativehumidity_2m': 'relative_humidity_2m',
      'windspeed_10m': 'wind_speed_10m',
    }

    if hourly_variables is not None:
      hourly_vars = [name_mapping.get(var, var) for var in hourly_variables]
      hourly_vars = [var for var in hourly_vars if var in allowed_hourly]
    else:
      hourly_vars = []

    if not hourly_vars:
      hourly_vars = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m']

    if daily_variables is not None:
      daily_vars = [var for var in daily_variables if var in allowed_daily]
    else:
      daily_vars = []

    if not daily_vars:
      daily_vars = ['sunrise', 'sunset']

    current_time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    current_time_str = current_time.isoformat()[0:-3]
    current_date = current_time.date().isoformat()

    response = await self.client.get(
      '/v1/forecast',
      params={
        'latitude': lat,
        'longitude': lon,
        'hourly': ','.join(hourly_vars),
        'daily': ','.join(daily_vars),
        'timezone': timezone or 'auto',
        'start_date': current_date,
        'end_date': current_date,
        'temperature_unit': temperature_unit,
      },
    )

    forecast = Forecast.model_validate_json(response.text)

    hourly_index = forecast.hourly.time.index(current_time_str)
    daily_index = forecast.daily.time.index(current_date)  # type: ignore

    return daily_index, hourly_index, forecast, hourly_vars, daily_vars

  async def fetch(
    self,
    *,
    lon: float,
    lat: float,
    timezone: str | None,
    temperature_unit: TemperatureUnit,
    hourly_variables: list[str] | None = None,
    daily_variables: list[str] | None = None,
  ) -> ForecastData:
    daily_index, hourly_index, forecast, hourly_vars, daily_vars = await self._fetch_hourly(
      lon=lon,
      lat=lat,
      timezone=timezone,
      temperature_unit=temperature_unit,
      hourly_variables=hourly_variables,
      daily_variables=daily_variables,
    )

    data = {}
    hourly_dict = forecast.hourly.model_dump()
    hourly_units_dict = forecast.hourly_units.model_dump()

    # Find temperature
    temp_val, temp_unit = None, None
    for k in ('temperature_2m', 'temperature'):
      if k in hourly_dict and hourly_dict[k] is not None:
        temp_val = hourly_dict[k][hourly_index]
        temp_unit = hourly_units_dict.get(k, '')
        break

    if temp_val is not None:
      data['temperature'] = f'{temp_val}{temp_unit}'

    # Find humidity
    hum_val, hum_unit = None, None
    for k in ('relative_humidity_2m', 'relativehumidity_2m', 'humidity'):
      if k in hourly_dict and hourly_dict[k] is not None:
        hum_val = hourly_dict[k][hourly_index]
        hum_unit = hourly_units_dict.get(k, '')
        break

    if hum_val is not None:
      data['humidity'] = f'{hum_val}{hum_unit}'

    # Find wind speed
    wind_val, wind_unit = None, None
    for k in ('wind_speed_10m', 'windspeed_10m', 'wind_speed'):
      if k in hourly_dict and hourly_dict[k] is not None:
        wind_val = hourly_dict[k][hourly_index]
        wind_unit = hourly_units_dict.get(k, '')
        break

    if wind_val is not None:
      data['wind_speed'] = f'{wind_val} {wind_unit}'.strip()

    # Process daily (sunrise/sunset)
    if forecast.daily and forecast.daily_units:
      daily_dict = forecast.daily.model_dump()

      if 'sunrise' in daily_dict and daily_dict['sunrise']:
        sunrise_date = datetime.datetime.strptime(daily_dict['sunrise'][daily_index], self.format)
        data['sunrise'] = str(sunrise_date.time())

      if 'sunset' in daily_dict and daily_dict['sunset']:
        sunset_date = datetime.datetime.strptime(daily_dict['sunset'][daily_index], self.format)
        data['sunset'] = str(sunset_date.time())

    # Populate any other hourly variables directly
    for var in hourly_vars:
      if var not in ('temperature_2m', 'relative_humidity_2m', 'relativehumidity_2m', 'wind_speed_10m', 'windspeed_10m'):
        if var in hourly_dict and hourly_dict[var] is not None:
          val = hourly_dict[var][hourly_index]
          unit = hourly_units_dict.get(var, '')
          data[var] = f'{val}{unit}' if unit else val

    return ForecastData(**data)
