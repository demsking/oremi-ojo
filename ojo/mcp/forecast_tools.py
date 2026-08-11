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
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from ..models.forecast import CurrentWeatherData
from ..models.forecast import DailyForecastResponse
from ..models.forecast import HourlyForecastResponse
from ..models.forecast import SunTimes
from ..models.forecast import WeatherAlert
from ..services.forecast_service import ForecastService
from ..services.forecast_service import TemperatureUnit


def register_forecast_mcp_tools(mcp: MCPServer[None], service: ForecastService) -> None:
  @mcp.tool(
    title='Get Current Weather',
    name='get_current_weather',
    description='Retrieve current weather conditions for a specific location.',
  )
  async def get_current_weather(
    lat: float,
    lon: float,
    timezone: str = 'auto',
    temperature_unit: TemperatureUnit = 'celsius',
  ) -> CurrentWeatherData:
    try:
      return await service.fetch_current_weather(
        lat=lat,
        lon=lon,
        timezone=timezone,
        temperature_unit=temperature_unit,
      )
    except Exception as exception:
      raise ToolError(f'Error fetching current weather: {exception}') from exception

  @mcp.tool(
    title='Get Hourly Forecast',
    name='get_hourly_forecast',
    description='Retrieve hourly weather forecast for the next hours.',
  )
  async def get_hourly_forecast(
    lat: float,
    lon: float,
    timezone: str = 'auto',
    temperature_unit: TemperatureUnit = 'celsius',
    hours: int = 24,
  ) -> HourlyForecastResponse:
    try:
      return await service.fetch_hourly_forecast(
        lat=lat,
        lon=lon,
        timezone=timezone,
        temperature_unit=temperature_unit,
        hours=hours,
      )
    except Exception as exception:
      raise ToolError(f'Error fetching hourly forecast: {exception}') from exception

  @mcp.tool(
    title='Get Daily Forecast',
    name='get_daily_forecast',
    description='Retrieve daily weather forecast for the next days.',
  )
  async def get_daily_forecast(
    lat: float,
    lon: float,
    timezone: str = 'auto',
    temperature_unit: TemperatureUnit = 'celsius',
    days: int = 7,
  ) -> DailyForecastResponse:
    try:
      return await service.fetch_daily_forecast(
        lat=lat,
        lon=lon,
        timezone=timezone,
        temperature_unit=temperature_unit,
        days=days,
      )
    except Exception as exception:
      raise ToolError(f'Error fetching daily forecast: {exception}') from exception

  @mcp.tool(
    title='Get Weather Alerts',
    name='get_weather_alerts',
    description='Retrieve severe weather alerts or warnings for a specific location.',
  )
  async def get_weather_alerts(
    lat: float,
    lon: float,
    timezone: str = 'auto',
  ) -> list[WeatherAlert]:
    try:
      return await service.fetch_weather_alerts(
        lat=lat,
        lon=lon,
        timezone=timezone,
      )
    except Exception as exception:
      raise ToolError(f'Error fetching weather alerts: {exception}') from exception

  @mcp.tool(
    title='Get Sun Times',
    name='get_sun_times',
    description='Retrieve sunrise and sunset times for a specific location.',
  )
  async def get_sun_times(
    lat: float,
    lon: float,
    timezone: str = 'auto',
    days: int = 7,
  ) -> list[SunTimes]:
    try:
      return await service.fetch_sun_times(
        lat=lat,
        lon=lon,
        timezone=timezone,
        days=days,
      )
    except Exception as exception:
      raise ToolError(f'Error fetching sun times: {exception}') from exception
