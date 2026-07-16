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
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class Daily(BaseModel):
  model_config = ConfigDict(extra='allow')

  time: list[str] = Field(..., description='List of ISO 8601 dates')
  sunrise: list[str] | None = Field(None, description='List of sunrise times in ISO 8601 format')
  sunset: list[str] | None = Field(None, description='List of sunset times in ISO 8601 format')


class DailyUnits(BaseModel):
  model_config = ConfigDict(extra='allow')

  time: str = Field(..., description='Unit of time for daily data, typically "iso8601"')
  sunrise: str | None = Field(None, description='Unit for sunrise time, typically "iso8601"')
  sunset: str | None = Field(None, description='Unit for sunset time, typically "iso8601"')


class Hourly(BaseModel):
  model_config = ConfigDict(extra='allow')

  time: list[str] = Field(..., description='List of ISO 8601 timestamps')
  temperature_2m: list[float] | None = Field(None, description='Hourly temperature at 2 meters above ground in Celsius')
  relativehumidity_2m: list[int] | None = Field(None, description='Hourly relative humidity at 2 meters above ground in percentage')
  windspeed_10m: list[float] | None = Field(None, description='Hourly wind speed at 10 meters above ground in km/h')


class HourlyUnits(BaseModel):
  model_config = ConfigDict(extra='allow')

  time: str = Field(..., description='Unit of time for hourly data, typically "iso8601"')
  temperature_2m: str | None = Field(None, description='Unit of temperature at 2 meters, typically "°C"')
  relativehumidity_2m: str | None = Field(None, description='Unit of relative humidity, typically "%"')
  windspeed_10m: str | None = Field(None, description='Unit of wind speed at 10 meters, typically "km/h"')


class Forecast(BaseModel):
  model_config = ConfigDict(extra='allow')

  latitude: float = Field(..., description='Latitude of the location')
  longitude: float = Field(..., description='Longitude of the location')
  generationtime_ms: float = Field(..., description='Time taken to generate the forecast data in milliseconds')
  utc_offset_seconds: int = Field(..., description='Offset from UTC in seconds')
  timezone: str = Field(..., description='Name of the timezone')
  timezone_abbreviation: str = Field(..., description='Abbreviation of the timezone')
  elevation: float = Field(..., description='Elevation of the location in meters')
  hourly_units: HourlyUnits = Field(..., description='Units for hourly data fields')
  hourly: Hourly = Field(..., description='Hourly forecast data')
  daily_units: DailyUnits | None = Field(None, description='Units for daily data fields')
  daily: Daily | None = Field(None, description='Daily forecast data')


class ForecastData(BaseModel):
  model_config = ConfigDict(extra='allow')

  temperature: str | None = Field(None, description='Temperature summary (e.g., min/max or average)')
  humidity: str | None = Field(None, description='Humidity level or description')
  wind_speed: str | None = Field(None, description='Wind speed description')
  sunrise: str | None = Field(None, description='Sunrise time in ISO 8601 format')
  sunset: str | None = Field(None, description='Sunset time in ISO 8601 format')


class DailyForecastData(BaseModel):
  model_config = ConfigDict(extra='allow')

  weather_code: int | None = Field(None, description='Weather condition code for the day')
  temperature_2m_max: float | None = Field(None, description='Maximum temperature at 2 meters')
  temperature_2m_min: float | None = Field(None, description='Minimum temperature at 2 meters')
  sunrise: str | None = Field(None, description='Sunrise time in local HH:MM:SS format')
  sunset: str | None = Field(None, description='Sunset time in local HH:MM:SS format')
  rain_sum: float | None = Field(None, description='Total daily rainfall in millimeters')
  uv_index_max: float | None = Field(None, description='Maximum UV index')
  wind_speed_10m_max: float | None = Field(None, description='Maximum wind speed at 10 meters')
  wind_direction_10m_dominant: float | None = Field(None, description='Dominant wind direction at 10 meters in degrees')
  wind_gusts_10m_max: float | None = Field(None, description='Maximum wind gusts at 10 meters')


class CurrentWeatherData(BaseModel):
  model_config = ConfigDict(extra='allow')

  time: str = Field(..., description='ISO 8601 timestamp of the current weather data')
  temperature: float = Field(..., description='Current temperature')
  temperature_unit: str = Field(..., description='Temperature unit')
  relative_humidity: int = Field(..., description='Relative humidity in percentage')
  apparent_temperature: float = Field(..., description='Apparent (feels-like) temperature')
  is_day: int = Field(..., description='Is 1 for day, 0 for night')
  weather_code: int = Field(..., description='WMO Weather weather code')
  wind_speed: float = Field(..., description='Wind speed')
  wind_speed_unit: str = Field(..., description='Wind speed unit')
  wind_direction: int = Field(..., description='Wind direction in degrees')
  wind_direction_compass: str = Field(..., description='Wind direction in compass points')


class HourlyForecastItem(BaseModel):
  model_config = ConfigDict(extra='allow')

  time: str = Field(..., description='ISO 8601 timestamp')
  temperature: float = Field(..., description='Temperature')
  relative_humidity: int = Field(..., description='Relative humidity in percentage')
  apparent_temperature: float = Field(..., description='Apparent temperature')
  precipitation_probability: int = Field(..., description='Precipitation probability in percentage')
  precipitation: float = Field(..., description='Precipitation amount')
  weather_code: int = Field(..., description='Weather condition code')
  wind_speed: float = Field(..., description='Wind speed')
  wind_direction: int = Field(..., description='Wind direction in degrees')
  is_day: int = Field(..., description='Is 1 for day, 0 for night')


class HourlyForecastResponse(BaseModel):
  model_config = ConfigDict(extra='allow')

  temperature_unit: str = Field(..., description='Temperature unit')
  wind_speed_unit: str = Field(..., description='Wind speed unit')
  precipitation_unit: str = Field(..., description='Precipitation unit')
  forecast: list[HourlyForecastItem] = Field(..., description='List of hourly forecast items')


class DailyForecastItem(BaseModel):
  model_config = ConfigDict(extra='allow')

  date: str = Field(..., description='ISO 8601 date')
  weather_code: int | None = Field(None, description='Weather condition code for the day')
  temperature_2m_max: float | None = Field(None, description='Maximum temperature at 2 meters')
  temperature_2m_min: float | None = Field(None, description='Minimum temperature at 2 meters')
  sunrise: str | None = Field(None, description='Sunrise time in local HH:MM:SS format')
  sunset: str | None = Field(None, description='Sunset time in local HH:MM:SS format')
  rain_sum: float | None = Field(None, description='Total daily rainfall in millimeters')
  uv_index_max: float | None = Field(None, description='Maximum UV index')
  wind_speed_10m_max: float | None = Field(None, description='Maximum wind speed at 10 meters')
  wind_direction_10m_dominant: float | None = Field(None, description='Dominant wind direction at 10 meters in degrees')
  wind_gusts_10m_max: float | None = Field(None, description='Maximum wind gusts at 10 meters')


class DailyForecastResponse(BaseModel):
  model_config = ConfigDict(extra='allow')

  temperature_unit: str = Field(..., description='Temperature unit')
  wind_speed_unit: str = Field(..., description='Wind speed unit')
  precipitation_unit: str = Field(..., description='Precipitation unit')
  forecast: list[DailyForecastItem] = Field(..., description='List of daily forecast items')


class WeatherAlert(BaseModel):
  model_config = ConfigDict(extra='allow')

  event: str = Field(..., description='The name of the alert event (e.g., Extreme Heat Warning)')
  description: str = Field(..., description='Detailed description of the alert and potential impact')
  severity: str = Field(..., description='Severity of the alert: minor, moderate, severe, or extreme')
  starts_at: str | None = Field(None, description='ISO timestamp or date when the alert starts')
  ends_at: str | None = Field(None, description='ISO timestamp or date when the alert ends')


class SunTimes(BaseModel):
  model_config = ConfigDict(extra='allow')

  date: str = Field(..., description='ISO 8601 date')
  sunrise: str | None = Field(None, description='Sunrise time in local HH:MM:SS format')
  sunset: str | None = Field(None, description='Sunset time in local HH:MM:SS format')
