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
from functools import lru_cache

import httpx
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from .settings import get_settings


class LocationAddress(BaseModel):
  model_config = ConfigDict(extra='ignore')

  country: str = Field(..., description='Full country name')
  country_code: str = Field(..., description='ISO country code')
  region: str | None = Field(None, description='Administrative region or province')
  postcode: int | str | None = Field(None, description='Postal code of the location')
  road: str | None = Field(None, description='Street or road name')
  town: str | None = Field(None, description='Town name, if applicable')
  municipality: str | None = Field(None, description='Municipality or local administrative division')
  county: str | None = Field(None, description='County or department')
  state: str | None = Field(None, description='State or large administrative region')
  city: str | None = Field(None, description='City name')


class Location(BaseModel):
  type: str = Field(..., description='Type of the geographical object (e.g., "city", "village")')
  name: str = Field(..., description='Common name of the location')
  boundingbox: list[float] = Field(..., description='Bounding box of the location as [south, north, west, east]')
  lat: float = Field(..., description='Latitude coordinate')
  lon: float = Field(..., description='Longitude coordinate')
  addresstype: str = Field(..., description='Type of the address (e.g., "administrative", "residential")')
  display_name: str = Field(..., description='Human-readable full name of the location')
  address: LocationAddress = Field(..., description='Structured address information')

  def __str__(self) -> str:
    return self.display_name


class NotFoundLocationException(Exception):
  """
  Raised when location is not found.
  """


@lru_cache
def _get_nominatim_http_client() -> httpx.AsyncClient:
  settings = get_settings()

  return httpx.AsyncClient(
    base_url='https://nominatim.openstreetmap.org',
    headers={'User-Agent': settings.http_user_agent},
    timeout=settings.http_request_timeout,
  )


class Geocode:
  @staticmethod
  async def _get(path: str, *, params: dict, language_result: str) -> httpx.Response:
    headers = {
      'Accept-Language': language_result,
    }

    try:
      return await _get_nominatim_http_client().get(url=path, params=params, headers=headers)
    except RuntimeError as exc:
      if 'Event loop is closed' not in str(exc):
        raise

      _get_nominatim_http_client.cache_clear()
      return await _get_nominatim_http_client().get(url=path, params=params, headers=headers)

  @classmethod
  async def search(
    cls,
    query: str,
    limit: int = 10,
    addressdetails: bool = True,
    country_codes: list[str] | str | None = None,
    language_result: str = 'en',
  ) -> list[Location]:
    params = {
      'q': query,
      'limit': limit,
      'format': 'json',
      'addressdetails': 1 if addressdetails else 0,
    }

    if isinstance(country_codes, list) and len(country_codes) > 0:
      params['countrycodes'] = ','.join(country_codes)

    response = await cls._get(
      '/search',
      params=params,
      language_result=language_result,
    )

    result = [Location(**item) for item in response.json()]

    return result

  @classmethod
  async def find(
    cls, query: str, addressdetails: bool = True, country_codes: list[str] | str | None = None, language_result: str = 'en'
  ) -> Location:
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

    result = await cls.search(
      query,
      limit=1,
      country_codes=country_codes,
      language_result=language_result,
    )

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

    response = await cls._get(
      '/reverse',
      params=params,
      language_result=language_result,
    )

    data = response.json()

    if not data or 'error' in data:
      raise NotFoundLocationException('No location found for the given coordinates.')

    # Parse the response into a Location object
    location = Location(
      type=data.get('type', ''),
      name=data.get('name', ''),
      boundingbox=[float(x) for x in data.get('boundingbox', [])],
      lat=float(data.get('lat', 0)),
      lon=float(data.get('lon', 0)),
      addresstype=data.get('addresstype', ''),
      display_name=data.get('display_name', ''),
      address=LocationAddress.model_validate(data.get('address', {})),
    )

    return location
