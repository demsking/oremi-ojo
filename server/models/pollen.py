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
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class PollenName(StrEnum):
  OAK = 'oak'
  OLIVE = 'olive'
  GRASS = 'grass'
  CUPRESSACEAE = 'cupressaceae'
  PLANTAIN = 'plantain'
  URTICACEAE = 'urticaceae'
  ALDER = 'alder'
  ASH = 'ash'
  BEECH = 'beech'
  BIRCH = 'birch'
  HAZEL = 'hazel'
  MUGWORT = 'mugwort'
  PLANE_TREE = 'plane-tree'
  POPLAR = 'poplar'
  RAGWEED = 'ragweed'
  SORREL = 'sorrel'
  WILLOW = 'willow'


class PollenCategory(StrEnum):
  TREE = 'tree'
  GRASS = 'grass'
  WEED = 'weed'


class DailyPollenForecast(BaseModel):
  day: str = Field(..., description='Date of the forecast in YYYY-MM-DD format')
  name: PollenName = Field(..., description='Name of the pollen type')
  riskLevel: int = Field(..., description='Risk level associated with the pollen (e.g., 0-5)')
  category: PollenCategory = Field(..., description='Category of the pollen')


class PollenData(BaseModel):
  pollen_names: list[PollenName] | None = Field(..., description='List of pollen types detected')
  level: int = Field(..., description='Aggregated pollen level')
  risk: Literal['unknown', 'low', 'medium', 'high'] = Field(..., description='Categorized risk level based on pollen level')
