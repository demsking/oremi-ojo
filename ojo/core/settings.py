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
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from .package import APP_NAME
from .package import APP_VERSION


class Settings(BaseSettings):
  """Application configuration settings for Oremi Ojọ.

  All settings can be configured via environment variables.
  Service URLs are optional - if not provided, the service will run in chat-only mode.
  """

  model_config = SettingsConfigDict(
    env_prefix='OREMI_OJO_',
    strict=True,
    extra='ignore',
  )

  server_host: str = Field(
    default='127.0.0.1',
    description="Host address to bind the server to. Use '0.0.0.0' to listen on all interfaces.",
  )

  server_port: int = Field(
    default=5040,
    ge=1,
    le=65535,
    description='Port number to bind the server to. Must be between 1 and 65535.',
  )

  api_prefix: str = Field(default='/', description='API prefix for all endpoints.')

  http_request_timeout: float = Field(
    default=30.0,
    gt=1.0,
    description='Global timeout in seconds for HTTP requests to external services. Default: 30.0.',
  )

  http_user_agent: str = Field(
    default=f'{APP_NAME}/{APP_VERSION} (https://gitlab.com/demsking/oremi-ojo)',
    min_length=1,
    description='User-Agent header value for outbound HTTP requests to external services.',
  )

  http_cache_ttl_seconds: float = Field(
    default=3600.0,
    ge=0.0,
    le=86400.0,
    description=(
      'TTL in seconds for external HTTP cache sessions. Default: 3600.0, matching the fastest hourly '
      'weather data refresh cadence used by the shared forecast and air-quality providers.'
    ),
  )

  log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = Field(default='INFO', description='Logging level.')
  log_file: str | None = Field(default=None, description='Path to rotating log file.')

  @field_validator('api_prefix')
  @classmethod
  def validate_api_prefix(cls, value: str) -> str:
    if not value.startswith('/'):
      raise ValueError("OREMI_OJO_API_PREFIX must start with '/'")

    return value.rstrip('/') or '/'


@lru_cache
def get_settings() -> Settings:
  """Return cached application settings."""
  return Settings()
