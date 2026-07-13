# Copyright 2025-2026 Sébastien Demanou. All Rights Reserved.
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
import datetime
import logging
import re
import unicodedata
from typing import Any
from typing import ClassVar
from typing import Literal
from typing import Mapping

import dateutil.parser
from ollama import Tool

from ..llm.agent import AgentClient
from ..utils.time import get_current_datetime

logger = logging.getLogger(__name__)


weather_tool_exec_current = Tool.Function(
  name='exec_current',
)

weather_tool_exec_today = Tool.Function(
  name='exec_today',
)

weather_tool_exec_morning = Tool.Function(
  name='exec_today_morning',
)

weather_tool_exec_afternoon = Tool.Function(
  name='exec_today_evening',
)

weather_tool_exec_night = Tool.Function(
  name='exec_today_night',
)

weather_tool_exec_tomorrow = Tool.Function(
  name='exec_tomorrow',
)

weather_tool_exec_this_week = Tool.Function(
  name='exec_this_week',
)

weather_tool_exec_weekend = Tool.Function(
  name='exec_weekend',
)

weather_tool_exec_next_week = Tool.Function(
  name='exec_next_week',
)

weather_tool_exec_specific_date = Tool.Function(
  name='exec_specific_date',
)

weather_tool_exec_unknown_date = Tool.Function(
  name='exec_unknown_date',
)

weather_tools = [
  weather_tool_exec_current,
  weather_tool_exec_today,
  weather_tool_exec_morning,
  weather_tool_exec_afternoon,
  weather_tool_exec_night,
  weather_tool_exec_tomorrow,
  weather_tool_exec_this_week,
  weather_tool_exec_weekend,
  weather_tool_exec_next_week,
  weather_tool_exec_specific_date,
  weather_tool_exec_unknown_date,
]


Period = Literal['hourly', 'daily', 'weekly']


class GetDateTool:
  MORNING_HOUR: ClassVar[int] = 9
  AFTERNOON_HOUR: ClassVar[int] = 15
  NIGHT_HOUR: ClassVar[int] = 21

  _hour_pattern = re.compile(r'\b(?:(\d{1,2})\s*h(?:\s*(\d{1,2}))?|((?:[01]?\d|2[0-3])):(\d{2}))\b', re.IGNORECASE)
  _date_pattern = re.compile(r'\b(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|\d{4}-\d{2}-\d{2})\b')

  _temporal_patterns: ClassVar[dict[str, re.Pattern[str]]] = {
    'morning': re.compile(r'\b(morning|ce matin)\b', re.IGNORECASE),
    'afternoon': re.compile(r'\b(afternoon|apres midi|cet apres midi|cette apres midi)\b', re.IGNORECASE),
    'night': re.compile(r'\b(tonight|ce soir|night)\b', re.IGNORECASE),
    'today': re.compile(r'\b(today|aujourd hui|aujourdhui|aujourd)\b', re.IGNORECASE),
    'tomorrow': re.compile(r'\b(tomorrow|demain)\b', re.IGNORECASE),
    'this_week': re.compile(r'\b(this week|cette semaine)\b', re.IGNORECASE),
    'weekend': re.compile(r'\b(weekend|week-end)\b', re.IGNORECASE),
    'next_week': re.compile(r'\b(next week|semaine prochaine)\b', re.IGNORECASE),
  }

  period_map: ClassVar[dict[str, Period]] = {
    weather_tool_exec_current.name: 'hourly',
    weather_tool_exec_today.name: 'daily',
    weather_tool_exec_morning.name: 'hourly',
    weather_tool_exec_afternoon.name: 'hourly',
    weather_tool_exec_night.name: 'hourly',
    weather_tool_exec_tomorrow.name: 'daily',
    weather_tool_exec_this_week.name: 'weekly',
    weather_tool_exec_weekend.name: 'weekly',
    weather_tool_exec_next_week.name: 'weekly',
    weather_tool_exec_specific_date.name: 'daily',
    weather_tool_exec_unknown_date.name: 'daily',
  }  # type: ignore

  def __init__(self, assistant: AgentClient):
    self.agent = assistant.create_tools_agent(
      system=(
        "You are a smart assistant. Your task is to extract the relevant date or date range from the user's request, if present, "
        'and call the appropriate tool(s) to retrieve the relevant weather data. '
        "Use the provided tools for extracting either a single date or a date range based on the user's request.\n\n"
        "In the event that no specific date or range is mentioned, use the device's current date and time.\n"
        'If the date or range is unclear, return the current date for the single date or a default range (e.g., today).'
      ),
      tools=[Tool(function=item) for item in weather_tools],
    )

  @staticmethod
  def _tool_name(tool: Tool.Function) -> str:
    return tool.name or ''

  @staticmethod
  def _normalize_text(user_input: str) -> str:
    normalized = unicodedata.normalize('NFKD', user_input)
    normalized = normalized.encode('ascii', 'ignore').decode('ascii')
    normalized = normalized.replace("'", ' ')
    return re.sub(r'\s+', ' ', normalized.lower()).strip()

  @staticmethod
  def _extract_hour(user_input: str) -> tuple[int, int] | None:
    match = GetDateTool._hour_pattern.search(GetDateTool._normalize_text(user_input))

    if not match:
      return None

    hour = match.group(1) or match.group(3)
    minute = match.group(2) or match.group(4) or '0'

    parsed_hour = int(hour)
    parsed_minute = int(minute)

    if 0 <= parsed_hour <= 23 and 0 <= parsed_minute <= 59:
      return parsed_hour, parsed_minute

    return None

  @staticmethod
  def _extract_specific_date(user_input: str) -> datetime.datetime | None:
    normalized = GetDateTool._normalize_text(user_input)
    match = GetDateTool._date_pattern.search(normalized)

    if not match:
      return None

    try:
      return dateutil.parser.parse(match.group(1), dayfirst=True)
    except (ValueError, OverflowError):
      return None

  @staticmethod
  def _has_explicit_day_marker(user_input: str) -> bool:
    normalized = GetDateTool._normalize_text(user_input)
    return any(pattern.search(normalized) for pattern in GetDateTool._temporal_patterns.values())

  @staticmethod
  def _compute_week_range(current_time_zero: datetime.datetime) -> tuple[datetime.datetime, datetime.datetime]:
    start_of_week = current_time_zero - datetime.timedelta(days=current_time_zero.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    return start_of_week, end_of_week

  @staticmethod
  def _compute_weekend_range(current_time_zero: datetime.datetime) -> tuple[datetime.datetime, datetime.datetime]:
    days_until_saturday = (5 - current_time_zero.weekday()) % 7
    start_of_weekend = current_time_zero + datetime.timedelta(days=days_until_saturday)
    end_of_weekend = start_of_weekend + datetime.timedelta(days=1)
    return start_of_weekend, end_of_weekend

  @staticmethod
  def _compute_next_week_range(current_time_zero: datetime.datetime) -> tuple[datetime.datetime, datetime.datetime]:
    days_until_next_monday = (7 - current_time_zero.weekday()) % 7

    if days_until_next_monday == 0:
      days_until_next_monday = 7

    start_of_next_week = current_time_zero + datetime.timedelta(days=days_until_next_monday)
    end_of_next_week = start_of_next_week + datetime.timedelta(days=6)
    return start_of_next_week, end_of_next_week

  @staticmethod
  def _select_tool_name(user_input: str, tool_names: list[str]) -> str:
    normalized = GetDateTool._normalize_text(user_input)

    # Prefer explicit temporal intent matches over raw first tool call.
    intent_priority: list[tuple[str, str]] = [
      ('morning', GetDateTool._tool_name(weather_tool_exec_morning)),
      ('afternoon', GetDateTool._tool_name(weather_tool_exec_afternoon)),
      ('night', GetDateTool._tool_name(weather_tool_exec_night)),
      ('tomorrow', GetDateTool._tool_name(weather_tool_exec_tomorrow)),
      ('weekend', GetDateTool._tool_name(weather_tool_exec_weekend)),
      ('next_week', GetDateTool._tool_name(weather_tool_exec_next_week)),
      ('this_week', GetDateTool._tool_name(weather_tool_exec_this_week)),
      ('today', GetDateTool._tool_name(weather_tool_exec_today)),
    ]

    for intent, tool_name in intent_priority:
      if GetDateTool._temporal_patterns[intent].search(normalized) and tool_name in tool_names:
        return tool_name

    specific_date_tool = GetDateTool._tool_name(weather_tool_exec_specific_date)

    if specific_date_tool in tool_names:
      return specific_date_tool

    for tool_name in tool_names:
      if tool_name != GetDateTool._tool_name(weather_tool_exec_unknown_date):
        return tool_name

    return GetDateTool._tool_name(weather_tool_exec_unknown_date)

  @staticmethod
  def _resolve_tool_output(
    *,
    tool_name: str,
    arguments: Mapping[str, Any],
    current_time_zero: datetime.datetime,
  ) -> tuple[Tool.Function, datetime.datetime, datetime.datetime] | None:
    if tool_name == weather_tool_exec_current.name:
      return weather_tool_exec_current, current_time_zero, current_time_zero

    if tool_name == weather_tool_exec_today.name:
      return weather_tool_exec_today, current_time_zero, current_time_zero

    if tool_name == weather_tool_exec_morning.name:
      morning_time = current_time_zero.replace(hour=GetDateTool.MORNING_HOUR)
      return weather_tool_exec_morning, morning_time, morning_time

    if tool_name == weather_tool_exec_afternoon.name:
      afternoon_time = current_time_zero.replace(hour=GetDateTool.AFTERNOON_HOUR)
      return weather_tool_exec_afternoon, afternoon_time, afternoon_time

    if tool_name == weather_tool_exec_night.name:
      night_time = current_time_zero.replace(hour=GetDateTool.NIGHT_HOUR)
      return weather_tool_exec_night, night_time, night_time

    if tool_name == weather_tool_exec_tomorrow.name:
      tomorrow_date = current_time_zero + datetime.timedelta(days=1)
      return weather_tool_exec_tomorrow, tomorrow_date, tomorrow_date

    if tool_name == weather_tool_exec_this_week.name:
      start_of_week, end_of_week = GetDateTool._compute_week_range(current_time_zero)
      return weather_tool_exec_this_week, start_of_week, end_of_week

    if tool_name == weather_tool_exec_weekend.name:
      start_of_weekend, end_of_weekend = GetDateTool._compute_weekend_range(current_time_zero)
      return weather_tool_exec_weekend, start_of_weekend, end_of_weekend

    if tool_name == weather_tool_exec_next_week.name:
      start_of_next_week, end_of_next_week = GetDateTool._compute_next_week_range(current_time_zero)
      return weather_tool_exec_next_week, start_of_next_week, end_of_next_week

    if tool_name == weather_tool_exec_specific_date.name:
      specific_date = arguments.get('date') if arguments else None

      if isinstance(specific_date, str) and specific_date.strip():
        parsed_date = dateutil.parser.parse(specific_date)
        return weather_tool_exec_specific_date, parsed_date, parsed_date

      return None

    if tool_name == weather_tool_exec_unknown_date.name:
      return weather_tool_exec_unknown_date, current_time_zero, current_time_zero

    return None

  async def get_date(self, user_input: str, *, timezone: str) -> tuple[Tool.Function, datetime.datetime, datetime.datetime]:
    current_time = get_current_datetime(timezone)
    current_time_zero = current_time.replace(minute=0, second=0, microsecond=0)

    # Explicit hour in the query should produce an hourly request at that hour.
    hour_info = GetDateTool._extract_hour(user_input)

    if hour_info:
      hour, minute = hour_info
      target_time = current_time_zero.replace(hour=hour, minute=minute)
      return weather_tool_exec_current, target_time, target_time

    specific_date = GetDateTool._extract_specific_date(user_input)

    if specific_date:
      target_date = specific_date.replace(hour=0, minute=0, second=0, microsecond=0)
      return weather_tool_exec_specific_date, target_date, target_date

    # If no explicit day/range marker is present, default to current conditions.
    if not GetDateTool._has_explicit_day_marker(user_input):
      return weather_tool_exec_current, current_time_zero, current_time_zero

    current_time_minute = current_time.replace(second=0, microsecond=0)
    results = await self.agent.query(f'User Request: {user_input}.\nCurrent date and time: {current_time_minute}.')

    if results:
      function_calls = [result.function for result in results]
      tool_names = [function_call.name for function_call in function_calls]
      selected_tool_name = GetDateTool._select_tool_name(user_input, tool_names)
      selected_call = next(
        (function_call for function_call in function_calls if function_call.name == selected_tool_name),
        function_calls[0],
      )

      logger.debug(f'Extracted date tool from user input: {selected_tool_name} args={selected_call.arguments}')

      resolved = GetDateTool._resolve_tool_output(
        tool_name=selected_tool_name,
        arguments=selected_call.arguments,
        current_time_zero=current_time_zero,
      )

      if resolved:
        return resolved

      logger.warning('Unable to resolve extracted date tool output, defaulting to current time.')

    return weather_tool_exec_unknown_date, current_time_zero, current_time_zero
