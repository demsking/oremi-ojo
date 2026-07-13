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
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from collections.abc import Sequence
from typing import Any
from typing import Generic
from typing import Protocol
from typing import TYPE_CHECKING
from typing import TypeVar

import httpx
import ollama
from ollama import AsyncClient
from ollama import GenerateResponse
from ollama import Message
from ollama import Options
from ollama import ResponseError
from ollama import Tool
from pydantic import BaseModel
from pydantic import Field
from pydantic_ai import Agent as PydanticAgent
from pydantic_ai import ModelSettings
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

from ..core.settings import Settings
from ..utils.cache import SmartCache


logger = logging.getLogger(__name__)

if TYPE_CHECKING:

  class ToolResult(Protocol):
    data: Any

  class ToolRegistry(Protocol):
    tools: dict[str, Any]

    async def execute(self, name: str, arguments: dict[str, Any], context: dict[str, Any]) -> ToolResult: ...


OutputModel = TypeVar('OutputModel')


class AgentClient(Generic[OutputModel]):
  def __init__(self, settings: Settings, client: httpx.AsyncClient, cache: SmartCache | None = None):
    self.settings = settings
    self.cache = cache
    self.is_available = not settings.should_use_native_ollama or settings.ollama_base_url is not None

    self.ollama_client = (
      ollama.AsyncClient(host=settings.ollama_base_url_string, timeout=settings.llm_request_timeout)
      if self.settings.should_use_native_ollama and settings.ollama_base_url is not None
      else None
    )

    self.model_settings = ModelSettings(
      temperature=settings.llm_temperature,
      max_tokens=settings.max_response_tokens,
      timeout=settings.llm_request_timeout,
      thinking=False,
    )

    self.model = (
      None if self.settings.should_use_native_ollama or not self.is_available else AgentClient.build_model(settings, client)
    )
    self.agent = None if self.model is None else self._create_agent()

  def create_agent(self, system: str | None) -> 'OllamaAgent | PydanticGenerateAgent | UnavailableOllamaAgent':
    if self.settings.should_use_native_ollama:
      if self.ollama_client is None:
        return UnavailableOllamaAgent(system=system)

      return OllamaAgent(
        client=self.ollama_client,
        model=self.settings.ollama_model_name,
        system=system,
      )

    if self.model is None:
      return UnavailableOllamaAgent(system=system)

    return PydanticGenerateAgent(
      model=self.model,
      model_settings=self.model_settings,
      system=system,
    )

  def create_tools_agent(
    self, tools: list[Tool], system: str | None = None
  ) -> 'OllamaToolsAgent | PydanticToolsAgent | UnavailableOllamaToolsAgent':
    if self.settings.should_use_native_ollama:
      if self.ollama_client is None:
        return UnavailableOllamaToolsAgent(system=system)

      return OllamaToolsAgent(
        client=self.ollama_client,
        model=self.settings.ollama_model_name,
        tools=tools,
        system=system,
      )

    if self.model is None:
      return UnavailableOllamaToolsAgent(system=system)

    return PydanticToolsAgent(
      model=self.model,
      model_settings=self.model_settings,
      tools=tools,
      system=system,
    )

  async def load_model(self) -> None:
    if not self.settings.should_use_native_ollama:
      return

    if self.ollama_client is None:
      raise RuntimeError('Native Ollama client is not configured')

    try:
      logger.info(f'Pulling model {self.settings.ollama_model_name}...')
      await self.ollama_client.pull(self.settings.ollama_model_name, stream=False)

      logger.info(f'Loading model {self.settings.ollama_model_name}...')
      await self.ollama_client.generate(model=self.settings.ollama_model_name, keep_alive=-1, stream=False)
    except httpx.ReadTimeout as error:
      self._log_model_load_timeout(self.settings.ollama_model_name, error)
      return
    except ResponseError as error:
      if error.status_code != 499:
        raise

      self._log_model_load_timeout(self.settings.ollama_model_name, error)
      return

    logger.info(f'Ollama model ready: {self.settings.ollama_model_name}')

  @staticmethod
  def _log_model_load_timeout(model_name: str, error: Exception) -> None:
    logger.warning(
      'Ollama model load timed out for %s; continuing startup and the model may finish loading in the background: %s',
      model_name,
      error,
    )

  @staticmethod
  def build_model(settings: Settings, client: httpx.AsyncClient) -> Any:
    if settings.should_use_native_ollama:
      return OllamaModel(
        settings.ollama_model_name,
        provider=OllamaProvider(
          base_url=settings.ollama_base_url_string,
          http_client=client,
        ),
      )

    return settings.llm_model

  def _create_agent(self) -> PydanticAgent:
    return PydanticAgent(
      self.model,
      instructions=self._system_prompt_for_cache() or (),
      model_settings=self.model_settings,
    )

  def _parse_output(self, output: OutputModel) -> OutputModel:
    return output

  def _system_prompt_for_cache(self) -> str | None:
    module = __import__(type(self).__module__, fromlist=['SYSTEM_PROMPT'])

    return getattr(module, 'SYSTEM_PROMPT', self.settings.llm_system_prompt)

  def _cache_key(
    self,
    prompt: str,
    *,
    system_prompt: str | None,
    output_type: type[Any] | None = None,
    model_settings: ModelSettings | None = None,
  ) -> str | None:
    if self.cache is None:
      return None

    settings = model_settings or self.model_settings

    return self.cache.make_key(
      'llm',
      {
        'agent': type(self).__name__,
        'model': self.settings.llm_model,
        'temperature': settings.get('temperature'),
        'max_tokens': settings.get('max_tokens'),
        'seed': settings.get('seed'),
        'system_prompt': system_prompt,
        'output_type': getattr(output_type, '__name__', str(output_type)),
        'prompt': prompt,
      },
    )

  def _ollama_options(self, model_settings: ModelSettings | None = None) -> dict[str, Any]:
    settings = model_settings or self.model_settings
    options: dict[str, Any] = {}

    if (temperature := settings.get('temperature')) is not None:
      options['temperature'] = temperature
    if (seed := settings.get('seed')) is not None:
      options['seed'] = seed
    if (max_tokens := settings.get('max_tokens')) is not None and max_tokens > 0:
      options['num_predict'] = max_tokens

    return options

  async def _run_ollama(
    self,
    prompt: str,
    *,
    system_prompt: str | None,
    model_settings: ModelSettings | None = None,
    output_type: type[Any] = str,
    response_format: Any = None,
  ) -> Any:
    if self.ollama_client is None:
      raise RuntimeError('Native Ollama client is not configured')

    messages: list[dict[str, str]] = []

    if system_prompt:
      messages.append({'role': 'system', 'content': system_prompt})

    messages.append({'role': 'user', 'content': prompt})

    cache_key = self._cache_key(
      prompt,
      system_prompt=system_prompt,
      output_type=output_type,
      model_settings=model_settings,
    )

    async def run_request() -> Any:
      response = await self.ollama_client.chat(  # pyright: ignore
        model=self.settings.ollama_model_name,
        messages=messages,
        stream=False,
        think=False,
        format=response_format,  # pyright: ignore
        options=self._ollama_options(model_settings),
      )

      return response.message.content or ''

    content = (
      await self.cache.get_or_set(cache_key, self.settings.cache_llm_ttl_seconds, run_request)
      if self.cache is not None and cache_key is not None
      else await run_request()
    )

    if isinstance(output_type, type) and issubclass(output_type, BaseModel):
      return output_type.model_validate_json(content)

    return content

  async def _run(self, prompt: str) -> OutputModel:
    if self.settings.should_use_native_ollama:
      output = await self._run_ollama(prompt, system_prompt=None)
      return self._parse_output(output)

    if self.agent is None:
      raise RuntimeError('Pydantic AI agent is not configured')

    cache_key = (
      self._cache_key(prompt, system_prompt=self._system_prompt_for_cache(), output_type=None)
      if self.cache is not None
      else None
    )

    async def run_request() -> Any:
      result: Any = await self.agent.run(prompt)  # pyright: ignore

      return result.output

    output = (
      await self.cache.get_or_set(cache_key, self.settings.cache_llm_ttl_seconds, run_request)
      if self.cache is not None and cache_key is not None
      else await run_request()
    )

    return self._parse_output(output)

  @staticmethod
  def _build_tool_function(
    name: str,
    context: dict[str, Any],
    registry: ToolRegistry,
    executed_tools: list[ToolResult],
  ) -> Callable[..., Any]:
    async def run_tool(**arguments: Any) -> str:
      result = await registry.execute(name, arguments, context)

      executed_tools.append(result)

      return json.dumps(result.data, ensure_ascii=False)

    tool = registry.tools[name]
    run_tool.__name__ = name
    run_tool.__qualname__ = name
    run_tool.__doc__ = tool.definition.get('function', {}).get('description') or f'Execute {name}.'

    return run_tool


class OllamaAgent:
  """Native Ollama generation wrapper backed by a shared AsyncClient."""

  def __init__(
    self,
    *,
    client: AsyncClient,
    model: str,
    system: str | None = None,
  ) -> None:
    self.client = client
    self.model = model
    self.system = system

  async def generate(
    self,
    prompt: str,
    options: Options | None = None,
  ) -> GenerateResponse | None:
    logger.debug(f'Generating with prompt:\n{prompt}')

    try:
      return await self.client.generate(
        model=self.model,
        prompt=prompt,
        system=self.system or '',
        stream=False,
        think=False,
        options=options,
      )
    except ResponseError as error:
      logger.error('Ollama Error: %s', error.error)
      return None


class UnavailableOllamaAgent:
  """No-op generation wrapper used when Ollama is intentionally unconfigured."""

  def __init__(self, *, system: str | None = None) -> None:
    self.system = system

  async def generate(
    self,
    prompt: str,
    options: Options | None = None,
  ) -> None:
    del prompt, options
    logger.warning('Skipping LLM generation because OREMI_OJO_OLLAMA_BASE_URL is not configured')
    return None


class OllamaToolsAgent:
  """Native Ollama tool agent wrapper backed by a shared AsyncClient."""

  def __init__(
    self,
    *,
    client: AsyncClient,
    model: str,
    tools: list[Tool],
    system: str | None = None,
  ) -> None:
    self.client = client
    self.model = model
    self.system = system
    self.tools = tools

  async def query(
    self,
    message: str,
    tools: list[Tool] | None = None,
  ) -> Sequence[Message.ToolCall] | None:
    messages: list[Message] = []

    if self.system:
      messages.append(Message(role='system', content=self.system))

    messages.append(Message(role='user', content=message))
    messages_dump = [message.model_dump() for message in messages]

    logger.debug(f'Querying with messages {messages}')

    try:
      response = await self.client.chat(
        self.model,
        messages=messages_dump,
        tools=tools or self.tools,
        stream=False,
      )
    except ResponseError as error:
      logger.error('Ollama Error: %s', error.error)
      return None

    return response.message.tool_calls or None


class PydanticGenerateResponse:
  def __init__(self, response: str) -> None:
    self.response = response


class PydanticToolFunction(BaseModel):
  name: str = Field(..., description='Name of the selected tool to call.')
  arguments: dict[str, Any] = Field(default_factory=dict, description='Arguments to pass to the selected tool.')


class PydanticToolCalls(BaseModel):
  calls: list[PydanticToolFunction] = Field(default_factory=list, description='Selected tool calls.')


class PydanticGenerateAgent:
  """Generation wrapper backed by Pydantic AI."""

  def __init__(self, *, model: Any, model_settings: ModelSettings, system: str | None = None) -> None:
    self.agent = PydanticAgent(
      model,
      instructions=system or (),
      model_settings=model_settings,
    )

  async def generate(
    self,
    prompt: str,
    options: Options | None = None,
  ) -> PydanticGenerateResponse | None:
    del options
    logger.debug(f'Generating with prompt:\n{prompt}')

    result: Any = await self.agent.run(prompt)

    return PydanticGenerateResponse(str(result.output or ''))


class PydanticToolsAgent:
  """Tool-selection wrapper backed by Pydantic AI structured output."""

  def __init__(self, *, model: Any, model_settings: ModelSettings, tools: list[Tool], system: str | None = None) -> None:
    self.model = model
    self.model_settings = model_settings
    self.system = system
    self.tools = tools

  @staticmethod
  def _tool_name(tool: Tool) -> str | None:
    return tool.function.name if tool.function else None

  @staticmethod
  def _tool_prompt(tools: list[Tool]) -> str:
    tool_definitions = [tool.model_dump(exclude_none=True) for tool in tools]

    return (
      'Select the tool calls needed to satisfy the user request. '
      'Return only tools from the available tool definitions. '
      'Use an empty calls list when no available tool applies.\n'
      f'Available tools: {json.dumps(tool_definitions, ensure_ascii=False)}'
    )

  async def query(
    self,
    message: str,
    tools: list[Tool] | None = None,
  ) -> Sequence[Message.ToolCall] | None:
    active_tools = tools or self.tools
    tool_names = {name for tool in active_tools if (name := self._tool_name(tool))}
    instructions = '\n'.join(part for part in (self.system, self._tool_prompt(active_tools)) if part)
    agent = PydanticAgent(
      self.model,
      output_type=PydanticToolCalls,
      instructions=instructions,
      model_settings=self.model_settings,
    )

    logger.debug(f'Querying with message {message}')
    result: Any = await agent.run(message)
    calls: list[Message.ToolCall] = []

    for call in result.output.calls:
      if call.name not in tool_names:
        continue

      calls.append(
        Message.ToolCall(
          function=Message.ToolCall.Function(
            name=call.name,
            arguments=call.arguments,
          )
        )
      )

    return calls or None


class UnavailableOllamaToolsAgent:
  """No-op tool wrapper used when Ollama is intentionally unconfigured."""

  def __init__(self, *, system: str | None = None) -> None:
    self.system = system

  async def query(
    self,
    message: str,
    tools: list[Tool] | None = None,
  ) -> None:
    del message, tools
    logger.warning('Skipping LLM tool extraction because OREMI_OJO_OLLAMA_BASE_URL is not configured')
    return None
