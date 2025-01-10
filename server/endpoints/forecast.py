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

from ..providers.OpenMeteoAirQualityProvider import AirQualityResponse
from ..providers.OpenMeteoAirQualityProvider import OpenMeteoAirQualityProvider
from ..providers.OpenMeteoForecastProvider import ForecastResponse
from ..providers.OpenMeteoForecastProvider import OpenMeteoForecastProvider
from ..providers.RNSAProvider import PollenResponse
from ..providers.RNSAProvider import RNSAProvider


def create_forecast_endpoints(tag: str, api: FastAPI) -> None:
  forecast = OpenMeteoForecastProvider()
  air_quality = OpenMeteoAirQualityProvider()
  rnsa = RNSAProvider()

  @api.get('/forecast', tags=[tag])
  async def get_forecast(
    lat: float = Query(
      description='The latitude of the location for which the weather forecast is requested.',
      example=48.8534951,
    ),
    lon: float = Query(
      description='The longitude of the location for which the weather forecast is requested.',
      example=2.3483915,
    ),
  ) -> ForecastResponse:
    """
    Retrieve the weather forecast for a specific location.

    This endpoint provides detailed weather information, including temperature, humidity, wind direction,
    wind speed, sunrise, and sunset times, based on the provided latitude and longitude.
    """
    return await forecast.fetch(lat=lat, lon=lon)

  @api.get('/air-quality', tags=[tag])
  async def get_air_quality(
    lat: float = Query(
      description='The latitude of the location for which the air quality data is requested.',
      example=48.8534951,
    ),
    lon: float = Query(
      description='The longitude of the location for which the air quality data is requested.',
      example=2.3483915,
    ),
  ) -> AirQualityResponse:
    """
    Retrieve the air quality data for a specific location.

    This endpoint provides detailed air quality information, including the Air Quality Index (AQI),
    PM2.5, PM10, NO₂, and O₃ levels, based on the provided latitude and longitude.
    """
    return await air_quality.fetch(lat=lat, lon=lon)

  @api.get('/pollen', tags=[tag])
  async def get_pollen(
    lat: float = Query(
      description='The latitude of the location for which the pollen data is requested.',
      example=48.8534951,
    ),
    lon: float = Query(
      description='The longitude of the location for which the pollen data is requested.',
      example=2.3483915,
    ),
  ) -> PollenResponse:
    """
    Retrieve the pollen data for a specific location.

    This endpoint provides information about the pollen types and their levels (e.g., Grass, Birch, Olive)
    based on the provided latitude and longitude.
    """
    return await rnsa.fetch(lat=lat, lon=lon)
