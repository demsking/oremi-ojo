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

from .core.api import BASE_PATH
from .core.assistant import Assistant
from .core.config import OLLAMA_BASEURL
from .core.config import OLLAMA_MODEL
from .core.controller import Controller
from .core.geo import NotFoundLocationException
from .core.logger import logger
from .core.package import APP_VERSION
from .endpoints.agent import create_agent_endpoints
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

agents_tag = {
  'name': 'Agents Endpoints',
  'description': (
    'Endpoints for generating climate information, such as weather, air quality, '
    'and pollen data, based on user input. These endpoints process queries to '
    'provide relevant and accurate responses.'
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


@asynccontextmanager
async def lifespan(app: FastAPI):
  # execute the app lifespan atr the start of the context manager and at the end
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
    agents_tag,
    geocode_tag,
    version_tag,
  ],
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


create_generative_endpoints(
  tag=agents_tag['name'], api=api, controller=controller, forecast=forecast, air_quality=air_quality, rnsa=rnsa
)

create_forecast_endpoints(tag=forecast_tag['name'], api=api, forecast=forecast, air_quality=air_quality, rnsa=rnsa)
create_agent_endpoints(tag=agents_tag['name'], api=api, controller=controller)
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
