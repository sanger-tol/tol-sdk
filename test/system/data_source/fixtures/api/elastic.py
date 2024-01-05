# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .util import ApiFixture
from ..elastic_ds import elastic


api_elastic = ApiFixture(elastic, 'system-test-api-elastic')
