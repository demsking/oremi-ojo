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
import pytest
from fastapi.testclient import TestClient

from ojo import app


def test_mcp_endpoint_active():
  # Check if streamable HTTP MCP server route /mcp is active
  # Running inside a context manager ensures Starlette's lifespan executes,
  # initializing the FastMCP session manager task group.
  with TestClient(app, backend='asyncio') as client:
    payload = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list', 'params': {}}
    response = client.post('http://localhost:8080/mcp', json=payload, headers={'Accept': 'application/json'})
    assert response.status_code == 200
    data = response.json()
    assert 'result' in data
    tools = data['result']['tools']

    tool_names = [tool['name'] for tool in tools]
    assert 'get_current_weather' in tool_names
    assert 'get_hourly_forecast' in tool_names
    assert 'get_daily_forecast' in tool_names
    assert 'get_weather_alerts' in tool_names
    assert 'get_sun_times' in tool_names
    assert 'get_air_quality' in tool_names
    assert 'get_current_pollen' in tool_names
    assert 'get_pollen_forecast' in tool_names
    assert 'search_locations' in tool_names
    assert 'reverse_geocode' in tool_names


@pytest.mark.asyncio
async def test_mcp_local_tools_list():
  mcp = app.state.mcp
  tools = await mcp.list_tools()
  tool_names = [tool.name for tool in tools]
  assert 'get_current_weather' in tool_names
  assert 'get_hourly_forecast' in tool_names
  assert 'get_daily_forecast' in tool_names
  assert 'get_weather_alerts' in tool_names
  assert 'get_sun_times' in tool_names
  assert 'get_air_quality' in tool_names
  assert 'get_current_pollen' in tool_names
  assert 'get_pollen_forecast' in tool_names
  assert 'search_locations' in tool_names
  assert 'reverse_geocode' in tool_names


@pytest.mark.asyncio
async def test_mcp_call_search_locations():
  mcp = app.state.mcp
  _content, result_dict = await mcp.call_tool('search_locations', {'query': 'Paris', 'limit': 1})
  locations = result_dict['result']
  assert isinstance(locations, list)
  assert len(locations) > 0
  assert locations[0]['name'] is not None
  assert locations[0]['lat'] is not None


@pytest.mark.asyncio
async def test_mcp_call_reverse_geocode():
  mcp = app.state.mcp
  _content, result_dict = await mcp.call_tool('reverse_geocode', {'lat': 48.8534951, 'lon': 2.3483915})
  assert result_dict['name'] is not None
  assert result_dict['lat'] == pytest.approx(48.8534951, abs=1e-3)


@pytest.mark.asyncio
async def test_mcp_call_get_air_quality():
  mcp = app.state.mcp
  _content, result_dict = await mcp.call_tool('get_air_quality', {'lat': 48.8534951, 'lon': 2.3483915})
  air_quality = result_dict['result']
  assert 'value' in air_quality
  assert 'level' in air_quality


@pytest.mark.asyncio
async def test_mcp_call_get_current_pollen():
  mcp = app.state.mcp
  _content, result_dict = await mcp.call_tool('get_current_pollen', {'lat': 48.8534951, 'lon': 2.3483915})
  assert result_dict['dominant_pollen'] is not None


@pytest.mark.asyncio
async def test_mcp_call_get_pollen_forecast():
  mcp = app.state.mcp
  _content, result_dict = await mcp.call_tool('get_pollen_forecast', {'lat': 48.8534951, 'lon': 2.3483915})
  assert result_dict['units'] is not None
  assert 'forecast' in result_dict


@pytest.mark.asyncio
async def test_mcp_call_get_current_weather():
  mcp = app.state.mcp
  _content, result_dict = await mcp.call_tool('get_current_weather', {'lat': 48.8534951, 'lon': 2.3483915})
  assert result_dict['temperature'] is not None
  assert 'relative_humidity' in result_dict
  assert 'wind_speed' in result_dict
  assert 'wind_direction' in result_dict
  assert 'wind_direction_compass' in result_dict


@pytest.mark.asyncio
async def test_mcp_call_get_hourly_forecast():
  mcp = app.state.mcp
  _content, result_dict = await mcp.call_tool('get_hourly_forecast', {'lat': 48.8534951, 'lon': 2.3483915, 'hours': 3})
  assert 'forecast' in result_dict
  assert len(result_dict['forecast']) == 3
  assert result_dict['forecast'][0]['temperature'] is not None


@pytest.mark.asyncio
async def test_mcp_call_get_daily_forecast():
  mcp = app.state.mcp
  _content, result_dict = await mcp.call_tool('get_daily_forecast', {'lat': 48.8534951, 'lon': 2.3483915, 'days': 3})
  assert 'forecast' in result_dict
  assert len(result_dict['forecast']) == 3
  assert result_dict['forecast'][0]['temperature_2m_max'] is not None


@pytest.mark.asyncio
async def test_mcp_call_get_weather_alerts():
  mcp = app.state.mcp
  _content, result_dict = await mcp.call_tool('get_weather_alerts', {'lat': 48.8534951, 'lon': 2.3483915})
  assert isinstance(result_dict['result'], list)


@pytest.mark.asyncio
async def test_mcp_call_get_sun_times():
  mcp = app.state.mcp
  _content, result_dict = await mcp.call_tool('get_sun_times', {'lat': 48.8534951, 'lon': 2.3483915, 'days': 2})
  assert isinstance(result_dict['result'], list)
  assert len(result_dict['result']) == 2
  assert 'sunrise' in result_dict['result'][0]
  assert 'sunset' in result_dict['result'][0]
