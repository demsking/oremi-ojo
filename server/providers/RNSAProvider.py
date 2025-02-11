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
from datetime import timedelta
from typing import ClassVar

from ..core.geo import Geocode
from ..core.http import HttpClient
from ..core.logger import logger
from ..core.provider import Provider
from ..models.rnsa import PollenResponse
from ..models.rnsa import RNSAResponse


class RNSAProvider(Provider):
  """
  The National Aerobiological Surveillance Network (R.N.S.A.) is an association
  under the law of 1901, created in 1996 to continue the work carried out since
  1985 by the Aerobiology Laboratory of the Pasteur Institute in Paris.

  It provides information about pollens for France.

  See https://pollens.fr/
  """

  LEVEL: ClassVar[dict[int, str]] = {
    0: 'unknown',
    1: 'low',
    2: 'medium',
    3: 'high',
  }

  def __init__(self) -> None:
    super().__init__('Réseau National de Surveillance Aérobiologique')
    self.client = HttpClient(base_url='https://pollens.fr', expire_after=timedelta(minutes=60))

  async def fetch(self, *, lon: float, lat: float) -> PollenResponse:
    location = await Geocode.reverse(lat=lat, lon=lon)

    if location and location.address.country_code == 'fr' and location.address.postcode:
      code = f'{location.address.postcode}'[0:2]
      logger.info(f'Fetching pollens data for French department {code}')
      response = await self.client.get(f'/risks/thea/counties/{code}')

      data = RNSAResponse.from_json(response.text)
      pollen_names = [pollen.pollenName for pollen in data.risks if pollen.level == data.riskLevel]
      risk = RNSAProvider.LEVEL[data.riskLevel]

      return PollenResponse(
        level=data.riskLevel,
        risk=risk,
        pollen_names=', '.join(pollen_names),
      )

    return PollenResponse(level=0, risk='unknown', pollen_names='')
