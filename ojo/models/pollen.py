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
from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field


class PollenName(StrEnum):
  ALDER = 'alder'  # Aulne
  BIRCH = 'birch'  # Bouleau
  GRASS = 'grass'  # Graminées
  MUGWORT = 'mugwort'  # Armoise
  OLIVE = 'olive'  # Olivier
  RAGWEED = 'ragweed'  # Ambroisie


class PollenSeverity(StrEnum):
  ZERO = 'zero'
  VERY_LOW = 'very_low'
  LOW = 'low'
  MODERATE = 'moderate'
  HIGH = 'high'
  VERY_HIGH = 'very_high'
  EXTREMELY_HIGH = 'extremely_high'


class PollenDetail(BaseModel):
  level: float = Field(..., description='Measured pollen concentration in grains/m³')
  severity: PollenSeverity = Field(..., description='SILAM severity classification for this pollen type')


class PollenData(BaseModel):
  pollen_names: list[PollenName] | None = Field(..., description='List of pollen types detected')
  units: str = Field(..., description='Units of measurement for pollen concentration (e.g., grains/m³)')
  dominant_pollen: PollenName | None = Field(
    default=None,
    description='Pollen type with the highest current concentration.',
  )
  details: dict[PollenName, PollenDetail] = Field(default_factory=dict, description='Current pollen details by type.')
