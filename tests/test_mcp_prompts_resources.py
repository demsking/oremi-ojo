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
import json

import pytest
from fastapi.testclient import TestClient

from ojo import app


def test_mcp_prompts_resources_endpoints_active():
  # Check if streamable HTTP MCP server route /mcp is active for prompts and resources
  with TestClient(app, backend='asyncio') as client:
    # 1. Test prompts list
    payload_prompts = {
      'jsonrpc': '2.0',
      'id': 1,
      'method': 'prompts/list',
      'params': {}
    }
    response = client.post('http://localhost:8080/mcp', json=payload_prompts, headers={'Accept': 'application/json'})
    assert response.status_code == 200
    data = response.json()
    assert 'result' in data
    prompts = data['result']['prompts']
    prompt_names = [p['name'] for p in prompts]
    assert 'current_weather' in prompt_names
    assert 'today_weather' in prompt_names
    assert 'weather_alerts' in prompt_names
    assert 'weather_data_source' in prompt_names
    assert 'air_quality_data_source' in prompt_names
    assert 'pollen_data_source' in prompt_names
    assert 'geocoding_data_source' in prompt_names
    assert 'data_sources_summary' in prompt_names

    # 2. Test resource templates list
    payload_resources = {
      'jsonrpc': '2.0',
      'id': 2,
      'method': 'resources/templates/list',
      'params': {}
    }
    response = client.post('http://localhost:8080/mcp', json=payload_resources, headers={'Accept': 'application/json'})
    assert response.status_code == 200
    data = response.json()
    assert 'result' in data
    templates = data['result']['resourceTemplates']
    resource_uris = [r['uriTemplate'] for r in templates]
    assert 'weather:///{lat}/{lon}/current' in resource_uris
    assert 'weather:///{lat}/{lon}/alerts' in resource_uris
    assert 'weather:///{lat}/{lon}/air-quality' in resource_uris
    assert 'weather:///{lat}/{lon}/pollen' in resource_uris
    assert 'weather:///{lat}/{lon}/pollen/forecast' in resource_uris

    # 3. Test reading a resource via JSON-RPC
    payload_read = {
      'jsonrpc': '2.0',
      'id': 3,
      'method': 'resources/read',
      'params': {
        'uri': 'weather:///48.8534/2.3483/current'
      }
    }
    response = client.post('http://localhost:8080/mcp', json=payload_read, headers={'Accept': 'application/json'})
    assert response.status_code == 200
    read_data = response.json()
    assert 'result' in read_data
    contents = read_data['result']['contents']
    assert len(contents) > 0
    text_content = json.loads(contents[0]['text'])
    assert 'temperature' in text_content


@pytest.mark.asyncio
async def test_mcp_local_prompts():
  mcp = app.state.mcp
  prompts = await mcp.list_prompts()
  prompt_names = [p.name for p in prompts]
  assert 'current_weather' in prompt_names
  assert 'today_weather' in prompt_names
  assert 'weather_alerts' in prompt_names
  assert 'weather_data_source' in prompt_names
  assert 'air_quality_data_source' in prompt_names
  assert 'pollen_data_source' in prompt_names
  assert 'geocoding_data_source' in prompt_names
  assert 'data_sources_summary' in prompt_names

  # Render prompt with arguments
  prompt = await mcp.get_prompt('current_weather', arguments={'location': 'Paris'})
  assert prompt is not None
  assert len(prompt.messages) > 0
  assert 'Paris' in prompt.messages[0].content.text

  # Render prompt without arguments
  prompt_no_args = await mcp.get_prompt('data_sources_summary')
  assert prompt_no_args is not None
  assert len(prompt_no_args.messages) > 0
  assert 'Summary' in prompt_no_args.messages[0].content.text



@pytest.mark.asyncio
async def test_mcp_local_resources():
  mcp = app.state.mcp
  templates = await mcp.list_resource_templates()
  resource_uris = [str(r.uriTemplate) for r in templates]
  assert 'weather:///{lat}/{lon}/current' in resource_uris
  assert 'weather:///{lat}/{lon}/alerts' in resource_uris

  # Read current weather resource
  current_weather_content = await mcp.read_resource('weather:///48.8534/2.3483/current')
  assert current_weather_content is not None
  assert len(current_weather_content) > 0
  assert 'temperature' in current_weather_content[0].content

  # Read air quality resource
  aqi_content = await mcp.read_resource('weather:///48.8534/2.3483/air-quality')
  assert aqi_content is not None
  assert len(aqi_content) > 0
  assert 'value' in aqi_content[0].content or 'level' in aqi_content[0].content
