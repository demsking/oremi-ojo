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


class Risk(BaseModel):
  pollenName: str = Field(..., description='Name of the pollen type')
  level: int = Field(..., description='Risk level associated with the pollen (e.g., 0-5)')


class RNSAResponse(BaseModel):
  countyName: str = Field(..., description='Name of the county')
  countyNumber: int = Field(..., description='Identification number of the county')
  risks: list[Risk] = Field(..., description='List of risks for various pollen types')
  riskLevel: int = Field(..., description='Overall risk level for the county')


class PollenData(BaseModel):
  pollen_names: list[str] | None = Field(..., description='List of pollen types detected')
  level: int = Field(..., description='Aggregated pollen level')
  risk: Literal['unknown', 'low', 'medium', 'high'] = Field(..., description='Categorized risk level based on pollen level')
