# Copyright 2024-2026 Sébastien Demanou. All Rights Reserved.
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
from typing import ClassVar
from typing import Literal
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

from openmeteo_sdk.Unit import Unit

from ..core.controller import Controller
from ..models.forecast import DailyForecastData
from ..models.forecast import ForecastData
from ..providers.OpenMeteoProvider import OpenMeteoProvider

logger = logging.getLogger(__name__)

TemperatureUnit = Literal['celsius', 'fahrenheit']


UNIT_LABELS = {
  Unit.celsius: '°C',
  Unit.degree_direction: '°',
  Unit.dimensionless_integer: '',
  Unit.dimensionless: '',
  Unit.fahrenheit: '°F',
  Unit.hectopascal: 'hPa',
  Unit.iso8601: 'iso8601',
  Unit.kilometres_per_hour: 'km/h',
  Unit.metre: 'm',
  Unit.miles_per_hour: 'mph',
  Unit.millimetre: 'mm',
  Unit.percentage: '%',
  Unit.seconds: 's',
  Unit.unix_time: 'unixtime',
  Unit.watt_per_square_metre: 'W/m²',
  Unit.wmo_code: '',
}

xxx = {
  'temperature_2m',
  'relative_humidity_2m',
  'dew_point_2m',
  'apparent_temperature',
  'precipitation_probability',
  'precipitation',
}


class ForecastService:
  format: str = '%Y-%m-%dT%H:%M'

  ALLOWED_HOURLY: ClassVar[set[str]] = {
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

  ALLOWED_DAILY: ClassVar[set[str]] = {'sunrise', 'sunset'}

  NAME_MAPPING: ClassVar[dict[str, str]] = {
    'relativehumidity_2m': 'relative_humidity_2m',
    'windspeed_10m': 'wind_speed_10m',
  }

  def __init__(self, provider: OpenMeteoProvider) -> None:
    self.provider = provider

  @property
  def name(self) -> str:
    return self.provider.name

  @staticmethod
  def get_wind_direction(wind_direction: int) -> str:
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    angle_per_direction = 360 / len(directions)
    index = round(wind_direction / angle_per_direction) % len(directions)

    return directions[index]

  @staticmethod
  def format_unix_time(value: int | None, utc_offset_seconds: int) -> str | None:
    if value is None:
      return None

    utc_time = datetime.datetime.fromtimestamp(value, tz=datetime.UTC)
    local_time = utc_time + datetime.timedelta(seconds=utc_offset_seconds)

    return local_time.time().isoformat()

  @staticmethod
  def _unit_label(unit: int) -> str:
    return UNIT_LABELS.get(unit, '')

  @staticmethod
  def _openmeteo_date(value: datetime.datetime) -> str:
    return value.date().isoformat()

  @staticmethod
  def _value_at(values, index: int):
    if values is None or isinstance(values, int) or len(values) <= index:
      return None

    value = values[index]
    return value.item() if hasattr(value, 'item') else value

  @staticmethod
  def _current_timestamp(timezone: str | None) -> int:
    if timezone and timezone != 'auto':
      try:
        return int(datetime.datetime.now(ZoneInfo(timezone)).replace(minute=0, second=0, microsecond=0).timestamp())
      except ZoneInfoNotFoundError:
        logger.warning('Unknown timezone %s, falling back to UTC', timezone)

    now_utc = datetime.datetime.now(datetime.UTC).replace(minute=0, second=0, microsecond=0)
    return int(now_utc.timestamp())

  @staticmethod
  def _time_index(series, timestamp: int) -> int:
    start = series.Time()
    interval = series.Interval() or 3600
    length = series.Variables(0).ValuesLength() if series and series.VariablesLength() else 0  # type: ignore

    if length <= 0:
      return 0

    index = round((timestamp - start) / interval)
    return max(0, min(index, length - 1))

  async def fetch_daily(
    self,
    *,
    lon: float,
    lat: float,
    dateinfo: Controller.DateInfo,
    temperature_unit: TemperatureUnit,
    daily_variables: list[str] | None = None,
  ):
    logger.info(f'Fetching forecast for geo ({lon}, {lat})')

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
      'start_date': self._openmeteo_date(dateinfo.start),
      'end_date': self._openmeteo_date(dateinfo.end),
      'temperature_unit': temperature_unit,
    }

    responses = self.provider.client.weather_api(url, params=params)

    # Process daily data. The order of variables needs to be the same as requested.
    response = responses[0]
    daily = response.Daily()
    utc_offset_seconds = response.UtcOffsetSeconds()
    daily_data = {}

    for i, var_name in enumerate(daily_vars):
      variable = daily.Variables(i)  # type: ignore
      if var_name in ('sunrise', 'sunset'):
        values = variable.ValuesInt64AsNumpy()  # type: ignore
      else:
        values = variable.ValuesAsNumpy()  # type: ignore

      value = values[0].item() if len(values) > 0 else None

      if var_name in ('sunrise', 'sunset'):
        daily_data[var_name] = self.format_unix_time(value, utc_offset_seconds)
      else:
        daily_data[var_name] = value

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
  ):
    logger.info(f'Fetching forecast for geo ({lon}, {lat})')

    if hourly_variables is not None:
      hourly_vars = [ForecastService.NAME_MAPPING.get(var, var) for var in hourly_variables]
      hourly_vars = [var for var in hourly_vars if var in ForecastService.ALLOWED_HOURLY]
    else:
      hourly_vars = []

    if not hourly_vars:
      hourly_vars = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m']

    if daily_variables is not None:
      daily_vars = [var for var in daily_variables if var in ForecastService.ALLOWED_DAILY]
    else:
      daily_vars = []

    if not daily_vars:
      daily_vars = ['sunrise', 'sunset']

    current_date = datetime.datetime.now().date().isoformat()

    responses = self.provider.client.weather_api(
      'https://api.open-meteo.com/v1/forecast',
      params={
        'latitude': lat,
        'longitude': lon,
        'hourly': hourly_vars,
        'daily': daily_vars,
        'timezone': timezone or 'auto',
        'start_date': current_date,
        'end_date': current_date,
        'temperature_unit': temperature_unit,
      },
    )

    response = responses[0]
    hourly = response.Hourly()
    daily = response.Daily()
    utc_offset_seconds = response.UtcOffsetSeconds()
    hourly_index = self._time_index(hourly, self._current_timestamp(timezone)) if hourly else 0
    daily_index = 0

    hourly_data: dict[str, object] = {}
    hourly_units: dict[str, str] = {}

    for index, var_name in enumerate(hourly_vars):
      variable = hourly.Variables(index) if hourly else None  # type: ignore
      hourly_data[var_name] = self._value_at(variable.ValuesAsNumpy(), hourly_index) if variable else None
      hourly_units[var_name] = self._unit_label(variable.Unit()) if variable else ''

    daily_data: dict[str, object] = {}

    for index, var_name in enumerate(daily_vars):
      variable = daily.Variables(index) if daily else None  # type: ignore

      if not variable:
        daily_data[var_name] = None
      elif var_name in ('sunrise', 'sunset'):
        daily_data[var_name] = self.format_unix_time(
          self._value_at(variable.ValuesInt64AsNumpy(), daily_index), utc_offset_seconds
        )
      else:
        daily_data[var_name] = self._value_at(variable.ValuesAsNumpy(), daily_index)

    return hourly_data, hourly_units, daily_data, hourly_vars

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
    hourly_dict, hourly_units_dict, daily_dict, hourly_vars = await self._fetch_hourly(
      lon=lon,
      lat=lat,
      timezone=timezone,
      temperature_unit=temperature_unit,
      hourly_variables=hourly_variables,
      daily_variables=daily_variables,
    )

    data = {}

    # Find temperature
    temp_val, temp_unit = None, None
    for k in ('temperature_2m', 'temperature'):
      if k in hourly_dict and hourly_dict[k] is not None:
        temp_val = hourly_dict[k]
        temp_unit = hourly_units_dict.get(k, '')
        break

    if temp_val is not None:
      data['temperature'] = f'{temp_val}{temp_unit}'

    # Find humidity
    hum_val, hum_unit = None, None
    for k in ('relative_humidity_2m', 'relativehumidity_2m', 'humidity'):
      if k in hourly_dict and hourly_dict[k] is not None:
        hum_val = hourly_dict[k]
        hum_unit = hourly_units_dict.get(k, '')
        break

    if hum_val is not None:
      data['humidity'] = f'{hum_val}{hum_unit}'

    # Find wind speed
    wind_val, wind_unit = None, None
    for k in ('wind_speed_10m', 'windspeed_10m', 'wind_speed'):
      if k in hourly_dict and hourly_dict[k] is not None:
        wind_val = hourly_dict[k]
        wind_unit = hourly_units_dict.get(k, '')
        break

    if wind_val is not None:
      data['wind_speed'] = f'{wind_val} {wind_unit}'.strip()

    # Process daily (sunrise/sunset)
    if daily_dict.get('sunrise'):
      data['sunrise'] = daily_dict['sunrise']

    if daily_dict.get('sunset'):
      data['sunset'] = daily_dict['sunset']

    # Populate any other hourly variables directly
    for var in hourly_vars:
      if var not in ('temperature_2m', 'relative_humidity_2m', 'relativehumidity_2m', 'wind_speed_10m', 'windspeed_10m'):
        if var in hourly_dict and hourly_dict[var] is not None:
          val = hourly_dict[var]
          unit = hourly_units_dict.get(var, '')
          data[var] = f'{val}{unit}' if unit else val

    return ForecastData(**data)
