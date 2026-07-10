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
from pydantic import HttpUrl
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from .package import APP_NAME
from .package import APP_VERSION


class Settings(BaseSettings):
  """Application configuration settings for Oremi Weather Agent.

  All settings can be configured via environment variables.
  Service URLs are optional - if not provided, the service will run in chat-only mode.
  """

  model_config = SettingsConfigDict(
    env_prefix='OREMI_WEATHER_',
    strict=True,
    extra='ignore',
  )

  server_host: str = Field(
    default='127.0.0.1',
    description="Host address to bind the server to. Use '0.0.0.0' to listen on all interfaces.",
  )

  server_port: int = Field(
    default=1777,
    ge=1,
    le=65535,
    description='Port number to bind the server to. Must be between 1 and 65535.',
  )

  api_prefix: str = Field(default='/', description='API prefix for all endpoints.')

  llm_model: str = Field(
    default='ollama:qwen3.5:2b',
    description='Fully qualified Pydantic-AI model identifier.',
  )

  llm_request_timeout: int = Field(
    default=15,
    ge=1,
    le=300,
    description='Request timeout in seconds for LLM calls.',
  )

  llm_temperature: float = Field(
    default=0.3,
    ge=0.0,
    le=2.0,
    description='Sampling temperature used by the configured LLM backend.',
  )

  llm_system_prompt: str = Field(
    default=('????'),
    description='System prompt for the AI agent.',
  )

  ollama_base_url: HttpUrl | None = Field(
    default=None,
    description='Ollama API base URL used when the agent runs on Ollama.',
  )

  request_timeout: float = Field(
    default=30.0,
    gt=1.0,
    description='Global timeout in seconds for HTTP requests to external services. Default: 30.0.',
  )

  user_agent: str = Field(
    default=f'{APP_NAME}/{APP_VERSION} (https://gitlab.com/demsking/oremi-weather-agent)',
    min_length=1,
    description='User-Agent header value for outbound HTTP requests to external services.',
  )

  max_response_tokens: int = Field(
    default=500,
    gt=10,
    le=4096,
    description='Maximum number of tokens to generate in LLM responses. Default: 500.',
  )

  cache_enabled: bool = Field(
    default=True,
    description='Enable the bounded internal cache for repeated LLM and idempotent component calls.',
  )

  cache_max_entries: int = Field(
    default=512,
    ge=0,
    le=10000,
    description='Maximum number of internal smart-cache entries kept in memory. Set to 0 to disable caching.',
  )

  cache_llm_ttl_seconds: float = Field(
    default=300.0,
    ge=0.0,
    le=3600.0,
    description='TTL in seconds for cacheable internal LLM calls.',
  )

  log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = Field(default='INFO', description='Logging level.')
  log_file: str | None = Field(default=None, description='Path to rotating log file.')

  @field_validator('api_prefix')
  @classmethod
  def validate_api_prefix(cls, value: str) -> str:
    if not value.startswith('/'):
      raise ValueError("OREMI_WEATHER_API_PREFIX must start with '/'")

    return value.rstrip('/') or '/'

  @field_validator('ollama_base_url', mode='before')
  @classmethod
  def validate_ollama_base_url(cls, value):
    """Remove trailing slashes from Ollama host URL."""
    if isinstance(value, str):
      value = value.rstrip('/')

    return value

  def uses_ollama(self) -> bool:
    """Return whether the active agent model uses the Ollama backend."""

    return self.llm_model.startswith('ollama:')

  def resolve_ollama_model_name(self) -> str:
    """Return the Ollama model name without provider prefix."""
    return self.llm_model.removeprefix('ollama:')  # pylint: disable=no-member

  @property
  def ollama_base_url_string(self) -> str:
    """Return the Ollama base URL for Pydantic AI."""
    if self.ollama_base_url is None:
      raise ValueError('OREMI_WEATHER_OLLAMA_BASE_URL is required when using an ollama: model')

    return str(self.ollama_base_url).rstrip('/')


@lru_cache
def get_settings() -> Settings:
  """Return cached application settings."""
  return Settings()
