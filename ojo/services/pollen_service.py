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
from typing import ClassVar

from openmeteo_sdk.Unit import Unit

from ..core.geo import Location
from ..models.pollen import PollenData
from ..models.pollen import PollenDetail
from ..models.pollen import PollenName
from ..models.pollen import PollenSeverity
from ..providers.OpenMeteoProvider import OpenMeteoProvider

logger = logging.getLogger(__name__)


class PollenService:
  """
  Open-Meteo Air Quality API (pollen)

  Pollen for various plants. Only available in Europe as provided by CAMS European Air Quality forecast.

  See https://open-meteo.com/en/docs/air-quality-api
  """

  SOURCE = 'Copernicus Atmosphere Monitoring Service (CAMS)'

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

  UNIT_LABELS: ClassVar[dict[int, str]] = {
    Unit.grains_per_cubic_metre: 'grains/m³',
  }

  def __init__(self, provider: OpenMeteoProvider) -> None:
    self.provider = provider

  @property
  def name(self) -> str:
    return self.SOURCE

  @staticmethod
  def _classify_pollen(pollen_name: PollenName, value: float) -> PollenSeverity:
    # Récupération des 5 seuils configurés
    thresholds = PollenService.SILAM_THRESHOLDS[pollen_name]
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

  @classmethod
  def _unit_label(cls, unit: int) -> str:
    return cls.UNIT_LABELS.get(unit, 'grains/m³')

  async def fetch(self, lon: float, *, lat: float) -> PollenData | None:
    logger.info(f'Fetching pollens data for lon={lon} lat={lat}')

    responses = self.provider.client.weather_api(
      'https://air-quality-api.open-meteo.com/v1/air-quality',
      params={
        'latitude': lat,
        'longitude': lon,
        'current': list(PollenService.POLLEN_FIELDS.values()),
      },
    )

    current = responses[0].Current()
    current_values = {}
    current_units = {}

    for index, (pollen_name, _field) in enumerate(PollenService.POLLEN_FIELDS.items()):
      variable = current.Variables(index) if current else None  # type: ignore
      current_values[pollen_name] = float(variable.Value() if variable else 0)
      current_units[pollen_name] = self._unit_label(variable.Unit()) if variable else 'grains/m³'

    pollen_levels = {pollen_name: current_values[pollen_name] for pollen_name in PollenService.POLLEN_FIELDS}

    pollen_details = {
      pollen_name: PollenDetail(
        level=value,
        severity=PollenService._classify_pollen(pollen_name, value),
      )
      for pollen_name, value in pollen_levels.items()
    }

    pollen_names = [name for name, value in pollen_levels.items() if value > 0]
    dominant_pollen = max(pollen_levels, key=lambda pollen_name: pollen_levels[pollen_name]) if pollen_levels else None

    if dominant_pollen and pollen_levels[dominant_pollen] <= 0:
      dominant_pollen = None

    return PollenData(
      pollen_names=pollen_names or None,
      units=current_units.get(dominant_pollen, 'grains/m³') if dominant_pollen else 'grains/m³',
      dominant_pollen=dominant_pollen,
      details=pollen_details,
    )

  async def fetch_location(self, location: Location) -> PollenData | None:
    return await self.fetch(lon=location.lon, lat=location.lat)
