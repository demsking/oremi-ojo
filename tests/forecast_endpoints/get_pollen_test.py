# Copyright 2025-2026 Sébastien Demanou. All Rights Reserved.
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
from fastapi.testclient import TestClient

from ojo import app


client = TestClient(app, backend='asyncio')


async def test_get_pollen_pollen_get():
  """Get Pollen"""
  path = '/api/pollen?lat=48.8534951&lon=2.3483915'
  response = client.get(path)
  assert response.status_code == 200


async def test_get_pollen_forecast_pollen_forecast_get():
  """Get Pollen Forecast"""
  path = '/api/pollen/forecast?lat=48.8534951&lon=2.3483915'
  response = client.get(path)
  assert response.status_code == 200


def test_pollen_classify_nan_or_none():
  """Classifying None or NaN pollen level should return ZERO severity."""
  import math
  from ojo.models.pollen import PollenName, PollenSeverity
  from ojo.services.pollen_service import PollenService

  assert PollenService._classify_pollen(PollenName.BIRCH, None) == PollenSeverity.ZERO
  assert PollenService._classify_pollen(PollenName.BIRCH, math.nan) == PollenSeverity.ZERO
