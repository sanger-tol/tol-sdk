# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


from .a import A  # noqa
from .b import B  # noqa
from .r1 import R1  # noqa
from .r2 import R2  # noqa
from .r3 import R3  # noqa
from .ext import ExtDefault, ExtOverride  # noqa

delete_models_list = [
    A,
    B,
    R3,  # must come before R1, as it points to it
    R1,
    R2,
    ExtDefault,
    ExtOverride
]

create_models_list = list(reversed(delete_models_list))
