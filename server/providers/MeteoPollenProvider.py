# Copyright 2025 Sébastien Demanou. All Rights Reserved.
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
from ..core.geo import Geocode
from ..core.geo import Location
from ..core.http import HttpClient
from ..core.provider import Provider
from ..models.pollen import DailyPollenForecast
from ..models.pollen import PollenData


class MeteoPollenProvider(Provider):
  """
  Météo Pollen is an innovative service that provides real-time information on
  pollen levels in the air, helping allergy sufferers anticipate high-risk
  periods and manage their symptoms more effectively. It relies on a network of
  physical sensors deployed across cities to measure pollen concentrations,
  combined with real-time analysis of different pollen types in the area,
  offering accurate forecasts and personalized alerts to reduce allergic
  reactions.

  It provides information about pollens for France.

  See https://meteo-pollen.com
  """

  LEVEL: ClassVar[dict[int, str]] = {
    0: 'unknown',
    1: 'low',
    2: 'medium',
    3: 'high',
  }

  def __init__(self, controller: Controller, logger: logging.Logger) -> None:
    super().__init__('Météo Pollen', controller, logger)

    self.client = HttpClient(
      base_url='https://meteo-pollen.com/api',
      expire_after=timedelta(minutes=60),
      logger=logger,
    )

  async def fetch(self, *, lon: float, lat: float) -> PollenData | None:
    location = await Geocode.reverse(lat=lat, lon=lon)

    return await self.fetch_location(location) if location else None

  async def fetch_location(self, location: Location) -> PollenData | None:
    if location.address.country_code == 'fr':
      self.logger.info(f'Fetching pollens data for {location}')
      response = await self.client.get(
        url='/predictions',
        params={
          'lat': location.lat,
          'lon': location.lon,
          'forecastDays': 1,
        },
      )

      data = response.json()
      data_list = [DailyPollenForecast.model_validate(item) for item in data]
      max_risk_level: int = max(pollen.riskLevel for pollen in data_list)
      pollen_names = [pollen.name for pollen in data_list if pollen.riskLevel > 0]
      risk = MeteoPollenProvider.LEVEL[max_risk_level]

      return PollenData(
        level=max_risk_level,
        risk=risk,  # type: ignore
        pollen_names=pollen_names or None,
      )

    return None
