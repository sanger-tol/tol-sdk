# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import urllib3  # noqa
from .main import Interface  # noqa

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
