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
from pydantic import BaseModel
from pydantic import ConfigDict


class Daily(BaseModel):
  model_config = ConfigDict(extra='ignore')

  time: list[str]
  sunrise: list[str]
  sunset: list[str]


class DailyUnits(BaseModel):
  model_config = ConfigDict(extra='ignore')

  time: str
  sunrise: str
  sunset: str


class Hourly(BaseModel):
  model_config = ConfigDict(extra='ignore')

  time: list[str]
  temperature_2m: list[float]
  relativehumidity_2m: list[int]
  windspeed_10m: list[float]


class HourlyUnits(BaseModel):
  model_config = ConfigDict(extra='ignore')

  time: str
  temperature_2m: str
  relativehumidity_2m: str
  windspeed_10m: str


class Forecast(BaseModel):
  model_config = ConfigDict(extra='ignore')

  latitude: float
  longitude: float
  generationtime_ms: float
  utc_offset_seconds: int
  timezone: str
  timezone_abbreviation: str
  elevation: int
  hourly_units: HourlyUnits
  hourly: Hourly
  daily_units: DailyUnits
  daily: Daily


class ForecastResponse(BaseModel):
  temperature: str
  humidity: str
  # wind_direction: int
  wind_speed: str
  sunrise: str
  sunset: str
