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
import math
from datetime import datetime
from datetime import timedelta
from datetime import timezone as dt_timezone
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
  def _classify_pollen(pollen_name: PollenName, value: float | None) -> PollenSeverity:
    if value is None or math.isnan(value):
      return PollenSeverity.ZERO

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
      raw_val = variable.Value() if variable else None
      value = None if raw_val is None or math.isnan(raw_val) else float(raw_val)

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

  async def forecast(self, lon: float, *, lat: float, timezone: str = 'auto') -> PollenForecastData | None:
    logger.info(f'Fetching pollen forecast data for lon={lon} lat={lat} timezone={timezone}')

    response = self._fetch_from_api(lon, lat, 'hourly', timezone=timezone)
    hourly = response.Hourly()
    if not hourly:
      return None

    utc_offset_seconds = response.UtcOffsetSeconds()
    tz = dt_timezone(timedelta(seconds=utc_offset_seconds))

    start_time = hourly.Time()
    end_time = hourly.TimeEnd()
    interval = hourly.Interval() or 3600
    timestamps = list(range(start_time, end_time, interval))

    pollen_values: dict[PollenName, list[float | None]] = {}
    pollen_units: dict[PollenName, str] = {}

    for index, pollen_name in enumerate(self.POLLEN_FIELDS.keys()):
      variable = hourly.Variables(index) if hourly else None
      raw_vals = self._values_list(variable) if variable else []
      pollen_values[pollen_name] = [
        None if v is None or math.isnan(v) else float(v) for v in raw_vals
      ]
      pollen_units[pollen_name] = self._unit_label(variable.Unit()) if variable else self.DEFAULT_UNIT

    forecast_items: list[PollenForecastItem] = []
    num_entries = len(timestamps)

    for i in range(num_entries):
      ts = timestamps[i]
      time_str = datetime.fromtimestamp(ts, tz=tz).isoformat()

      details: dict[PollenName, PollenDetail] = {}
      for pollen_name in self.POLLEN_FIELDS.keys():
        values = pollen_values[pollen_name]
        value = values[i] if i < len(values) else None
        details[pollen_name] = PollenDetail(
          level=value,
          severity=self._classify_pollen(pollen_name, value),
        )

      dominant_pollen = max(details.keys(), key=lambda k: details[k].level or 0.0) if details else None
      if dominant_pollen and (details[dominant_pollen].level or 0) <= 0:
        dominant_pollen = None

      forecast_items.append(
        PollenForecastItem(
          time=time_str,
          dominant_pollen=dominant_pollen,
          details=details,
        )
      )

    unit = next(iter(pollen_units.values()), self.DEFAULT_UNIT)

    return PollenForecastData(
      units=unit,
      forecast=forecast_items,
    )

  @staticmethod
  def _values_list(variable: Any) -> list[Any]:
    if not variable:
      return []
    if hasattr(variable, 'ValuesAsNumpy'):
      try:
        return variable.ValuesAsNumpy().tolist()  # type: ignore[no-any-return]
      except RuntimeError:
        pass
    if hasattr(variable, 'ValuesInt64AsNumpy'):
      try:
        return variable.ValuesInt64AsNumpy().tolist()  # type: ignore[no-any-return]
      except RuntimeError:
        pass
    if hasattr(variable, 'ValuesInt64'):
      return [variable.ValuesInt64(i) for i in range(variable.ValuesInt64Length())]
    if hasattr(variable, 'Values'):
      return [variable.Values(i) for i in range(variable.ValuesLength())]
    return []
