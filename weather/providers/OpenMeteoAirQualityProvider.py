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

import httpx

from ..core.controller import Controller
from ..core.provider import Provider
from ..models.air_quality import AirQualityData
from ..models.air_quality import EAQIData
from ..models.air_quality import USAQIData


logger = logging.getLogger(__name__)

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

  def __init__(self, controller: Controller) -> None:
    super().__init__('Open-Météo', controller)
    self.client = httpx.AsyncClient(
      base_url='https://air-quality-api.open-meteo.com',
    )

  @staticmethod
  def determine_level(value: float, levels: list[tuple[float, float, str]]) -> str:
    for low, high, level in levels:
      if low <= value <= high:
        return level
    return 'unknown'

  async def fetch(self, *, lon: float, lat: float, variables: list[str] | None = None) -> USAQIData | EAQIData:
    logger.info(f'Fetching air quality data for geo ({lon}, {lat})')

    allowed_aqi = {
      'pm10',
      'pm2_5',
      'carbon_monoxide',
      'carbon_dioxide',
      'nitrogen_dioxide',
      'sulphur_dioxide',
      'ozone',
      'aerosol_optical_depth',
      'dust',
      'uv_index',
      'uv_index_clear_sky',
      'ammonia',
      'methane',
      'alder_pollen',
      'birch_pollen',
      'grass_pollen',
      'mugwort_pollen',
      'olive_pollen',
      'ragweed_pollen',
      'formaldehyde',
      'glyoxal',
      'non_methane_volatile_organic_compounds',
      'pm10_wildfires',
      'peroxyacyl_nitrates',
      'secondary_inorganic_aerosol',
      'residential_elementary_carbon',
      'total_elementary_carbon',
      'pm2_5_total_organic_matter',
      'sea_salt_aerosol',
      'nitrogen_monoxide',
      'european_aqi',
      'european_aqi_pm2_5',
      'european_aqi_pm10',
      'european_aqi_nitrogen_dioxide',
      'european_aqi_ozone',
      'european_aqi_sulphur_dioxide',
      'us_aqi',
      'us_aqi_pm2_5',
      'us_aqi_pm10',
      'us_aqi_nitrogen_dioxide',
      'us_aqi_carbon_monoxide',
      'us_aqi_ozone',
      'us_aqi_sulphur_dioxide',
      'is_day',
    }

    if variables is not None:
      aqi_vars = [var for var in variables if var in allowed_aqi]
    else:
      aqi_vars = []

    # Make sure we always fetch the AQIs to determine the overall levels/response class
    if 'european_aqi' not in aqi_vars:
      aqi_vars.append('european_aqi')

    if 'us_aqi' not in aqi_vars:
      aqi_vars.append('us_aqi')

    current_time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    current_time_str = current_time.isoformat()[0:-3]

    response = await self.client.get(
      '/v1/air-quality',
      params={
        'latitude': lat,
        'longitude': lon,
        'hourly': ','.join(aqi_vars),
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
    air_quality = raw[index]  # type: ignore
    level = OpenMeteoAirQualityProvider.determine_level(air_quality, levels)  # type: ignore

    # Get extra pollutant values at the current time
    hourly_dict = data.hourly.model_dump()
    hourly_units_dict = data.hourly_units.model_dump()

    extra_data = {}
    for var in aqi_vars:
      if var not in ('european_aqi', 'us_aqi') and var in hourly_dict and hourly_dict[var] is not None:
        val = hourly_dict[var][index]
        unit_val = hourly_units_dict.get(var, '')
        extra_data[var] = f'{val} {unit_val}'.strip() if unit_val else val

    return response_class(value=air_quality, level=level, unit=unit, **extra_data)  # type: ignore
