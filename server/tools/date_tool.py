# Copyright 2025 Sébastien Demanou. All Rights Reserved.
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

import dateutil.parser
from ollama import Tool

from ..core.assistant import Assistant
from ..core.time import get_current_datetime


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


class GetDateTool:
  def __init__(self, assistant: Assistant, logger: logging.Logger):
    self.logger = logger
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

  async def get_contextual_date(
    self, user_input: str, *, timezone: str
  ) -> tuple[Tool.Function, datetime.datetime, datetime.datetime]:
    current_time = get_current_datetime(timezone)
    current_time_zero = get_current_datetime(timezone).replace(minute=0, second=0, microsecond=0)
    result = await self.agent.query(input=(f'User Request: {user_input}.\nCurrent date and time: {current_time}'))

    if result:
      self.logger.debug(f'Extracted date from user input: {result.arguments}')

      if result.name == weather_tool_exec_current.name:
        return weather_tool_exec_current, current_time_zero, current_time_zero

      if result.name == weather_tool_exec_today.name:
        return weather_tool_exec_today, current_time_zero, current_time_zero

      if result.name == weather_tool_exec_morning.name:
        morning_time = current_time_zero.replace(hour=9)
        return weather_tool_exec_morning, morning_time, morning_time

      if result.name == weather_tool_exec_afternoon.name:
        afternoon_time = current_time_zero.replace(hour=15)
        return weather_tool_exec_afternoon, afternoon_time, afternoon_time

      if result.name == weather_tool_exec_night.name:
        night_time = current_time_zero.replace(hour=21)
        return weather_tool_exec_night, night_time, night_time

      if result.name == weather_tool_exec_tomorrow.name:
        tomorrow_date = current_time_zero + datetime.timedelta(days=1)
        return weather_tool_exec_tomorrow, tomorrow_date, tomorrow_date

      if result.name == weather_tool_exec_this_week.name:
        start_of_week = current_time_zero - datetime.timedelta(days=current_time_zero.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        return weather_tool_exec_this_week, start_of_week, end_of_week

      if result.name == weather_tool_exec_weekend.name:
        start_of_weekend = current_time_zero + datetime.timedelta(days=(5 - current_time_zero.weekday()))
        end_of_weekend = start_of_weekend + datetime.timedelta(days=1)
        return weather_tool_exec_weekend, start_of_weekend, end_of_weekend

      if result.name == weather_tool_exec_next_week.name:
        start_of_next_week = current_time_zero + datetime.timedelta(days=(7 - current_time_zero.weekday()))
        end_of_next_week = start_of_next_week + datetime.timedelta(days=6)
        return weather_tool_exec_next_week, start_of_next_week, end_of_next_week

      if result.name == weather_tool_exec_specific_date.name:
        specific_date = result.arguments.get('date')

        if specific_date:
          parsed_date = dateutil.parser.parse(specific_date)
          return weather_tool_exec_specific_date, parsed_date, parsed_date

      if result.name == weather_tool_exec_unknown_date.name:
        self.logger.warning('Unknown date requested, defaulting to current time.')

    return weather_tool_exec_unknown_date, current_time_zero, current_time_zero
