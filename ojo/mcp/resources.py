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

from ..models.air_quality import EAQIData
from ..models.air_quality import USAQIData
from ..models.forecast import CurrentWeatherData
from ..models.forecast import WeatherAlert
from ..models.pollen import PollenData
from ..services.air_quality_service import AirQualityService
from ..services.forecast_service import ForecastService
from ..services.pollen_service import PollenService


def register_mcp_resources(
  mcp: FastMCP,
  forecast_service: ForecastService,
  air_quality_service: AirQualityService,
  pollen_service: PollenService,
) -> None:
  @mcp.resource('weather:///{lat}/{lon}/current', mime_type='application/json')
  async def get_current_weather_resource(lat: str, lon: str) -> CurrentWeatherData:
    """Retrieve current weather conditions as a resource."""
    return await forecast_service.fetch_current_weather(
      lat=float(lat),
      lon=float(lon),
    )

  @mcp.resource('weather:///{lat}/{lon}/alerts', mime_type='application/json')
  async def get_weather_alerts_resource(lat: str, lon: str) -> list[WeatherAlert]:
    """Retrieve active severe weather alerts as a resource."""
    return await forecast_service.fetch_weather_alerts(
      lat=float(lat),
      lon=float(lon),
    )

  @mcp.resource('weather:///{lat}/{lon}/air-quality', mime_type='application/json')
  async def get_air_quality_resource(lat: str, lon: str) -> EAQIData | USAQIData:
    """Retrieve current air quality indexes (AQI) as a resource."""
    return await air_quality_service.fetch(
      lat=float(lat),
      lon=float(lon),
    )

  @mcp.resource('weather:///{lat}/{lon}/pollen', mime_type='application/json')
  async def get_pollen_resource(lat: str, lon: str) -> PollenData | None:
    """Retrieve pollen allergen data as a resource."""
    return await pollen_service.fetch(
      lat=float(lat),
      lon=float(lon),
    )
