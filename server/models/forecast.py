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
from pydantic import Field


class Daily(BaseModel):
  model_config = ConfigDict(extra='ignore')

  time: list[str] = Field(..., description='List of ISO 8601 dates')
  sunrise: list[str] = Field(..., description='List of sunrise times in ISO 8601 format')
  sunset: list[str] = Field(..., description='List of sunset times in ISO 8601 format')


class DailyUnits(BaseModel):
  model_config = ConfigDict(extra='ignore')

  time: str = Field(..., description='Unit of time for daily data, typically "iso8601"')
  sunrise: str = Field(..., description='Unit for sunrise time, typically "iso8601"')
  sunset: str = Field(..., description='Unit for sunset time, typically "iso8601"')


class Hourly(BaseModel):
  model_config = ConfigDict(extra='ignore')

  time: list[str] = Field(..., description='List of ISO 8601 timestamps')
  temperature_2m: list[float] = Field(..., description='Hourly temperature at 2 meters above ground in Celsius')
  relativehumidity_2m: list[int] = Field(..., description='Hourly relative humidity at 2 meters above ground in percentage')
  windspeed_10m: list[float] = Field(..., description='Hourly wind speed at 10 meters above ground in km/h')


class HourlyUnits(BaseModel):
  model_config = ConfigDict(extra='ignore')

  time: str = Field(..., description='Unit of time for hourly data, typically "iso8601"')
  temperature_2m: str = Field(..., description='Unit of temperature at 2 meters, typically "°C"')
  relativehumidity_2m: str = Field(..., description='Unit of relative humidity, typically "%"')
  windspeed_10m: str = Field(..., description='Unit of wind speed at 10 meters, typically "km/h"')


class Forecast(BaseModel):
  model_config = ConfigDict(extra='ignore')

  latitude: float = Field(..., description='Latitude of the location')
  longitude: float = Field(..., description='Longitude of the location')
  generationtime_ms: float = Field(..., description='Time taken to generate the forecast data in milliseconds')
  utc_offset_seconds: int = Field(..., description='Offset from UTC in seconds')
  timezone: str = Field(..., description='Name of the timezone')
  timezone_abbreviation: str = Field(..., description='Abbreviation of the timezone')
  elevation: int = Field(..., description='Elevation of the location in meters')
  hourly_units: HourlyUnits = Field(..., description='Units for hourly data fields')
  hourly: Hourly = Field(..., description='Hourly forecast data')
  daily_units: DailyUnits = Field(..., description='Units for daily data fields')
  daily: Daily = Field(..., description='Daily forecast data')


class ForecastData(BaseModel):
  temperature: str = Field(..., description='Temperature summary (e.g., min/max or average)')
  humidity: str = Field(..., description='Humidity level or description')
  wind_speed: str = Field(..., description='Wind speed description')
  sunrise: str = Field(..., description='Sunrise time in ISO 8601 format')
  sunset: str = Field(..., description='Sunset time in ISO 8601 format')
