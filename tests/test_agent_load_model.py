import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest
import httpx
from ollama import ChatResponse
from ollama import GenerateResponse
from ollama import Message
from ollama import ResponseError
from ollama import Tool
from pydantic_ai.models.test import TestModel


ROOT = Path(__file__).resolve().parents[1]


def load_project_module(module_name: str):
  if 'ojo' not in sys.modules:
    package = ModuleType('ojo')
    package.__path__ = [str(ROOT / 'ojo')]  # type: ignore[attr-defined]
    sys.modules['ojo'] = package

  for package_name in ('ojo.core', 'ojo.llm', 'ojo.utils'):
    if package_name not in sys.modules:
      package = ModuleType(package_name)
      package.__path__ = [str(ROOT / package_name.replace('.', '/'))]  # type: ignore[attr-defined]
      sys.modules[package_name] = package

  return importlib.import_module(module_name)


Settings = load_project_module('ojo.core.settings').Settings
AgentClient = load_project_module('ojo.llm.agent').AgentClient
OllamaAgent = load_project_module('ojo.llm.agent').OllamaAgent
OllamaToolsAgent = load_project_module('ojo.llm.agent').OllamaToolsAgent
PydanticGenerateAgent = load_project_module('ojo.llm.agent').PydanticGenerateAgent
PydanticToolsAgent = load_project_module('ojo.llm.agent').PydanticToolsAgent
SmartCache = load_project_module('ojo.utils.cache').SmartCache


class FakeOllamaClient:
  def __init__(self, *, pull_error: Exception | None = None, generate_error: Exception | None = None):
    self.pull_error = pull_error
    self.generate_error = generate_error
    self.calls: list[str] = []

  async def pull(self, model: str, stream: bool = False):
    self.calls.append(f'pull:{model}:{stream}')

    if self.pull_error is not None:
      raise self.pull_error

  async def generate(self, *, model: str, keep_alive: int | None = None, stream: bool = False, **kwargs):
    if 'prompt' in kwargs:
      self.calls.append(f'generate:{model}:{kwargs["prompt"]}:{stream}')
    else:
      self.calls.append(f'generate:{model}:{keep_alive}:{stream}')

    if self.generate_error is not None:
      raise self.generate_error

    return GenerateResponse(response='Bonjour')

  async def chat(self, model: str, *, messages, tools=None, stream: bool = False):
    self.calls.append(f'chat:{model}:{messages[-1]["content"]}:{stream}')

    return ChatResponse(
      message=Message(
        role='assistant',
        tool_calls=[
          Message.ToolCall(
            function=Message.ToolCall.Function(
              name='handle_context_location',
              arguments={'location': 'Douala'},
            )
          )
        ],
      )
    )


def make_agent(fake_ollama_client: FakeOllamaClient) -> AgentClient:
  settings = Settings(
    llm_model='ollama:test-model',
    ollama_base_url='http://localhost:11434',
  )
  agent = AgentClient(settings, None)  # type: ignore[arg-type]
  agent.ollama_client = fake_ollama_client  # type: ignore[assignment]

  return agent


async def test_pydantic_generate_agent_returns_ollama_compatible_response():
  agent = PydanticGenerateAgent(
    model=TestModel(custom_output_text='Bonjour'),
    model_settings={},
    system='test',
  )

  result = await agent.generate('hello')

  assert result is not None
  assert result.response == 'Bonjour'


async def test_pydantic_tools_agent_returns_ollama_compatible_tool_calls():
  agent = PydanticToolsAgent(
    model=TestModel(
      custom_output_args={
        'calls': [
          {
            'name': 'handle_context_location',
            'arguments': {'location': 'Douala'},
          }
        ]
      }
    ),
    model_settings={},
    system='test',
    tools=[
      Tool(
        function=Tool.Function(
          name='handle_context_location',
          description='Handle context location',
        )
      )
    ],
  )

  result = await agent.query('weather in Douala')

  assert result is not None
  assert result[0].function.name == 'handle_context_location'
  assert result[0].function.arguments == {'location': 'Douala'}


async def test_ollama_generate_agent_caches_repeated_prompts():
  fake_ollama_client = FakeOllamaClient()
  cache = SmartCache(enabled=True, max_entries=8)
  agent = OllamaAgent(
    client=fake_ollama_client,
    model='test-model',
    system='test',
    cache=cache,
    cache_ttl_seconds=60.0,
  )

  first = await agent.generate('hello')
  second = await agent.generate('hello')

  assert first is not None
  assert second is not None
  assert first.response == 'Bonjour'
  assert second.response == 'Bonjour'
  assert fake_ollama_client.calls == ['generate:test-model:hello:False']
  assert cache.stats.hits == 1


async def test_ollama_tools_agent_caches_repeated_queries():
  fake_ollama_client = FakeOllamaClient()
  cache = SmartCache(enabled=True, max_entries=8)
  agent = OllamaToolsAgent(
    client=fake_ollama_client,
    model='test-model',
    system='test',
    tools=[
      Tool(
        function=Tool.Function(
          name='handle_context_location',
          description='Handle context location',
        )
      )
    ],
    cache=cache,
    cache_ttl_seconds=60.0,
  )

  first = await agent.query('weather in Douala')
  second = await agent.query('weather in Douala')

  assert first is not None
  assert second is not None
  assert first[0].function.arguments == {'location': 'Douala'}
  assert second[0].function.arguments == {'location': 'Douala'}
  assert fake_ollama_client.calls == ['chat:test-model:weather in Douala:False']
  assert cache.stats.hits == 1


async def test_load_model_continues_after_read_timeout():
  fake_ollama_client = FakeOllamaClient(generate_error=httpx.ReadTimeout('model load timed out'))
  agent = make_agent(fake_ollama_client)

  await agent.load_model()

  assert fake_ollama_client.calls == [
    'pull:test-model:False',
    'generate:test-model:-1:False',
  ]


async def test_load_model_continues_after_ollama_499_response():
  fake_ollama_client = FakeOllamaClient(generate_error=ResponseError('Client Closed Request', 499))
  agent = make_agent(fake_ollama_client)

  await agent.load_model()

  assert fake_ollama_client.calls == [
    'pull:test-model:False',
    'generate:test-model:-1:False',
  ]


async def test_load_model_raises_unexpected_ollama_response_error():
  fake_ollama_client = FakeOllamaClient(generate_error=ResponseError('server error', 500))
  agent = make_agent(fake_ollama_client)

  with pytest.raises(ResponseError):
    await agent.load_model()
