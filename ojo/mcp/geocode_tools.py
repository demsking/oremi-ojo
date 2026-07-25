# Copyright 2026 Sébastien Demanou. All Rights Reserved.
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
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from ..core.geo import Geocode
from ..core.geo import Location
from ..core.geo import NotFoundLocationException


def register_geocode_mcp_tools(mcp: FastMCP) -> None:
  @mcp.tool(
    title='Search Locations',
    name='search_locations',
    description='Look up location coordinates and details for a query string.',
  )
  async def search_locations(
    query: str,
    limit: int = 10,
  ) -> list[Location]:
    try:
      return await Geocode.search(query=query, limit=limit)
    except Exception as exception:
      raise ToolError(f'Error searching locations: {exception}') from exception

  @mcp.tool(
    title='Reverse Geocode',
    name='reverse_geocode',
    description='Retrieve location details by latitude and longitude.',
  )
  async def reverse_geocode(
    lat: float,
    lon: float,
  ) -> Location:
    try:
      return await Geocode.reverse(lat=lat, lon=lon)
    except NotFoundLocationException as exception:
      raise ToolError('No location found for the given coordinates.') from exception
    except Exception as exception:
      raise ToolError(f'Error performing reverse geocoding: {exception}') from exception
