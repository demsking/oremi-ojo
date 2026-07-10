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
from fastapi_mcp import FastApiMCP

from ..api import agent
from ..api import docs
from ..api import forecast
from ..api import geocode
from ..api import health
from ..core.controller import Controller
from ..core.geo import NotFoundLocationException
from ..llm.agent import AgentClient
from ..providers.OpenMeteoAirQualityProvider import OpenMeteoAirQualityProvider
from ..providers.OpenMeteoForecastProvider import OpenMeteoForecastProvider
from ..providers.OpenMeteoPollenProvider import OpenMeteoPollenProvider
from ..utils.logger import configure_logging
from ..utils.url import safe_url
from .package import APP_DESCRIPTION
from .package import APP_NAME
from .package import APP_VERSION
from .settings import Settings
from weather.utils.cache import SmartCache


logger = logging.getLogger(__name__)


def create_app(settings: Settings, http_client: httpx.AsyncClient | None = None) -> FastAPI:
  @asynccontextmanager
  async def lifespan(app: FastAPI):
    startup_started = perf_counter()
    ready = False

    configure_logging(settings.log_level, settings.log_file)

    logger.info(f'{APP_NAME} v{APP_VERSION}')
    logger.info(f'Server: http://{settings.server_host}:{settings.server_port}')
    logger.info(f'API Docs: http://{settings.server_host}:{settings.server_port}/docs')

    logger.info(
      'App settings [server]: host=%s port=%s api_prefix=%s', settings.server_host, settings.server_port, settings.api_prefix
    )
    logger.info(
      'App settings [ollama]: model=%s base_url=%s',
      settings.llm_model,
      safe_url(settings.ollama_base_url_string if settings.ollama_base_url is not None else None),
    )
    logger.info(
      'App settings [generation]: request_timeout=%s temperature=%s max_response_tokens=%s system_prompt=%s',
      settings.llm_request_timeout,
      settings.llm_temperature,
      settings.max_response_tokens,
      settings.llm_system_prompt.replace('\n', ' ').strip(),
    )
    logger.info('App settings [logging]: level=%s destination=%s', settings.log_level, settings.log_file or 'stderr')
    logger.info(
      'App settings [smart_cache]: enabled=%s max_entries=%s llm_ttl_seconds=%s',
      settings.cache_enabled,
      settings.cache_max_entries,
      settings.cache_llm_ttl_seconds,
    )

    client = http_client or httpx.AsyncClient(timeout=settings.request_timeout)
    smart_cache = SmartCache(enabled=settings.cache_enabled, max_entries=settings.cache_max_entries)
    assistant = AgentClient(settings, client, smart_cache)

    try:
      if settings.uses_ollama():
        if settings.ollama_base_url is None:
          logger.warning('OREMI_WEATHER_OLLAMA_BASE_URL is not configured; LLM-backed endpoints will be unavailable')
        else:
          await assistant.load_model()

      app.state.client = client
      app.state.settings = settings

      controller = Controller(assistant)
      forecast_provider = OpenMeteoForecastProvider(controller)
      air_quality_provider = OpenMeteoAirQualityProvider(controller)
      pollen_provider = OpenMeteoPollenProvider(controller)

      app.state.controller = controller
      app.state.forecast_provider = forecast_provider
      app.state.air_quality_provider = air_quality_provider
      app.state.pollen_provider = pollen_provider

      logger.info(f'Oremi Weather Agent ready: duration_ms={(perf_counter() - startup_started) * 1000:.1f}')

      yield
    finally:
      shutdown_started = perf_counter()

      if ready:
        logger.info('Shutting down Oremi Weather Agent')
      else:
        logger.warning('Oremi Weather Agent startup aborted; cleaning up resources')

      await client.aclose()
      logger.info(f'Oremi Weather Agent stopped: duration_ms={(perf_counter() - shutdown_started) * 1000:.1f}')

  app = FastAPI(
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
    title='Oremi Weather Agent',
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
      agent.API_TAG_METADATA,
      geocode.API_TAG_METADATA,
      health.API_TAG_METADATA,
    ],
  )

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
  app.include_router(agent.router, prefix=api_prefix)
  app.include_router(health.router, prefix=prefix)
  app.add_api_route(f'{api_prefix}/server', health.health, methods=['GET'], include_in_schema=False)
  app.include_router(docs.router, prefix=prefix)

  mcp = FastApiMCP(
    app,
    name=APP_NAME,
    description=APP_DESCRIPTION,
    describe_all_responses=True,
    describe_full_response_schema=True,
    include_tags=[
      forecast.API_TAG_METADATA['name'],
      geocode.API_TAG_METADATA['name'],
    ],
  )

  mcp.mount_http()
  app.state.mcp = mcp

  return app
