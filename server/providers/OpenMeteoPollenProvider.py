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
import logging
from datetime import timedelta
from typing import ClassVar

from ..core.controller import Controller
from ..core.geo import Location
from ..core.http import HttpClient
from ..core.provider import Provider
from ..models.pollen import PollenData
from ..models.pollen import PollenDetail
from ..models.pollen import PollenName
from ..models.pollen import PollenSeverity


class OpenMeteoPollenProvider(Provider):
  """
  Open-Meteo Air Quality API (pollen)

  Pollen for various plants. Only available in Europe as provided by CAMS European Air Quality forecast.

  See https://open-meteo.com/en/docs/air-quality-api
  """

  POLLEN_FIELDS: ClassVar[dict[PollenName, str]] = {
    PollenName.ALDER: 'alder_pollen',
    PollenName.BIRCH: 'birch_pollen',
    PollenName.GRASS: 'grass_pollen',
    PollenName.MUGWORT: 'mugwort_pollen',
    PollenName.OLIVE: 'olive_pollen',
    PollenName.RAGWEED: 'ragweed_pollen',
  }

  # tuple(zero_limit, very_low, low, moderate, high) → au-delà = very_high
  # Groupe 1 — Arbres + Armoise (EAACI/SILAM : saison ≥10, pic ≥100)
  _TREE = (1.0, 10.0, 50.0, 100.0, 500.0)

  # Groupe 2 — Graminées + Ambroisie (EAACI/SILAM : saison ≥3, pic ≥50)
  _GRASS = (1.0, 3.0, 15.0, 50.0, 200.0)

  SILAM_THRESHOLDS: ClassVar[dict[PollenName, tuple[float, float, float, float, float]]] = {
    # Groupe 1 : Arbres + Armoise
    PollenName.ALDER: _TREE,
    PollenName.BIRCH: _TREE,
    PollenName.OLIVE: _TREE,
    PollenName.MUGWORT: _TREE,  # ← corrigé (était custom, doit être = arbres)
    # Groupe 2 : Graminées + Ambroisie
    PollenName.GRASS: _GRASS,
    PollenName.RAGWEED: _GRASS,  # ← corrigé (était custom, doit être = grass)
  }

  def __init__(self, controller: Controller, logger: logging.Logger) -> None:
    super().__init__('Copernicus Atmosphere Monitoring Service (CAMS)', controller, logger)

    self.client = HttpClient(
      base_url='https://air-quality-api.open-meteo.com',
      expire_after=timedelta(minutes=30),
      logger=logger,
    )

  @staticmethod
  def _classify_pollen(pollen_name: PollenName, value: float) -> PollenSeverity:
    # Récupération des 5 seuils configurés
    thresholds = OpenMeteoPollenProvider.SILAM_THRESHOLDS[pollen_name]
    v_low, low, mod, high, v_high = thresholds

    if value < v_low:
      return PollenSeverity.ZERO  # < 1.0

    if value < low:
      return PollenSeverity.VERY_LOW

    if value < mod:
      return PollenSeverity.LOW

    if value < high:
      return PollenSeverity.MODERATE

    if value < v_high:
      return PollenSeverity.HIGH

    return PollenSeverity.EXTREMELY_HIGH

  async def fetch(self, lon: float, *, lat: float) -> PollenData | None:
    self.logger.info(f'Fetching pollens data for lon={lon} lat={lat}')
    response = await self.client.get(
      url='/v1/air-quality',
      params={
        'latitude': lat,
        'longitude': lon,
        'current': ','.join(OpenMeteoPollenProvider.POLLEN_FIELDS.values()),
      },
    )

    response_data = response.json()
    current = response_data.get('current', {})
    current_units = response_data.get('current_units', {})

    pollen_levels = {
      pollen_name: float(current.get(field, 0) or 0) for pollen_name, field in OpenMeteoPollenProvider.POLLEN_FIELDS.items()
    }

    pollen_units = {
      pollen_name: str(current_units.get(field, 'grains/m³'))
      for pollen_name, field in OpenMeteoPollenProvider.POLLEN_FIELDS.items()
    }

    pollen_details = {
      pollen_name: PollenDetail(
        level=value,
        severity=OpenMeteoPollenProvider._classify_pollen(pollen_name, value),
      )
      for pollen_name, value in pollen_levels.items()
    }

    pollen_names = [name for name, value in pollen_levels.items() if value > 0]
    dominant_pollen = max(pollen_levels, key=lambda pollen_name: pollen_levels[pollen_name]) if pollen_levels else None

    if dominant_pollen and pollen_levels[dominant_pollen] <= 0:
      dominant_pollen = None

    return PollenData(
      pollen_names=pollen_names or None,
      units=pollen_units.get(dominant_pollen, 'grains/m³') if dominant_pollen else 'grains/m³',
      dominant_pollen=dominant_pollen,
      details=pollen_details,
    )

  async def fetch_location(self, location: Location) -> PollenData | None:
    return await self.fetch(lon=location.lon, lat=location.lat)
