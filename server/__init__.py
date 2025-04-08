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
from .core.assistant import Assistant
from .core.config import ALLOWED_ORIGINS
from .core.config import CACHE_DIR
from .core.config import HOST
from .core.config import LOG_FILE
from .core.config import OLLAMA_BASEURL
from .core.config import OLLAMA_MODEL
from .core.config import PORT
from .core.config import ROOT_PATH
from .core.config import USER_AGENT
from .core.config import WORKERS
from .core.controller import Controller
from .core.geo import NotFoundLocationException
from .core.logger import LOG_LEVEL_STR
from .core.logger import logger
from .core.package import APP_NAME
from .core.package import APP_VERSION
from .endpoints.docs import create_docs_endpoints
from .endpoints.forecast import create_forecast_endpoints
from .endpoints.generative import create_generative_endpoints
from .endpoints.geocode import create_geocode_endpoints
from .endpoints.version import create_version_endpoints
from .providers.OpenMeteoAirQualityProvider import OpenMeteoAirQualityProvider
from .providers.OpenMeteoForecastProvider import OpenMeteoForecastProvider
from .providers.RNSAProvider import RNSAProvider


SERVICE_TITLE = 'Oremi Weather Agent Documentation'

_current_dir = os.path.dirname(os.path.abspath(__file__))
_readme_path = os.path.realpath(
  os.path.join(_current_dir, '..', 'DOCUMENTATION.md'),
)

with open(_readme_path, encoding='utf-8') as file:
  SERVICE_DESCRIPTION = file.read()

forecast_tag = {
  'name': 'Forecast Endpoints',
  'description': (
    'Endpoints for retrieving detailed weather forecast data. These include '
    'information such as temperature, humidity, wind speed, wind direction, '
    'sunrise, and sunset times. The endpoints allow users to obtain weather '
    'information for specific locations based on latitude and longitude, '
    'helping them plan activities and make informed decisions.'
  ),
}

generative_tag = {
  'name': 'Generative Endpoints',
  'description': (
    'Endpoints that provide generative responses for weather-related queries. '
    'Users can input natural language questions, and the API will generate '
    'detailed weather forecasts or related information for the specified or '
    'inferred location.'
  ),
}

geocode_tag = {
  'name': 'Geocode Endpoints',
  'description': (
    'Endpoints for retrieving geographical data, including address details, '
    'coordinates, and bounding boxes. These endpoints support forward '
    'geocoding (searching by name or address) and reverse geocoding (finding '
    'locations by latitude and longitude). They are essential for mapping, '
    'navigation, and location-based services.'
  ),
}

version_tag = {
  'name': 'Server Endpoints',
  'description': (
    "Endpoints for retrieving server-related metadata, such as the server's "
    'name and version. These endpoints help clients identify the server they '
    'are interacting with and ensure compatibility with the API.'
  ),
}

BASE_PATH = parse_path('/api')


@asynccontextmanager
async def lifespan(app: FastAPI):
  # execute the app lifespan atr the start of the context manager and at the end
  logger.info(f'Starting {APP_NAME}/{APP_VERSION}')
  logger.info(f'Server Host: {HOST}')
  logger.info(f'Server Port: {PORT}')
  logger.info(f'Server Workers: {WORKERS}')
  logger.info(f'Server Root Path: {ROOT_PATH}')
  logger.info(f'User Agent: {USER_AGENT}')
  logger.info(f'Cache Directory: {CACHE_DIR}')
  logger.info(f'Allowed Origins: {ALLOWED_ORIGINS or "*"}')
  logger.info(f'Log Level: {LOG_LEVEL_STR}')
  logger.info(f'Log File Path: {LOG_FILE or None}')
  logger.info(f'API Base Path: {BASE_PATH}')
  logger.info(f'Ollama URL: {OLLAMA_BASEURL}')
  logger.info(f'Ollama Model: {OLLAMA_MODEL}')
  logger.info(f'User Agent: {USER_AGENT}')
  logger.info(f'API Root Path: {ROOT_PATH}')
  await assistant.load_model()
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
    generative_tag,
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

assistant = Assistant(
  model=OLLAMA_MODEL,
  logger=logger,
  ollama_baseurl=OLLAMA_BASEURL,
)

controller = Controller(
  logger=logger,
  assistant=assistant,
)

forecast = OpenMeteoForecastProvider(controller, logger)
air_quality = OpenMeteoAirQualityProvider(controller, logger)
rnsa = RNSAProvider(controller, logger)

create_forecast_endpoints(
  tag=forecast_tag['name'], api=api, controller=controller, forecast=forecast, air_quality=air_quality, rnsa=rnsa
)

create_generative_endpoints(
  tag=generative_tag['name'], api=api, controller=controller, forecast=forecast, air_quality=air_quality, rnsa=rnsa
)

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
