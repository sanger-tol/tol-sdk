# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re

BUS_MESSAGE = 'bus_message'
ROUTING_KEY_PATTERN = re.compile(r'^[a-z0-9_-]+(\.[a-z0-9_-]+){2,}$')
