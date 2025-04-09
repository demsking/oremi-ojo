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
from fastapi import Header
from fastapi import Query

from ..core.geo import Geocode
from ..core.geo import Location


def create_geocode_endpoints(tag: str, api: FastAPI) -> None:
  example_location = Location.model_validate(
    {
      'place_id': 33097391,
      'licence': 'Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright',
      'osm_type': 'relation',
      'osm_id': 3823474,
      'lat': '3.9474481',
      'lon': '10.8377284',
      'class': 'boundary',
      'type': 'administrative',
      'place_rank': 16,
      'importance': 0.35000999999999993,
      'addresstype': 'town',
      'name': 'Ngog-Mapubi',
      'display_name': 'Ngog-Mapubi, Nyong-et-Kéllé, Centre, Cameroon',
      'address': {
        'town': 'Ngog-Mapubi',
        'county': 'Nyong-et-Kéllé',
        'state': 'Centre',
        'ISO3166-2-lvl4': 'CM-CE',
        'country': 'Cameroon',
        'country_code': 'cm',
      },
      'boundingbox': ['3.8144945', '3.9894203', '10.8120304', '11.0180446'],
    }
  )

  @api.get(
    '/search',
    tags=[tag],
    responses={
      200: {
        'content': {
          'application/json': {
            'example': [example_location],
          },
        },
      },
    },
  )
  async def search(
    language_result: str = Header(
      default='en',
      alias='Accept-Language',
      description='The language of the response. This can be used to specify the preferred language for the search results.',
      examples=['en'],
    ),
    query: str = Query(
      alias='q',
      description='The search query to find a location. This can be a city name, address, or landmark.',
      examples=['Paris, France'],
    ),
    limit: int = Query(
      description='The maximum number of results to return.',
      default=10,
    ),
    country_codes: list[str] | str | None = Query(
      description='List of ISO 3166 country codes to restrict search within.',
      examples=['cm'],
      default=None,
    ),
  ) -> list[Location]:
    """
    Look up a location for a query string using [Nominatim Search API](https://nominatim.org/release-docs/develop/api/Search/).

    The server uses the content of **"Accept-Language"** HTTP header for the language
    of results.

    Preferred language order for showing search results. This may either be a
    simple comma-separated list of language codes or have the same format as the
    "Accept-Language" HTTP header.
    """
    return await Geocode.search(
      query,
      limit=limit,
      country_codes=country_codes,
      language_result=language_result,
    )

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
