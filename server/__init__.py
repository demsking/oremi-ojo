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
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware

from .core.api import parse_path
from .core.config import ALLOWED_ORIGINS
from .core.geo import NotFoundLocationException
from .core.logger import logger
from .core.package import APP_VERSION
from .endpoints.docs import create_docs_endpoints
from .endpoints.forecast import create_forecast_endpoints
from .endpoints.geocode import create_geocode_endpoints
from .endpoints.version import create_version_endpoints


SERVICE_TITLE = 'Oremi Forecast API'

_current_dir = os.path.dirname(os.path.abspath(__file__))
_readme_path = os.path.realpath(
  os.path.join(_current_dir, '..', 'DOCUMENTATION.md'),
)

with open(_readme_path, 'r', encoding='utf-8') as file:
  SERVICE_DESCRIPTION = file.read()

forecast_tag = {
  'name': 'Forecast Endpoints',
  'description': (
    'Endpoints for retrieving weather forecast data, including temperature, humidity, wind speed, '
    'wind direction, sunrise, and sunset times. These endpoints provide detailed weather information '
    'for a specific location based on latitude and longitude, enabling users to plan activities and '
    'make informed decisions based on current and future weather conditions.'
  ),
}

geocode_tag = {
  'name': 'Geocode Endpoints',
  'description': (
    'Endpoints for retrieving geographical location data, including address details, coordinates, '
    'and bounding boxes. These endpoints support both forward geocoding (searching for a location '
    'by name or address) and reverse geocoding (finding a location by latitude and longitude). '
    'They are useful for mapping, navigation, and location-based services.'
  ),
}

version_tag = {
  'name': 'Server Endpoints',
  'description': (
    'Endpoints for retrieving server-related information, including the server\'s name and version. '
    'This allows clients to easily identify the server they are interacting with and its current version, '
    'ensuring transparency and compatibility in API usage.'
  ),
}

BASE_PATH = parse_path('/api')


@asynccontextmanager
async def lifespan(app: FastAPI):
  # execute the app lifespan atr the start of the context manager and at the end
  logger.info(f'Allowed Origins: {ALLOWED_ORIGINS}')
  yield

api = FastAPI(
  docs_url=None,
  redoc_url=None,
  lifespan=lifespan,
  title=SERVICE_TITLE,
  version=APP_VERSION,
  description=SERVICE_DESCRIPTION,
  root_path=BASE_PATH,
  servers=[
    {'url': BASE_PATH},
  ],
  license_info={
    'name': 'Apache 2.0',
    'url': 'http://www.apache.org/licenses/LICENSE-2.0.html',
  },
  openapi_tags=[
    forecast_tag,
    geocode_tag,
    version_tag,
  ],
)

api.add_middleware(
  CORSMiddleware,
  allow_origins=ALLOWED_ORIGINS,
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

create_forecast_endpoints(forecast_tag['name'], api)
create_geocode_endpoints(geocode_tag['name'], api)
create_version_endpoints(version_tag['name'], api)
create_docs_endpoints(api)


@api.exception_handler(NotFoundLocationException)
async def not_found_location_exception_handler(
  request: Request,
  error: NotFoundLocationException,
) -> Response:
  logger.error(error)

  return Response(status_code=404)
