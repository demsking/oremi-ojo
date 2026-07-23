# Copyright 2024-2026 Sébastien Demanou. All Rights Reserved.
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

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from pydantic import BaseModel

from ..models.air_quality import EAQIData
from ..models.air_quality import USAQIData
from ..models.forecast import ForecastData
from ..models.pollen import PollenData
from ..services.air_quality_service import AirQualityService
from ..services.forecast_service import ForecastService
from ..services.forecast_service import TemperatureUnit
from ..services.pollen_service import PollenService


API_TAG_METADATA = {
  'name': 'Forecast Endpoints',
  'description': (
    'Endpoints for retrieving detailed weather forecast data. These include '
    'information such as temperature, humidity, wind speed, wind direction, '
    'sunrise, and sunset times. The endpoints allow users to obtain weather '
    'information for specific locations based on latitude and longitude, '
    'helping them plan activities and make informed decisions.'
  ),
}


router = APIRouter(tags=[API_TAG_METADATA['name']])

ResponseData = TypeVar('ResponseData')


class Response(BaseModel, Generic[ResponseData]):
  provider: str
  data: ResponseData


@router.get(
  path='/forecast',
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
  request: Request,
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
  temperature_unit: TemperatureUnit = Query(
    'celsius',
    alias='temperature-unit',
    description='Preferred unit for temperature values in the forecast response.',
    examples=['celsius', 'fahrenheit'],
  ),
) -> Response[ForecastData]:
  """
  Retrieve detailed weather forecast data for a specific location.

  This endpoint fetches current weather conditions including temperature,
  humidity, wind speed, sunrise, and sunset times for the specified
  latitude and longitude. Optionally, a timezone can be provided to ensure
  time-based data (like sunrise/sunset) is returned appropriately for the
  location. The temperature unit can also be specified to return values in
  either Celsius or Fahrenheit.

  It returns the name of the provider and the structured weather data.
  """
  forecast_service: ForecastService = request.app.state.forecast_service

  return Response[ForecastData](
    provider=forecast_service.name,
    data=await forecast_service.fetch(lat=lat, lon=lon, timezone=timezone, temperature_unit=temperature_unit),
  )


@router.get(
  '/air-quality',
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
  request: Request,
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
  Retrieve current air quality data for a specific location.

  This endpoint returns air quality metrics such as the Air Quality Index
  (AQI), and potentially pollutant levels like PM2.5, PM10, NO₂, and O₃,
  depending on the provider's capabilities. The data is localized to the
  specified latitude and longitude.

  The response includes the provider name and a structured representation
  of the air quality data based on either EAQI or USAQI standards.
  """
  air_quality_service: AirQualityService = request.app.state.air_quality_service
  data = await air_quality_service.fetch(lat=lat, lon=lon)

  return Response[EAQIData | USAQIData](
    provider=air_quality_service.name,
    data=data,
  )


@router.get(
  path='/pollen',
  responses={
    200: {
      'content': {
        'application/json': {
          'example': Response[PollenData].model_validate(
            {
              'provider': 'Open-Météo',
              'data': {
                'pollen_names': ['grass', 'ragweed'],
                'units': 'grains/m³',
                'dominant_pollen': 'grass',
                'details': {
                  'alder': {'level': 0.0, 'severity': 'zero'},
                  'birch': {'level': 0.0, 'severity': 'zero'},
                  'grass': {'level': 23.4, 'severity': 'moderate'},
                  'mugwort': {'level': 0.0, 'severity': 'zero'},
                  'olive': {'level': 0.0, 'severity': 'zero'},
                  'ragweed': {'level': 4.2, 'severity': 'moderate'},
                },
              },
            }
          ),
        },
      },
    },
  },
)
async def get_pollen(
  request: Request,
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
  Retrieve current pollen data for a specific location.

  This endpoint provides information on the presence and concentration levels
  of various airborne pollens at the given geographic coordinates.

  The response includes the data provider and a structured payload detailing
  pollen types, units, and per-pollen concentration plus SILAM severity.
  """
  pollen_service: PollenService = request.app.state.pollen_service

  return Response[PollenData](
    provider=pollen_service.name,
    data=await pollen_service.fetch(lat=lat, lon=lon),  # type: ignore
  )
