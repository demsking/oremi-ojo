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
from typing import Any
from typing import ClassVar
from typing import Literal
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

from openmeteo_sdk.Unit import Unit  # type: ignore[import-untyped]

from ..models.forecast import CurrentWeatherData
from ..models.forecast import DailyForecastItem
from ..models.forecast import DailyForecastResponse
from ..models.forecast import ForecastData
from ..models.forecast import HourlyForecastItem
from ..models.forecast import HourlyForecastResponse
from ..models.forecast import SunTimes
from ..models.forecast import WeatherAlert
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
  def _value_at(values: Any, index: int) -> Any:
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
  def _time_index(series: Any, timestamp: int) -> int:
    start: int = series.Time()
    interval: int = series.Interval() or 3600
    length: int = series.Variables(0).ValuesLength() if series and series.VariablesLength() else 0

    if length <= 0:
      return 0

    index = round((timestamp - start) / interval)
    return int(max(0, min(index, length - 1)))

  async def _fetch_hourly(
    self,
    *,
    lon: float,
    lat: float,
    timezone: str | None,
    temperature_unit: TemperatureUnit,
    hourly_variables: list[str] | None = None,
    daily_variables: list[str] | None = None,
  ) -> tuple[dict[str, Any], dict[str, str], dict[str, Any], list[str]]:
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
      variable = hourly.Variables(index) if hourly else None
      hourly_data[var_name] = self._value_at(variable.ValuesAsNumpy(), hourly_index) if variable else None
      hourly_units[var_name] = self._unit_label(variable.Unit()) if variable else ''

    daily_data: dict[str, object] = {}

    for index, var_name in enumerate(daily_vars):
      variable = daily.Variables(index) if daily else None

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

  async def fetch_current_weather(
    self,
    *,
    lon: float,
    lat: float,
    timezone: str | None = 'auto',
    temperature_unit: TemperatureUnit = 'celsius',
  ) -> CurrentWeatherData:
    logger.info(f'Fetching current weather for geo ({lon}, {lat})')

    current_vars = [
      'temperature_2m',
      'relative_humidity_2m',
      'apparent_temperature',
      'is_day',
      'weather_code',
      'wind_speed_10m',
      'wind_direction_10m',
    ]

    responses = self.provider.client.weather_api(
      'https://api.open-meteo.com/v1/forecast',
      params={
        'latitude': lat,
        'longitude': lon,
        'current': current_vars,
        'timezone': timezone or 'auto',
        'temperature_unit': temperature_unit,
      },
    )

    response = responses[0]
    current = response.Current()
    utc_offset_seconds = response.UtcOffsetSeconds()

    current_values = {}
    current_units = {}

    for index, var in enumerate(current_vars):
      variable = current.Variables(index) if current else None
      current_values[var] = variable.Value() if variable else 0
      current_units[var] = self._unit_label(variable.Unit()) if variable else ''

    current_time_unix = current.Time() if current else 0
    utc_time = datetime.datetime.fromtimestamp(current_time_unix, tz=datetime.UTC)
    local_time = utc_time + datetime.timedelta(seconds=utc_offset_seconds)
    time_str = local_time.isoformat()

    wind_dir_deg = int(current_values.get('wind_direction_10m', 0))

    return CurrentWeatherData(
      time=time_str,
      temperature=float(current_values.get('temperature_2m', 0.0)),
      temperature_unit=current_units.get('temperature_2m', '°C'),
      relative_humidity=int(current_values.get('relative_humidity_2m', 0)),
      apparent_temperature=float(current_values.get('apparent_temperature', 0.0)),
      is_day=int(current_values.get('is_day', 0)),
      weather_code=int(current_values.get('weather_code', 0)),
      wind_speed=float(current_values.get('wind_speed_10m', 0.0)),
      wind_speed_unit=current_units.get('wind_speed_10m', 'km/h'),
      wind_direction=wind_dir_deg,
      wind_direction_compass=self.get_wind_direction(wind_dir_deg),
    )

  async def fetch_hourly_forecast(
    self,
    *,
    lon: float,
    lat: float,
    timezone: str | None = 'auto',
    temperature_unit: TemperatureUnit = 'celsius',
    hours: int = 24,
  ) -> HourlyForecastResponse:
    logger.info(f'Fetching hourly forecast for geo ({lon}, {lat})')

    hourly_vars = [
      'temperature_2m',
      'relative_humidity_2m',
      'apparent_temperature',
      'precipitation_probability',
      'precipitation',
      'weather_code',
      'wind_speed_10m',
      'wind_direction_10m',
      'is_day',
    ]

    responses = self.provider.client.weather_api(
      'https://api.open-meteo.com/v1/forecast',
      params={
        'latitude': lat,
        'longitude': lon,
        'hourly': hourly_vars,
        'timezone': timezone or 'auto',
        'temperature_unit': temperature_unit,
      },
    )

    response = responses[0]
    hourly = response.Hourly()
    utc_offset_seconds = response.UtcOffsetSeconds()

    hourly_data: dict[str, list[float]] = {}
    hourly_units: dict[str, str] = {}

    for index, var in enumerate(hourly_vars):
      variable = hourly.Variables(index) if hourly else None
      if variable:
        hourly_data[var] = variable.ValuesAsNumpy().tolist()
        hourly_units[var] = self._unit_label(variable.Unit())
      else:
        hourly_data[var] = []
        hourly_units[var] = ''

    start_time = hourly.Time() if hourly else 0
    interval = (hourly.Interval() if hourly else 3600) or 3600
    length = len(hourly_data.get('temperature_2m', []))

    current_time = self._current_timestamp(timezone)
    start_index = 0
    if length > 0:
      start_index = round((current_time - start_time) / interval)
      start_index = max(0, min(start_index, length - 1))

    forecast_items = []
    end_index = min(start_index + hours, length)
    for i in range(start_index, end_index):
      t = start_time + i * interval
      utc_time = datetime.datetime.fromtimestamp(t, tz=datetime.UTC)
      local_time = utc_time + datetime.timedelta(seconds=utc_offset_seconds)
      time_str = local_time.isoformat()

      forecast_items.append(
        HourlyForecastItem(
          time=time_str,
          temperature=float(hourly_data['temperature_2m'][i]),
          relative_humidity=int(hourly_data['relative_humidity_2m'][i]),
          apparent_temperature=float(hourly_data['apparent_temperature'][i]),
          precipitation_probability=int(hourly_data['precipitation_probability'][i]),
          precipitation=float(hourly_data['precipitation'][i]),
          weather_code=int(hourly_data['weather_code'][i]),
          wind_speed=float(hourly_data['wind_speed_10m'][i]),
          wind_direction=int(hourly_data['wind_direction_10m'][i]),
          is_day=int(hourly_data['is_day'][i]),
        )
      )

    return HourlyForecastResponse(
      temperature_unit=hourly_units.get('temperature_2m', '°C'),
      wind_speed_unit=hourly_units.get('wind_speed_10m', 'km/h'),
      precipitation_unit=hourly_units.get('precipitation', 'mm'),
      forecast=forecast_items,
    )

  async def fetch_daily_forecast(
    self,
    *,
    lon: float,
    lat: float,
    timezone: str | None = 'auto',
    temperature_unit: TemperatureUnit = 'celsius',
    days: int = 7,
  ) -> DailyForecastResponse:
    logger.info(f'Fetching daily forecast for geo ({lon}, {lat})')

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

    responses = self.provider.client.weather_api(
      'https://api.open-meteo.com/v1/forecast',
      params={
        'latitude': lat,
        'longitude': lon,
        'daily': daily_vars,
        'timezone': timezone or 'auto',
        'temperature_unit': temperature_unit,
      },
    )

    response = responses[0]
    daily = response.Daily()
    utc_offset_seconds = response.UtcOffsetSeconds()

    daily_data: dict[str, Any] = {}
    daily_units: dict[str, str] = {}

    for index, var in enumerate(daily_vars):
      variable = daily.Variables(index) if daily else None
      if variable:
        if var in ('sunrise', 'sunset'):
          daily_data[var] = variable.ValuesInt64AsNumpy().tolist()
        else:
          daily_data[var] = variable.ValuesAsNumpy().tolist()
        daily_units[var] = self._unit_label(variable.Unit())
      else:
        daily_data[var] = []
        daily_units[var] = ''

    start_time = daily.Time() if daily else 0
    interval = (daily.Interval() if daily else 86400) or 86400
    length = len(daily_data.get('temperature_2m_max', []))

    forecast_items = []
    end_index = min(days, length)
    for i in range(end_index):
      t = start_time + i * interval
      date_str = datetime.datetime.fromtimestamp(t, tz=datetime.UTC).date().isoformat()

      sunrise_val = daily_data['sunrise'][i] if i < len(daily_data['sunrise']) else None
      sunset_val = daily_data['sunset'][i] if i < len(daily_data['sunset']) else None

      forecast_items.append(
        DailyForecastItem(
          date=date_str,
          weather_code=int(daily_data['weather_code'][i]) if daily_data['weather_code'] else None,
          temperature_2m_max=float(daily_data['temperature_2m_max'][i]) if daily_data['temperature_2m_max'] else None,
          temperature_2m_min=float(daily_data['temperature_2m_min'][i]) if daily_data['temperature_2m_min'] else None,
          sunrise=self.format_unix_time(sunrise_val, utc_offset_seconds) if sunrise_val else None,
          sunset=self.format_unix_time(sunset_val, utc_offset_seconds) if sunset_val else None,
          rain_sum=float(daily_data['rain_sum'][i]) if daily_data['rain_sum'] else None,
          uv_index_max=float(daily_data['uv_index_max'][i]) if daily_data['uv_index_max'] else None,
          wind_speed_10m_max=float(daily_data['wind_speed_10m_max'][i]) if daily_data['wind_speed_10m_max'] else None,
          wind_direction_10m_dominant=float(daily_data['wind_direction_10m_dominant'][i]) if daily_data['wind_direction_10m_dominant'] else None,
          wind_gusts_10m_max=float(daily_data['wind_gusts_10m_max'][i]) if daily_data['wind_gusts_10m_max'] else None,
        )
      )

    return DailyForecastResponse(
      temperature_unit=daily_units.get('temperature_2m_max', '°C'),
      wind_speed_unit=daily_units.get('wind_speed_10m_max', 'km/h'),
      precipitation_unit=daily_units.get('rain_sum', 'mm'),
      forecast=forecast_items,
    )

  async def fetch_weather_alerts(
    self,
    *,
    lon: float,
    lat: float,
    timezone: str | None = 'auto',
  ) -> list[WeatherAlert]:
    logger.info(f'Fetching weather alerts for geo ({lon}, {lat})')

    daily_vars = [
      'temperature_2m_max',
      'temperature_2m_min',
      'wind_speed_10m_max',
      'rain_sum',
      'uv_index_max',
    ]

    responses = self.provider.client.weather_api(
      'https://api.open-meteo.com/v1/forecast',
      params={
        'latitude': lat,
        'longitude': lon,
        'daily': daily_vars,
        'timezone': timezone or 'auto',
      },
    )

    response = responses[0]
    daily = response.Daily()

    daily_data: dict[str, list[float]] = {}
    for index, var in enumerate(daily_vars):
      variable = daily.Variables(index) if daily else None
      daily_data[var] = variable.ValuesAsNumpy().tolist() if variable else []

    start_time = daily.Time() if daily else 0
    interval = (daily.Interval() if daily else 86400) or 86400
    length = len(daily_data.get('temperature_2m_max', []))

    alerts = []

    for i in range(length):
      t = start_time + i * interval
      date_str = datetime.datetime.fromtimestamp(t, tz=datetime.UTC).date().isoformat()

      temp_max = daily_data['temperature_2m_max'][i] if i < len(daily_data['temperature_2m_max']) else None
      if temp_max is not None and temp_max > 38.0:
        alerts.append(
          WeatherAlert(
            event='Extreme Heat Warning',
            description=f'Dangerous heat levels expected. Maximum temperature of {temp_max:.1f}°C.',
            severity='severe',
            starts_at=f'{date_str}T09:00:00',
            ends_at=f'{date_str}T19:00:00',
          )
        )

      temp_min = daily_data['temperature_2m_min'][i] if i < len(daily_data['temperature_2m_min']) else None
      if temp_min is not None and temp_min < -10.0:
        alerts.append(
          WeatherAlert(
            event='Extreme Cold Warning',
            description=f'Severely cold temperatures expected. Minimum temperature of {temp_min:.1f}°C.',
            severity='severe',
            starts_at=f'{date_str}T00:00:00',
            ends_at=f'{date_str}T23:59:59',
          )
        )

      wind_max = daily_data['wind_speed_10m_max'][i] if i < len(daily_data['wind_speed_10m_max']) else None
      if wind_max is not None and wind_max > 50.0:
        alerts.append(
          WeatherAlert(
            event='High Wind Warning',
            description=f'Strong winds expected with gusts or maximum speeds up to {wind_max:.1f} km/h.',
            severity='moderate',
            starts_at=f'{date_str}T00:00:00',
            ends_at=f'{date_str}T23:59:59',
          )
        )

      rain_sum = daily_data['rain_sum'][i] if i < len(daily_data['rain_sum']) else None
      if rain_sum is not None and rain_sum > 50.0:
        alerts.append(
          WeatherAlert(
            event='Heavy Rainfall Warning',
            description=f'Potential for localized flooding with heavy rainfall up to {rain_sum:.1f} mm.',
            severity='moderate',
            starts_at=f'{date_str}T00:00:00',
            ends_at=f'{date_str}T23:59:59',
          )
        )

      uv_max = daily_data['uv_index_max'][i] if i < len(daily_data['uv_index_max']) else None
      if uv_max is not None and uv_max > 8.0:
        alerts.append(
          WeatherAlert(
            event='High UV Index Alert',
            description=f'Very high UV radiation levels expected (UV Index: {uv_max:.1f}). Protect your skin and eyes.',
            severity='minor',
            starts_at=f'{date_str}T10:00:00',
            ends_at=f'{date_str}T16:00:00',
          )
        )

    return alerts

  async def fetch_sun_times(
    self,
    *,
    lon: float,
    lat: float,
    timezone: str | None = 'auto',
    days: int = 7,
  ) -> list[SunTimes]:
    logger.info(f'Fetching sun times for geo ({lon}, {lat})')

    daily_vars = ['sunrise', 'sunset']

    responses = self.provider.client.weather_api(
      'https://api.open-meteo.com/v1/forecast',
      params={
        'latitude': lat,
        'longitude': lon,
        'daily': daily_vars,
        'timezone': timezone or 'auto',
      },
    )

    response = responses[0]
    daily = response.Daily()
    utc_offset_seconds = response.UtcOffsetSeconds()

    daily_data: dict[str, list[int]] = {}
    for index, var in enumerate(daily_vars):
      variable = daily.Variables(index) if daily else None
      if variable:
        daily_data[var] = variable.ValuesInt64AsNumpy().tolist()
      else:
        daily_data[var] = []

    start_time = daily.Time() if daily else 0
    interval = (daily.Interval() if daily else 86400) or 86400
    length = len(daily_data.get('sunrise', []))

    sun_times_list = []
    end_index = min(days, length)
    for i in range(end_index):
      t = start_time + i * interval
      date_str = datetime.datetime.fromtimestamp(t, tz=datetime.UTC).date().isoformat()

      sunrise_val = daily_data['sunrise'][i] if i < len(daily_data['sunrise']) else None
      sunset_val = daily_data['sunset'][i] if i < len(daily_data['sunset']) else None

      sun_times_list.append(
        SunTimes(
          date=date_str,
          sunrise=self.format_unix_time(sunrise_val, utc_offset_seconds) if sunrise_val else None,
          sunset=self.format_unix_time(sunset_val, utc_offset_seconds) if sunset_val else None,
        )
      )

    return sun_times_list
