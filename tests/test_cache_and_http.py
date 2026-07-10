import asyncio
import importlib.util
from datetime import timedelta
from pathlib import Path
import httpx
import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_module(module_name: str, relative_path: str):
  spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
  module = importlib.util.module_from_spec(spec)
  assert spec.loader is not None
  spec.loader.exec_module(module)
  return module


cache_module = load_module('weather.utils.cache', 'weather/utils/cache.py')

SmartCache = cache_module.SmartCache


def test_smart_cache_keeps_none_values() -> None:
  async def run_test() -> None:
    cache = SmartCache(enabled=True, max_entries=8)
    calls = 0

    async def factory() -> None:
      nonlocal calls
      calls += 1
      return None

    first = await cache.get_or_set('none-key', 60.0, factory)
    second = await cache.get_or_set('none-key', 60.0, factory)

    assert first is None
    assert second is None
    assert calls == 1

  asyncio.run(run_test())
