# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
import re


def __getattr__(name: str):
	"""
    Lazily load an action class from its snake_case module.
	"""
	module_name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
	action_module = importlib.import_module(f'.{module_name}', __name__)
	return getattr(action_module, name)
