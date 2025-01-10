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
import functools
from dataclasses import dataclass
from datetime import timedelta

from dataclasses_json import dataclass_json
from dataclasses_json import DataClassJsonMixin
from dataclasses_json import Undefined

from .http import HttpClient

__all__ = [
  'Geocode',
  'Location',
  'NotFoundLocationException',
]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Address(DataClassJsonMixin):
  country: str
  country_code: str
  region: str | None = None
  postcode: int | str | None = None
  road: str | None = None
  town: str | None = None
  municipality: str | None = None
  county: str | None = None
  state: str | None = None
  city: str | None = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Location(DataClassJsonMixin):
  type: str
  name: str
  boundingbox: list[float]
  lat: float
  lon: float
  addresstype: str
  display_name: str
  address: Address

  def __str__(self) -> str:
    if self.display_name:
      return self.display_name

    info = [
      self.address.city,
      self.address.region,
      self.address.country,
    ]

    return ', '.join(info)


class NotFoundLocationException(Exception):
  """
  Raised when location is not found.
  """


class Geocode:
  _http_client: HttpClient | None = None

  @classmethod
  @functools.lru_cache
  def _get_http_client(cls) -> HttpClient:
    return HttpClient(
      base_url='https://nominatim.openstreetmap.org',
      expire_after=timedelta(days=30),
    )

  @classmethod
  async def find(cls, query: str, addressdetails: bool = True, country_codes: list[str] | str | None = None, language_result: str = 'en') -> Location:
    """
    Return a location point by address.

    Args:
      query (str): Free-form query string to search for.
      addressdetails (bool): If True, include address details in Location.raw.
      country_codes (list[str] | str | None): Limit search results to specific countries.
      language_result (str): Preferred language order for showing search results.

    Returns:
      Location | None: A Location object if found, otherwise None.
    """

    params = {
      'q': query,
      'format': 'json',
      'addressdetails': 1 if addressdetails else 0,
    }

    if isinstance(country_codes, list) and len(country_codes) > 0:
      params['countrycodes'] = ','.join(country_codes)

    # See https://nominatim.org/release-docs/develop/api/Search
    response = await cls._get_http_client().get(
      url='/search',
      params=params,
      headers={
        'Accept-Language': language_result,
      },
    )

    result = Location.schema().loads(response.text, many=True)

    if len(result) > 0:
      return result[0]

    raise NotFoundLocationException

  @classmethod
  async def reverse(
    cls,
    *,
    lat: float,
    lon: float,
    addressdetails: bool = True,
    language_result: str = 'en',
  ) -> Location:
    """
    Return a location by latitude and longitude (reverse geocoding).

    Args:
      lat (float): Latitude of the location.
      lon (float): Longitude of the location.
      addressdetails (bool): If True, include address details in Location.raw.
      language_result (str): Preferred language order for showing search results.

    Returns:
      Location: A Location object with address details.

    Raises:
      NotFoundLocationException: If no location is found for the given coordinates.
    """
    params = {
      'lat': lat,
      'lon': lon,
      'format': 'json',
      'addressdetails': 1 if addressdetails else 0,
    }

    # See https://nominatim.org/release-docs/develop/api/Reverse
    response = await cls._get_http_client().get(
      url='/reverse',
      params=params,
      headers={
        'Accept-Language': language_result,
      },
    )

    data = response.json()

    if not data or 'error' in data:
      raise NotFoundLocationException('No location found for the given coordinates.')

    # Parse the response into a Location object
    location = Location(
      type=data.get('type', ''),
      name=data.get('name', ''),
      boundingbox=data.get('boundingbox', []),
      lat=float(data.get('lat', 0)),
      lon=float(data.get('lon', 0)),
      addresstype=data.get('addresstype', ''),
      display_name=data.get('display_name', ''),
      address=Address.schema().load(data.get('address', {})),
    )

    return location
