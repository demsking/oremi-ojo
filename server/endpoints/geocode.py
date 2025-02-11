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
from fastapi import FastAPI
from fastapi import Query

from ..core.geo import Geocode
from ..core.geo import Location


def create_geocode_endpoints(tag: str, api: FastAPI) -> None:
  @api.get('/search', tags=[tag])
  async def search(
    query: str = Query(
      description='The search query to find a location. This can be a city name, address, or landmark.',
      examples=['Paris, France'],
    ),
  ) -> Location:
    """
    Retrieve location details by a search query.

    This endpoint allows you to search for a location by providing a query string, such as a city name,
    address, or landmark. It returns detailed information about the location, including its coordinates,
    bounding box, and address details.
    """
    return await Geocode.find(query)

  @api.get('/reverse', tags=[tag])
  async def reverse(
    lat: float = Query(
      description='The latitude of the location for which details are requested.',
      examples=[48.8534951],
    ),
    lon: float = Query(
      description='The longitude of the location for which details are requested.',
      examples=[2.3483915],
    ),
  ) -> Location:
    """
    Retrieve location details by latitude and longitude (reverse geocoding).

    This endpoint allows you to find a location by providing its latitude and longitude. It returns
    detailed information about the location, including its name, bounding box, and address details.
    """
    return await Geocode.reverse(lat=lat, lon=lon)
