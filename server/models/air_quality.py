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
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class Hourly(BaseModel):
  time: list[str] = Field(..., description='List of ISO 8601 timestamps')
  european_aqi: list[int] = Field(..., description='List of European AQI values')
  us_aqi: list[int] = Field(..., description='List of US AQI values')


class HourlyUnits(BaseModel):
  time: str = Field(..., description='Unit for time values, typically "iso8601"')
  european_aqi: str = Field(..., description='Unit for European AQI, typically "EAQI"')
  us_aqi: str = Field(..., description='Unit for US AQI, typically "USAQI"')


class AirQualityData(BaseModel):
  latitude: float = Field(..., description='Latitude of the location')
  longitude: float = Field(..., description='Longitude of the location')
  generationtime_ms: float = Field(..., description='Time taken to generate the response in milliseconds')
  utc_offset_seconds: int = Field(..., description='Offset from UTC in seconds')
  timezone: str = Field(..., description='Timezone name')
  timezone_abbreviation: str = Field(..., description='Abbreviation of the timezone')
  hourly_units: HourlyUnits = Field(..., description='Units of the hourly data')
  hourly: Hourly = Field(..., description='Hourly air quality data')


class EAQIData(BaseModel):
  value: int = Field(..., description='European AQI value')
  level: Literal['good', 'fair', 'moderate', 'poor', 'very poor', 'extremely poor', 'unknown'] = Field(
    ..., description='European AQI level category'
  )
  unit: Literal['EAQI'] = Field('EAQI', description='Unit identifier for EAQI')


class USAQIData(BaseModel):
  value: int = Field(..., description='US AQI value')
  level: Literal[
    'good', 'moderate', 'unhealthy for sensitive groups', 'unhealthy', 'very unhealthy', 'hazardous', 'unknown'
  ] = Field(..., description='US AQI level category')
  unit: Literal['USAQI'] = Field('USAQI', description='Unit identifier for USAQI')
