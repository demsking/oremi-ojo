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
from ..models.pollen import PollenForecastData
from ..services.pollen_service import PollenService


def register_pollen_mcp_tools(mcp: FastMCP, service: PollenService) -> None:
  @mcp.tool(
    title='Get Current Pollen',
    name='get_current_pollen',
    description='Retrieve current pollen data for a specific location.',
  )
  async def get_current_pollen(
    lat: float,
    lon: float,
  ) -> PollenData:
    try:
      result = await service.fetch(lat=lat, lon=lon)

      if result is None:
        raise ToolError('No pollen data found for the given coordinates.')

      return result
    except Exception as exception:
      if isinstance(exception, ToolError):
        raise

      raise ToolError(f'Error fetching pollen data: {exception}') from exception

  @mcp.tool(
    title='Get Pollen Forecast',
    name='get_pollen_forecast',
    description='Retrieve hourly pollen forecast for a specific location.',
  )
  async def get_pollen_forecast(
    lat: float,
    lon: float,
    timezone: str = 'auto',
  ) -> PollenForecastData:
    try:
      result = await service.forecast(lat=lat, lon=lon, timezone=timezone)

      if result is None:
        raise ToolError('No pollen forecast data found for the given coordinates.')

      return result
    except Exception as exception:
      if isinstance(exception, ToolError):
        raise

      raise ToolError(f'Error fetching pollen forecast data: {exception}') from exception
