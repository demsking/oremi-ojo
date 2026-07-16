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

from ..models.pollen import PollenData
from ..services.pollen_service import PollenService


def register_pollen_mcp_tools(mcp: FastMCP, service: PollenService) -> None:
  @mcp.tool(name='get_pollen')
  async def get_pollen(
    lat: float,
    lon: float,
  ) -> PollenData:
    """Retrieve current pollen data for a specific location.

    This tool provides information on the presence and concentration levels
    of various airborne pollens (like grass, birch, olive, ragweed, etc.)
    at the given geographic coordinates.
    """
    try:
      res = await service.fetch(lat=lat, lon=lon)

      if res is None:
        raise ToolError('No pollen data found for the given coordinates.')

      return res
    except Exception as exception:
      if isinstance(exception, ToolError):
        raise

      raise ToolError(f'Error fetching pollen data: {exception}') from exception
