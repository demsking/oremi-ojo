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
import logging
from contextlib import asynccontextmanager
from time import perf_counter

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

from ..api import docs
from ..api import forecast
from ..api import geocode
from ..api import health
from ..core.geo import NotFoundLocationException
from ..mcp.air_quality_tools import register_air_quality_mcp_tools
from ..mcp.forecast_tools import register_forecast_mcp_tools
from ..mcp.geocode_tools import register_geocode_mcp_tools
from ..mcp.pollen_tools import register_pollen_mcp_tools
from ..mcp.prompts import register_mcp_prompts
from ..mcp.resources import register_mcp_resources
from ..providers.OpenMeteoProvider import OpenMeteoProvider
from ..services.air_quality_service import AirQualityService
from ..services.forecast_service import ForecastService
from ..services.pollen_service import PollenService
from ..utils.logger import configure_logging
from .package import APP_DESCRIPTION
from .package import APP_NAME
from .package import APP_VERSION
from .settings import Settings


logger = logging.getLogger(__name__)


def log_startup_settings(settings: Settings) -> None:
  """Log every configured application setting without exposing secrets."""
  for name in settings.__class__.model_fields:
    value = getattr(settings, name)
    logger.info('Setting %s: %s', name, value)


def create_app(settings: Settings, http_client: httpx.AsyncClient | None = None) -> FastAPI:
  @asynccontextmanager
  async def lifespan(app: FastAPI):
    startup_started = perf_counter()
    ready = False

    configure_logging(settings.log_level, settings.log_file)

    logger.info(f'{APP_NAME} v{APP_VERSION}')
    log_startup_settings(settings)

    client = app.state.client

    logger.info(f'Oremi Ojọ ready: duration_ms={(perf_counter() - startup_started) * 1000:.1f}')

    ready = True

    _ = mcp.streamable_http_app()
    if mcp._session_manager is not None:  # pylint: disable=protected-access
      mcp._session_manager._has_started = False  # pylint: disable=protected-access
    async with mcp.session_manager.run():
      yield

    shutdown_started = perf_counter()

    if ready:
      logger.info('Shutting down Oremi Ojọ')
    else:
      logger.warning('Oremi Ojọ startup aborted; cleaning up resources')

    await client.aclose()
    logger.info(f'Oremi Ojọ stopped: duration_ms={(perf_counter() - shutdown_started) * 1000:.1f}')

  app = FastAPI(
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
    title='Oremi Ojọ',
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    root_path=settings.api_prefix,
    servers=[
      {'url': settings.api_prefix},
    ],
    license_info={
      'name': 'Apache 2.0',
      'url': 'http://www.apache.org/licenses/LICENSE-2.0.html',
    },
    openapi_tags=[
      forecast.API_TAG_METADATA,
      geocode.API_TAG_METADATA,
      health.API_TAG_METADATA,
    ],
  )

  mcp = FastMCP(
    name='Oremi Ojọ',
    instructions=('???'),
    stateless_http=True,
    json_response=True,
    streamable_http_path='/mcp',
  )

  openmeteo = OpenMeteoProvider(settings)
  forecast_service = ForecastService(openmeteo)
  air_quality_service = AirQualityService(openmeteo)
  pollen_service = PollenService(openmeteo)

  client = http_client or httpx.AsyncClient(timeout=settings.http_request_timeout)

  app.state.client = client
  app.state.settings = settings
  app.state.mcp = mcp
  app.state.forecast_service = forecast_service
  app.state.air_quality_service = air_quality_service
  app.state.pollen_service = pollen_service

  @app.exception_handler(Exception)
  async def unhandled_exception_handler(_, exc: Exception) -> JSONResponse:
    logger.exception('Unhandled application error')
    return JSONResponse(status_code=500, content={'detail': 'Internal server error', 'error': str(exc)})

  @app.exception_handler(httpx.ConnectTimeout)
  async def handle_httpx_connect_timeout(_, exc: httpx.ConnectTimeout) -> JSONResponse:
    return JSONResponse(status_code=500, content={'detail': str(exc) or 'Connection Timeout Error'})

  @app.exception_handler(httpx.ConnectError)
  async def handle_httpx_connect_error(_, exc: httpx.ConnectError) -> JSONResponse:
    return JSONResponse(status_code=500, content={'detail': str(exc)})

  @app.exception_handler(NotFoundLocationException)
  async def not_found_location_exception_handler(_, exc: NotFoundLocationException) -> JSONResponse:
    logger.error(exc)
    return JSONResponse(status_code=404, content={'detail': 'No location found'})

  @app.get('/', include_in_schema=False)
  async def redirect_to_docs():
    return HTMLResponse(status_code=307, headers={'Location': docs.router.prefix})

  prefix = '' if settings.api_prefix == '/' else settings.api_prefix
  api_prefix = f'{prefix}/api'

  app.include_router(forecast.router, prefix=api_prefix)
  app.include_router(geocode.router, prefix=api_prefix)
  app.include_router(health.router, prefix=prefix)
  app.include_router(docs.router, prefix=prefix)

  register_air_quality_mcp_tools(mcp, air_quality_service)
  register_forecast_mcp_tools(mcp, forecast_service)
  register_pollen_mcp_tools(mcp, pollen_service)
  register_geocode_mcp_tools(mcp)
  register_mcp_prompts(mcp)
  register_mcp_resources(
    mcp=mcp,
    forecast_service=forecast_service,
    air_quality_service=air_quality_service,
    pollen_service=pollen_service,
  )

  app.mount(settings.api_prefix, mcp.streamable_http_app())

  return app
