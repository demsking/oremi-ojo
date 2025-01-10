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
from datetime import timedelta

from ..core.http import HttpClient
from ..core.logger import logger
from ..core.provider import Provider
from ..models.forecast import Forecast
from ..models.forecast import ForecastResponse


class OpenMeteoForecastProvider(Provider):
  format: str = '%Y-%m-%dT%H:%M'

  def __init__(self) -> None:
    super().__init__('Open-Météo')
    self.client = HttpClient(
      base_url='https://api.open-meteo.com',
      expire_after=timedelta(minutes=30),
    )

  @staticmethod
  def get_wind_direction(wind_direction: int) -> str:
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    angle_per_direction = 360 / len(directions)
    index = round(wind_direction / angle_per_direction) % len(directions)

    return directions[index]

  async def _fetch(self, *, lon: float, lat: float) -> tuple[str, int, int, Forecast]:
    logger.info(f'Fetching forecast for geo ({lon}, {lat})')

    current_time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    current_time_str = current_time.isoformat()[0:-3]
    current_date = current_time.date().isoformat()

    response = await self.client.get('/v1/forecast', params={
      'latitude': lat,
      'longitude': lon,
      'hourly': 'temperature_2m,relativehumidity_2m,windspeed_10m',
      'daily': 'sunrise,sunset',
      'current_weather': 'true',
      'timezone': 'auto',
      'start_date': current_date,
      'end_date': current_date,
    })

    forecast = Forecast.from_json(response.text)

    hourly_index = forecast.hourly.time.index(current_time_str)
    daily_index = forecast.daily.time.index(current_date)

    return daily_index, hourly_index, forecast

  async def fetch(self, *, lon: float, lat: float) -> ForecastResponse:
    daily_index, hourly_index, forecast = await self._fetch(lon=lon, lat=lat)

    sunset_date = datetime.datetime.strptime(forecast.daily.sunset[daily_index], self.format)
    sunrise_date = datetime.datetime.strptime(forecast.daily.sunrise[daily_index], self.format)

    current_humidity = forecast.hourly.relativehumidity_2m[hourly_index]
    current_temperature = forecast.hourly.temperature_2m[hourly_index]
    current_windspeed = forecast.hourly.windspeed_10m[hourly_index]

    return ForecastResponse(
      temperature=f'{current_temperature}{forecast.hourly_units.temperature_2m}',
      humidity=f'{current_humidity}{forecast.hourly_units.relativehumidity_2m}',
      wind_direction=forecast.current_weather.winddirection,
      wind_speed=f'{current_windspeed} {forecast.hourly_units.windspeed_10m}',
      sunrise=sunrise_date.time(),
      sunset=sunset_date.time(),
    )
