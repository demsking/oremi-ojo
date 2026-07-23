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
import datetime
import logging
from typing import Any
from typing import ClassVar

from openmeteo_sdk.Unit import Unit  # type: ignore[import-untyped]

from ..models.pollen import PollenData
from ..models.pollen import PollenDetail
from ..models.pollen import PollenForecastData
from ..models.pollen import PollenForecastItem
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
  DEFAULT_UNIT = 'grains/m³'

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
    PollenName.MUGWORT: _TREE,
    # Groupe 2 : Graminées + Ambroisie
    PollenName.GRASS: _GRASS,
    PollenName.RAGWEED: _GRASS,
  }

  UNIT_LABELS: ClassVar[dict[int, str]] = {
    Unit.grains_per_cubic_metre: DEFAULT_UNIT,
  }

  def __init__(self, provider: OpenMeteoProvider) -> None:
    self.provider = provider

  @property
  def name(self) -> str:
    return self.SOURCE

  @staticmethod
  def _classify_pollen(pollen_name: PollenName, value: float) -> PollenSeverity:
    # Récupération des 5 seuils configurés
    v_low, low, mod, high, v_high = PollenService.SILAM_THRESHOLDS[pollen_name]

    if value < v_low:
      return PollenSeverity.ZERO

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
    return cls.UNIT_LABELS.get(unit, cls.DEFAULT_UNIT)

  def _fetch_from_api(self, lon: float, lat: float, target_field: str, timezone: str | None = None) -> Any:
    """Helper method to encapsulate the Open-Meteo API call."""
    params = {
      'latitude': lat,
      'longitude': lon,
      target_field: list(self.POLLEN_FIELDS.values()),
    }

    if timezone:
      params['timezone'] = timezone

    responses = self.provider.client.weather_api(
      'https://air-quality-api.open-meteo.com/v1/air-quality',
      params=params,
    )

    return responses[0]

  async def fetch(self, lon: float, *, lat: float) -> PollenData | None:
    logger.info(f'Fetching pollens data for lon={lon} lat={lat}')

    response = self._fetch_from_api(lon, lat, 'current')
    current = response.Current()

    pollen_details = {}
    current_units = {}

    for index, pollen_name in enumerate(self.POLLEN_FIELDS.keys()):
      variable = current.Variables(index) if current else None
      value = float(variable.Value() if variable else 0)

      current_units[pollen_name] = self._unit_label(variable.Unit()) if variable else self.DEFAULT_UNIT
      pollen_details[pollen_name] = PollenDetail(
        level=value,
        severity=self._classify_pollen(pollen_name, value),
      )

    pollen_names = [name for name, detail in pollen_details.items() if (detail.level or 0) > 0]
    dominant_pollen = max(pollen_details.keys(), key=lambda k: pollen_details[k].level or 0.0) if pollen_details else None

    if dominant_pollen and (pollen_details[dominant_pollen].level or 0) <= 0:
      dominant_pollen = None

    return PollenData(
      pollen_names=pollen_names or None,
      units=current_units.get(dominant_pollen, self.DEFAULT_UNIT) if dominant_pollen else self.DEFAULT_UNIT,
      dominant_pollen=dominant_pollen,
      details=pollen_details,
    )

  async def forecast(self, lon: float, *, lat: float, timezone: str | None = 'auto') -> PollenForecastData | None:
    logger.info(f'Fetching pollens forecast data for lon={lon} lat={lat}')

    response = self._fetch_from_api(lon, lat, 'hourly', timezone or 'auto')
    hourly = response.Hourly()
    utc_offset_seconds = response.UtcOffsetSeconds()

    hourly_data: dict[PollenName, list[float]] = {}
    hourly_units: dict[PollenName, str] = {}

    for index, pollen_name in enumerate(self.POLLEN_FIELDS.keys()):
      variable = hourly.Variables(index) if hourly else None
      hourly_data[pollen_name] = variable.ValuesAsNumpy().tolist() if variable else []
      hourly_units[pollen_name] = self._unit_label(variable.Unit()) if variable else self.DEFAULT_UNIT

    start_time = hourly.Time() if hourly else 0
    interval = (hourly.Interval() if hourly else 3600) or 3600
    length = len(next(iter(hourly_data.values()), []))

    forecast_items = []
    units = next(iter(hourly_units.values()), self.DEFAULT_UNIT)

    for i in range(length):
      utc_time = datetime.datetime.fromtimestamp(start_time + i * interval, tz=datetime.UTC)
      local_time = utc_time + datetime.timedelta(seconds=utc_offset_seconds)

      details: dict[PollenName, PollenDetail] = {}

      for pollen_name, values in hourly_data.items():
        if i < len(values):
          value = float(values[i])

          if value > 0:
            details[pollen_name] = PollenDetail(
              level=value,
              severity=self._classify_pollen(pollen_name, value),
            )

      dominant_pollen = max(details.keys(), key=lambda k: details[k].level or 0.0) if details else None

      forecast_items.append(
        PollenForecastItem(
          time=local_time.isoformat(),
          dominant_pollen=dominant_pollen,
          details=details,
        )
      )

    return PollenForecastData(
      units=units,
      forecast=forecast_items,
    )
