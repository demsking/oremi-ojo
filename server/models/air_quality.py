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
class Hourly(DataClassJsonMixin):
  time: list[str]
  european_aqi: list[int]
  us_aqi: list[int]


@dataclass
class HourlyUnits(DataClassJsonMixin):
  time: str
  european_aqi: str
  us_aqi: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class AirQualityData(DataClassJsonMixin):
  latitude: float
  longitude: float
  generationtime_ms: float
  utc_offset_seconds: int
  timezone: str
  timezone_abbreviation: str
  hourly_units: HourlyUnits
  hourly: Hourly


@dataclass
class AirQualityResponse(DataClassJsonMixin):
  value: str
  unit: str
  ranges: str
