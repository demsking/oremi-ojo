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
from ..models.air_quality import AirQualityData
from ..models.air_quality import AirQualityResponse

AMERICA_LATITUDE_RANGE = (28.0, 72.0)
AMERICA_LONGITUDE_RANGE = (-172.0, -34.0)

EAGI_RANGES_DESC = 'from 0-20 (good), 20-40 (fair), 40-60 (moderate), 60-80 (poor), 80-100 (very poor) and exceeds 100 for extremely poor conditions.'

USAGI_RANGES_DESC = 'from 0-50 (good), 51-100 (moderate), 101-150 (unhealthy for sensitive groups), 151-200 (unhealthy), 201-300 (very unhealthy) and 301-500 (hazardous).'


class OpenMeteoAirQualityProvider(Provider):
  def __init__(self) -> None:
    super().__init__('Open-Météo')
    self.client = HttpClient(
      base_url='https://air-quality-api.open-meteo.com',
      expire_after=timedelta(minutes=30),
    )

  async def fetch(self, *, lon: float, lat: float) -> AirQualityResponse:
    logger.info(f'Fetching air quality data for geo ({lon}, {lat})')

    current_time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    current_time_str = current_time.isoformat()[0:-3]

    response = await self.client.get('/v1/air-quality', params={
      'latitude': lat,
      'longitude': lon,
      'hourly': 'european_aqi,us_aqi',
      'start_date': current_time.date().isoformat(),
      'end_date': current_time.date().isoformat(),
    })

    data = AirQualityData.from_json(response.text)

    if (AMERICA_LATITUDE_RANGE[0] <= lat <= AMERICA_LATITUDE_RANGE[1] and
        AMERICA_LONGITUDE_RANGE[0] <= lon <= AMERICA_LONGITUDE_RANGE[1]):
      raw = data.hourly.us_aqi
      unit = data.hourly_units.us_aqi
      ranges_desc = USAGI_RANGES_DESC
    else:
      # use European data for other locations
      raw = data.hourly.european_aqi
      unit = data.hourly_units.european_aqi
      ranges_desc = EAGI_RANGES_DESC

    index = data.hourly.time.index(current_time_str)
    air_quality = raw[index]

    return AirQualityResponse(
      value=air_quality,
      unit=unit,
      ranges=ranges_desc,
    )
