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
from dataclasses import dataclass

from dataclasses_json import dataclass_json
from dataclasses_json import DataClassJsonMixin
from dataclasses_json import Undefined


@dataclass
class CurrentWeather(DataClassJsonMixin):
  time: str
  interval: int
  temperature: float
  windspeed: float
  winddirection: int
  is_day: int
  weathercode: int


@dataclass
class CurrentWeatherUnits(DataClassJsonMixin):
  time: str
  interval: str
  temperature: str
  windspeed: str
  winddirection: str
  is_day: str
  weathercode: str


@dataclass
class Daily(DataClassJsonMixin):
  time: list[str]
  sunrise: list[str]
  sunset: list[str]


@dataclass
class DailyUnits(DataClassJsonMixin):
  time: str
  sunrise: str
  sunset: str


@dataclass
class Hourly(DataClassJsonMixin):
  time: list[str]
  temperature_2m: list[float]
  relativehumidity_2m: list[int]
  windspeed_10m: list[float]


@dataclass
class HourlyUnits(DataClassJsonMixin):
  time: str
  temperature_2m: str
  relativehumidity_2m: str
  windspeed_10m: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Forecast(DataClassJsonMixin):
  latitude: float
  longitude: int
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
  def from_dict(cls, data):
    # Convert nested dictionaries to objects
    data['current_weather_units'] = CurrentWeatherUnits(**data['current_weather_units'])
    data['current_weather'] = CurrentWeather(**data['current_weather'])
    data['hourly_units'] = HourlyUnits(**data['hourly_units'])
    data['hourly'] = Hourly(**data['hourly'])
    data['daily_units'] = DailyUnits(**data['daily_units'])
    data['daily'] = Daily(**data['daily'])

    # Create and return AirQualityData instance
    return cls(**data)


@dataclass
class ForecastResponse(DataClassJsonMixin):
  temperature: str
  humidity: str
  wind_direction: int
  wind_speed: str
  sunrise: str
  sunset: str
