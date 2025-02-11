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
from pydantic import Field


class CurrentWeather(BaseModel):
  time: str
  interval: int
  temperature: float
  windspeed: float
  winddirection: int
  is_day: int
  weathercode: int


class CurrentWeatherUnits(BaseModel):
  time: str
  interval: str
  temperature: str
  windspeed: str
  winddirection: str
  is_day: str
  weathercode: str


class Daily(BaseModel):
  time: list[str]
  sunrise: list[str]
  sunset: list[str]


class DailyUnits(BaseModel):
  time: str
  sunrise: str
  sunset: str


class Hourly(BaseModel):
  time: list[str]
  temperature_2m: list[float] = Field(alias='temperature_2m')
  relativehumidity_2m: list[int] = Field(alias='relativehumidity_2m')
  windspeed_10m: list[float] = Field(alias='windspeed_10m')


class HourlyUnits(BaseModel):
  time: str
  temperature_2m: str = Field(alias='temperature_2m')
  relativehumidity_2m: str = Field(alias='relativehumidity_2m')
  windspeed_10m: str = Field(alias='windspeed_10m')


class Forecast(BaseModel):
  latitude: float
  longitude: float
  generationtime_ms: float
  utc_offset_seconds: int
  timezone: str
  timezone_abbreviation: str
  elevation: int
  current_weather_units: CurrentWeatherUnits
  current_weather: CurrentWeather
  hourly_units: HourlyUnits
  hourly: Hourly
  daily_units: DailyUnits
  daily: Daily

  @classmethod
  def from_dict(cls, data: dict) -> 'Forecast':
    return cls.model_validate(data)


class ForecastResponse(BaseModel):
  temperature: str
  humidity: str
  wind_direction: int
  wind_speed: str
  sunrise: str
  sunset: str
