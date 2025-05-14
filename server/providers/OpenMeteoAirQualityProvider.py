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

from ..core.controller import Controller
from ..core.http import HttpClient
from ..core.provider import Provider
from ..models.air_quality import AirQualityData
from ..models.air_quality import EAQIData
from ..models.air_quality import USAQIData

USA_LATITUDE_RANGE = (28.0, 72.0)
USA_LONGITUDE_RANGE = (-172.0, -34.0)

EAGI_LEVELS = [
  (0, 20, 'good'),
  (20, 40, 'fair'),
  (40, 60, 'moderate'),
  (60, 80, 'poor'),
  (80, 100, 'very poor'),
  (100, float('inf'), 'extremely poor'),
]

USAGI_LEVELS = [
  (0, 50, 'good'),
  (51, 100, 'moderate'),
  (101, 150, 'unhealthy for sensitive groups'),
  (151, 200, 'unhealthy'),
  (201, 300, 'very unhealthy'),
  (301, 500, 'hazardous'),
]


class OpenMeteoAirQualityProvider(Provider):
  """
  Air Quality API

  Pollutants and pollen forecast in 11 km resolution.

  See https://open-meteo.com/en/docs/air-quality-api
  """

  def __init__(self, controller: Controller, logger: logging.Logger) -> None:
    super().__init__('Open-Météo', controller, logger)
    self.client = HttpClient(
      base_url='https://air-quality-api.open-meteo.com',
      expire_after=timedelta(minutes=30),
      logger=logger,
    )

  @staticmethod
  def determine_level(value: float, levels: list[tuple[float, float, str]]) -> str:
    for low, high, level in levels:
      if low <= value <= high:
        return level
    return 'unknown'

  async def fetch(self, *, lon: float, lat: float) -> USAQIData | EAQIData:
    self.logger.info(f'Fetching air quality data for geo ({lon}, {lat})')

    current_time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    current_time_str = current_time.isoformat()[0:-3]

    response = await self.client.get(
      '/v1/air-quality',
      params={
        'latitude': lat,
        'longitude': lon,
        'hourly': 'european_aqi,us_aqi',
        'start_date': current_time.date().isoformat(),
        'end_date': current_time.date().isoformat(),
      },
    )

    data = AirQualityData.model_validate_json(response.text)

    if USA_LATITUDE_RANGE[0] <= lat <= USA_LATITUDE_RANGE[1] and USA_LONGITUDE_RANGE[0] <= lon <= USA_LONGITUDE_RANGE[1]:
      raw = data.hourly.us_aqi
      unit = data.hourly_units.us_aqi
      levels = USAGI_LEVELS
      response_class = USAQIData
    else:
      # use European data for other locations
      raw = data.hourly.european_aqi
      unit = data.hourly_units.european_aqi
      levels = EAGI_LEVELS
      response_class = EAQIData

    index = data.hourly.time.index(current_time_str)
    air_quality = raw[index]
    level = OpenMeteoAirQualityProvider.determine_level(air_quality, levels)  # type: ignore

    return response_class(value=air_quality, level=level, unit=unit)  # type: ignore
