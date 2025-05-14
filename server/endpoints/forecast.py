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
from typing import Generic
from typing import TypeVar

from fastapi import FastAPI
from fastapi import Query
from pydantic import BaseModel

from ..providers.MeteoPollenProvider import MeteoPollenProvider
from ..providers.MeteoPollenProvider import PollenData
from ..providers.OpenMeteoAirQualityProvider import EAQIData
from ..providers.OpenMeteoAirQualityProvider import OpenMeteoAirQualityProvider
from ..providers.OpenMeteoAirQualityProvider import USAQIData
from ..providers.OpenMeteoForecastProvider import ForecastData
from ..providers.OpenMeteoForecastProvider import OpenMeteoForecastProvider


ResponseData = TypeVar('ResponseData')


class Response(BaseModel, Generic[ResponseData]):
  provider: str
  data: ResponseData


def create_forecast_endpoints(
  tag: str,
  api: FastAPI,
  forecast: OpenMeteoForecastProvider,
  air_quality: OpenMeteoAirQualityProvider,
  pollen=MeteoPollenProvider,
) -> None:
  @api.get(
    path='/forecast',
    tags=[tag],
    responses={
      200: {
        'content': {
          'application/json': {
            'example': Response.model_validate(
              {
                'provider': 'Open-Météo',
                'data': {
                  'temperature': '17.1°C',
                  'humidity': '50%',
                  'wind_speed': '12.5 km/h',
                  'sunrise': '06:08:00',
                  'sunset': '21:25:00',
                },
              }
            )
          },
        },
      },
    },
  )
  async def get_forecast(
    lat: float = Query(
      description='The latitude of the location for which the weather forecast is requested.',
      examples=[48.8534951],
    ),
    lon: float = Query(
      description='The longitude of the location for which the weather forecast is requested.',
      examples=[2.3483915],
    ),
    timezone: str = Query(
      default='auto',
      description='The timezone identifier for the location for which the weather forecast is requested.',
      examples=['Africa/Douala', 'Europe/Paris'],
    ),
  ) -> Response[ForecastData]:
    """
    Retrieve the weather forecast for a specific location.

    This endpoint provides detailed weather information for a given latitude
    and longitude. The data includes temperature, humidity, wind direction,
    wind speed, sunrise, and sunset times. Users can also specify a timezone
    to adjust the forecast data accordingly.
    """
    return Response[ForecastData](
      provider=forecast.name,
      data=await forecast.fetch(lat=lat, lon=lon, timezone=timezone),
    )

  @api.get(
    '/air-quality',
    tags=[tag],
    responses={
      200: {
        'content': {
          'application/json': {
            'example': Response.model_validate(
              {'provider': 'Open-Météo', 'data': {'value': 28, 'level': 'fair', 'unit': 'EAQI'}}
            ),
          },
        }
      }
    },
  )
  async def get_air_quality(
    lat: float = Query(
      description='The latitude of the location for which the air quality data is requested.',
      examples=[48.8534951],
    ),
    lon: float = Query(
      description='The longitude of the location for which the air quality data is requested.',
      examples=[2.3483915],
    ),
  ) -> Response[EAQIData | USAQIData]:
    """
    Retrieve the air quality data for a specific location.

    This endpoint provides detailed air quality information for a given
    latitude and longitude. The data includes metrics such as the Air Quality
    Index (AQI), PM2.5, PM10, NO₂, and O₃ levels. Users can specify a timezone
    to adjust the data accordingly.
    """
    data = await air_quality.fetch(lat=lat, lon=lon)

    return Response[EAQIData | USAQIData](
      provider=air_quality.name,
      data=data,
    )

  @api.get(
    path='/pollen',
    tags=[tag],
    responses={
      200: {
        'content': {
          'application/json': {
            'example': Response[PollenData].model_validate(
              {
                'provider': 'Météo Pollen',
                'data': {'pollen_names': ['grass', 'urticaceae', 'oak', 'sorrel'], 'level': 3, 'risk': 'high'},
              }
            ),
          },
        },
      },
    },
  )
  async def get_pollen(
    lat: float = Query(
      description='The latitude of the location for which the pollen data is requested.',
      examples=[48.8534951],
    ),
    lon: float = Query(
      description='The longitude of the location for which the pollen data is requested.',
      examples=[2.3483915],
    ),
  ) -> Response[PollenData]:
    """
    Retrieve the pollen data for a specific location.

    This endpoint provides information about pollen levels for a given
    latitude and longitude. The data includes details about various pollen
    types, such as Grass, Birch, and Olive, along with their respective
    levels.
    """
    return Response[PollenData](
      provider=pollen.name,  # type: ignore
      data=await pollen.fetch(lat=lat, lon=lon),  # type: ignore
    )
