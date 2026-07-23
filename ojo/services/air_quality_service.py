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
import logging
from typing import ClassVar

from openmeteo_sdk.Unit import Unit  # type: ignore[import-untyped]

from ..models.air_quality import EAQIData
from ..models.air_quality import USAQIData
from ..providers.OpenMeteoProvider import OpenMeteoProvider


logger = logging.getLogger(__name__)

USA_LATITUDE_RANGE = (28.0, 72.0)
USA_LONGITUDE_RANGE = (-172.0, -34.0)

EAGI_LEVELS: list[tuple[float, float, str]] = [
  (0, 20, 'good'),
  (20, 40, 'fair'),
  (40, 60, 'moderate'),
  (60, 80, 'poor'),
  (80, 100, 'very poor'),
  (100, float('inf'), 'extremely poor'),
]

USAGI_LEVELS: list[tuple[float, float, str]] = [
  (0, 50, 'good'),
  (51, 100, 'moderate'),
  (101, 150, 'unhealthy for sensitive groups'),
  (151, 200, 'unhealthy'),
  (201, 300, 'very unhealthy'),
  (301, 500, 'hazardous'),
]


class AirQualityService:
  """
  Air Quality API

  Pollutants and pollen forecast in 11 km resolution.

  See https://open-meteo.com/en/docs/air-quality-api
  """

  UNIT_LABELS: ClassVar[dict[int, str]] = {
    Unit.dimensionless: '',
    Unit.dimensionless_integer: '',
    Unit.european_air_quality_index: 'EAQI',
    Unit.grains_per_cubic_metre: 'grains/m³',
    Unit.micrograms_per_cubic_metre: 'μg/m³',
    Unit.parts_per_million: 'ppm',
    Unit.percentage: '%',
    Unit.us_air_quality_index: 'USAQI',
  }

  ALLOWED_AQI: ClassVar[set[str]] = {
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

  def __init__(self, provider: OpenMeteoProvider) -> None:
    self.provider = provider

  @property
  def name(self) -> str:
    return self.provider.name

  @staticmethod
  def determine_level(value: float, levels: list[tuple[float, float, str]]) -> str:
    for low, high, level in levels:
      if low <= value <= high:
        return level
    return 'unknown'

  @classmethod
  def _unit_label(cls, unit: int) -> str:
    return cls.UNIT_LABELS.get(unit, '')

  async def fetch(self, *, lon: float, lat: float, variables: list[str] | None = None) -> USAQIData | EAQIData:
    logger.info(f'Fetching air quality data for geo ({lon}, {lat})')

    if variables is not None:
      aqi_vars = [var for var in variables if var in AirQualityService.ALLOWED_AQI]
    else:
      aqi_vars = []

    # Make sure we always fetch the AQIs to determine the overall levels/response class
    if 'european_aqi' not in aqi_vars:
      aqi_vars.append('european_aqi')

    if 'us_aqi' not in aqi_vars:
      aqi_vars.append('us_aqi')

    responses = self.provider.client.weather_api(
      'https://air-quality-api.open-meteo.com/v1/air-quality',
      params={
        'latitude': lat,
        'longitude': lon,
        'current': aqi_vars,
      },
    )

    current = responses[0].Current()
    current_values = {}
    current_units = {}

    for index, var in enumerate(aqi_vars):
      variable = current.Variables(index) if current else None
      current_values[var] = variable.Value() if variable else 0
      current_units[var] = self._unit_label(variable.Unit()) if variable else ''

    response_class: type[USAQIData] | type[EAQIData]

    if USA_LATITUDE_RANGE[0] <= lat <= USA_LATITUDE_RANGE[1] and USA_LONGITUDE_RANGE[0] <= lon <= USA_LONGITUDE_RANGE[1]:
      unit = current_units.get('us_aqi', 'USAQI') or 'USAQI'
      air_quality = int(current_values.get('us_aqi', 0))
      levels = USAGI_LEVELS
      response_class = USAQIData
    else:
      # use European data for other locations
      unit = current_units.get('european_aqi', 'EAQI') or 'EAQI'
      air_quality = int(current_values.get('european_aqi', 0))
      levels = EAGI_LEVELS
      response_class = EAQIData

    level = AirQualityService.determine_level(air_quality, levels)

    extra_data = {}
    for var in aqi_vars:
      if var not in ('european_aqi', 'us_aqi') and var in current_values:
        val = current_values[var]
        unit_val = current_units.get(var, '')
        extra_data[var] = f'{val} {unit_val}'.strip() if unit_val else val

    return response_class(value=air_quality, level=level, unit=unit, **extra_data)  # type: ignore
