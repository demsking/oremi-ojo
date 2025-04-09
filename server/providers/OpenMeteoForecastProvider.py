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

import openmeteo_requests
import requests_cache
from pydantic import BaseModel
from pydantic import Field
from retry_requests import retry

from ..core.config import CACHE_DIR
from ..core.controller import Controller
from ..core.http import HttpClient
from ..core.provider import Provider
from ..models.forecast import Forecast
from ..models.forecast import ForecastData


class OpenMeteoForecastProvider(Provider):
  format: str = '%Y-%m-%dT%H:%M'

  def __init__(self, controller: Controller, logger: logging.Logger) -> None:
    super().__init__('Open-Météo', controller, logger)
    self.client = HttpClient(
      base_url='https://api.open-meteo.com',
      expire_after=timedelta(minutes=30),
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

  async def fetch_daily(self, *, lon: float, lat: float, dateinfo: Controller.DateInfo):
    self.logger.info(f'Fetching forecast for geo ({lon}, {lat})')

    url = 'https://api.open-meteo.com/v1/forecast'
    params = {
      'latitude': lat,
      'longitude': lon,
      'daily': [
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
      ],
      'timezone': dateinfo.timezone,
      'start_date': dateinfo.start_date,
      'end_date': dateinfo.end_date,
    }

    responses = self.openmeteo.weather_api(url, params=params)

    # Process daily data. The order of variables needs to be the same as requested.
    daily = responses[0].Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()
    daily_sunrise = daily.Variables(3).ValuesInt64AsNumpy()
    daily_sunset = daily.Variables(4).ValuesInt64AsNumpy()
    daily_rain_sum = daily.Variables(5).ValuesAsNumpy()
    daily_uv_index_max = daily.Variables(6).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(7).ValuesAsNumpy()
    daily_wind_direction_10m_dominant = daily.Variables(8).ValuesAsNumpy()
    daily_wind_gusts_10m_max = daily.Variables(9).ValuesAsNumpy()

    return OpenMeteoForecastProvider.DailyForecastData(
      weather_code=daily_weather_code[0].item(),
      temperature_2m_max=daily_temperature_2m_max[0].item(),
      temperature_2m_min=daily_temperature_2m_min[0].item(),
      sunrise=daily_sunrise[0].item(),
      sunset=daily_sunset[0].item(),
      rain_sum=daily_rain_sum[0].item(),
      uv_index_max=daily_uv_index_max[0].item(),
      wind_speed_10m_max=daily_wind_speed_10m_max[0].item(),
      wind_direction_10m_dominant=daily_wind_direction_10m_dominant[0].item(),
      wind_gusts_10m_max=daily_wind_gusts_10m_max[0].item(),
    )

  async def _fetch_hourly(self, *, lon: float, lat: float, timezone: str | None) -> tuple[str, int, int, Forecast]:
    self.logger.info(f'Fetching forecast for geo ({lon}, {lat})')

    current_time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    current_time_str = current_time.isoformat()[0:-3]
    current_date = current_time.date().isoformat()

    response = await self.client.get(
      '/v1/forecast',
      params={
        'latitude': lat,
        'longitude': lon,
        'hourly': 'temperature_2m,relativehumidity_2m,windspeed_10m',
        'daily': 'sunrise,sunset',
        'timezone': timezone or 'auto',
        'start_date': current_date,
        'end_date': current_date,
      },
    )

    forecast = Forecast.model_validate_json(response.text)

    hourly_index = forecast.hourly.time.index(current_time_str)
    daily_index = forecast.daily.time.index(current_date)

    return daily_index, hourly_index, forecast

  async def fetch(self, *, lon: float, lat: float, timezone: str | None) -> ForecastData:
    daily_index, hourly_index, forecast = await self._fetch_hourly(lon=lon, lat=lat, timezone=timezone)

    sunset_date = datetime.datetime.strptime(forecast.daily.sunset[daily_index], self.format)
    sunrise_date = datetime.datetime.strptime(forecast.daily.sunrise[daily_index], self.format)

    current_humidity = forecast.hourly.relativehumidity_2m[hourly_index]
    current_temperature = forecast.hourly.temperature_2m[hourly_index]
    current_windspeed = forecast.hourly.windspeed_10m[hourly_index]

    return ForecastData(
      temperature=f'{current_temperature}{forecast.hourly_units.temperature_2m}',
      humidity=f'{current_humidity}{forecast.hourly_units.relativehumidity_2m}',
      # wind_direction=forecast.current_weather.winddirection,
      wind_speed=f'{current_windspeed} {forecast.hourly_units.windspeed_10m}',
      sunrise=str(sunrise_date.time()),
      sunset=str(sunset_date.time()),
    )

  class DailyForecastData(BaseModel):
    weather_code: int = Field(..., description='Weather condition code for the day')
    temperature_2m_max: float = Field(..., description='Maximum temperature at 2 meters')
    temperature_2m_min: float = Field(..., description='Minimum temperature at 2 meters')
    sunrise: int = Field(..., description='Sunrise time as Unix timestamp')
    sunset: int = Field(..., description='Sunset time as Unix timestamp')
    rain_sum: float = Field(..., description='Total daily rainfall in millimeters')
    uv_index_max: float = Field(..., description='Maximum UV index')
    wind_speed_10m_max: float = Field(..., description='Maximum wind speed at 10 meters')
    wind_direction_10m_dominant: float = Field(..., description='Dominant wind direction at 10 meters in degrees')
    wind_gusts_10m_max: float = Field(..., description='Maximum wind gusts at 10 meters')
