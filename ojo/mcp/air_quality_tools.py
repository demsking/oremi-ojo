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

from ..models.air_quality import EAQIData
from ..models.air_quality import USAQIData
from ..services.air_quality_service import AirQualityService


def register_air_quality_mcp_tools(mcp: FastMCP, service: AirQualityService) -> None:
  @mcp.tool(
    title='Get Air Quality',
    name='get_air_quality',
    description='Retrieve current air quality data for a specific location.',
  )
  async def get_air_quality(
    lat: float,
    lon: float,
  ) -> EAQIData | USAQIData:
    try:
      return await service.fetch(lat=lat, lon=lon)
    except Exception as exception:
      raise ToolError(f'Error fetching air quality: {exception}') from exception
