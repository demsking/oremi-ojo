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

from ..models.forecast import CurrentWeatherData
from ..models.forecast import DailyForecastResponse
from ..models.forecast import HourlyForecastResponse
from ..models.forecast import SunTimes
from ..models.forecast import WeatherAlert
from ..services.forecast_service import ForecastService
from ..services.forecast_service import TemperatureUnit


def register_forecast_mcp_tools(mcp: FastMCP, service: ForecastService) -> None:
  @mcp.tool(name='get_current_weather')
  async def get_current_weather(
    lat: float,
    lon: float,
    timezone: str = 'auto',
    temperature_unit: TemperatureUnit = 'celsius',
  ) -> CurrentWeatherData:
    """Retrieve current weather conditions for a specific location.

    This tool fetches current temperature, humidity, wind speed, wind direction,
    apparent temperature, weather code, and day/night status.
    """
    try:
      return await service.fetch_current_weather(
        lat=lat,
        lon=lon,
        timezone=timezone,
        temperature_unit=temperature_unit,
      )
    except Exception as exception:
      raise ToolError(f'Error fetching current weather: {exception}') from exception

  @mcp.tool(name='get_hourly_forecast')
  async def get_hourly_forecast(
    lat: float,
    lon: float,
    timezone: str = 'auto',
    temperature_unit: TemperatureUnit = 'celsius',
    hours: int = 24,
  ) -> HourlyForecastResponse:
    """Retrieve hourly weather forecast for the next hours.

    This tool fetches hourly predictions for temperature, humidity, wind, and
    precipitation starting from the current hour.
    """
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

  @mcp.tool(name='get_daily_forecast')
  async def get_daily_forecast(
    lat: float,
    lon: float,
    timezone: str = 'auto',
    temperature_unit: TemperatureUnit = 'celsius',
    days: int = 7,
  ) -> DailyForecastResponse:
    """Retrieve daily weather forecast for the next days.

    This tool fetches daily maximum and minimum temperatures, total rain,
    wind speeds, and UV index.
    """
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

  @mcp.tool(name='get_weather_alerts')
  async def get_weather_alerts(
    lat: float,
    lon: float,
    timezone: str = 'auto',
  ) -> list[WeatherAlert]:
    """Retrieve severe weather alerts or warnings for a specific location.

    This tool analyzes upcoming forecast data to detect severe weather conditions
    such as extreme temperatures, high winds, heavy rain, or high UV levels.
    """
    try:
      return await service.fetch_weather_alerts(
        lat=lat,
        lon=lon,
        timezone=timezone,
      )
    except Exception as exception:
      raise ToolError(f'Error fetching weather alerts: {exception}') from exception

  @mcp.tool(name='get_sun_times')
  async def get_sun_times(
    lat: float,
    lon: float,
    timezone: str = 'auto',
    days: int = 7,
  ) -> list[SunTimes]:
    """Retrieve sunrise and sunset times for a specific location.

    This tool fetches the sunrise and sunset times for the specified coordinates
    over the next few days.
    """
    try:
      return await service.fetch_sun_times(
        lat=lat,
        lon=lon,
        timezone=timezone,
        days=days,
      )
    except Exception as exception:
      raise ToolError(f'Error fetching sun times: {exception}') from exception
