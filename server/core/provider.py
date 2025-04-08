# Copyright 2024-2025 Sébastien Demanou. All Rights Reserved.
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
import logging
from abc import ABC
from abc import abstractmethod
from typing import Any

from .controller import Controller
from .geo import Location


class Provider(ABC):
  def __init__(self, name: str, controller: Controller, logger: logging.Logger) -> None:
    self.name = name
    self.logger = logger
    self.controller = controller

  @abstractmethod
  def fetch(self, *, location: Location):
    raise NotImplementedError

  class Response:
    def __init__(self, label: str, provider: 'Provider', data: dict[str, Any] | None) -> None:
      self.label = label
      self.provider = provider
      self.data = data or {'API Result': 'No data'}

    def format(self) -> dict[str, dict]:
      return {
        f'{self.label} data from {self.provider.name}': self.data,
      }

    def __str__(self):
      return '\n'.join(
        [f'Provider: {self.provider.name}.']
        + [f'Data type: {self.label}.']
        + [f'{key}: {value}.' for key, value in self.data.items()]
      )
