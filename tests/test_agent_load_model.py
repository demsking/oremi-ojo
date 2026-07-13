import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest
import httpx
from ollama import ResponseError


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


class FakeOllamaClient:
  def __init__(self, *, pull_error: Exception | None = None, generate_error: Exception | None = None):
    self.pull_error = pull_error
    self.generate_error = generate_error
    self.calls: list[str] = []

  async def pull(self, model: str, stream: bool = False):
    self.calls.append(f'pull:{model}:{stream}')

    if self.pull_error is not None:
      raise self.pull_error

  async def generate(self, *, model: str, keep_alive: int, stream: bool = False):
    self.calls.append(f'generate:{model}:{keep_alive}:{stream}')

    if self.generate_error is not None:
      raise self.generate_error


def make_agent(fake_ollama_client: FakeOllamaClient) -> AgentClient:
  settings = Settings(
    llm_model='ollama:test-model',
    ollama_base_url='http://localhost:11434',
  )
  agent = AgentClient(settings, None)  # type: ignore[arg-type]
  agent.ollama_client = fake_ollama_client  # type: ignore[assignment]

  return agent


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
