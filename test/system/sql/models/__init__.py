# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


from .a import A
from .b import B
from .standard import standard_models
from .c import C
from .ext import ExtDefault, ExtOverride
from .gs import GS
from .inc import Inc
from .r1 import R1
from .r2 import R2
from .r3 import R3
from .r4 import R4
from .r5 import R5
from .user_mixin import TestUserMixin  # noqa F401

delete_models_list = [
    A,
    B,
    C,
    GS,
    Inc,
    R3,  # must come before R1, as it points to it
    R4,  # must come before R3, as it points to it
    R1,
    R5,
    R2,
    ExtDefault,
    ExtOverride,
    *standard_models  # these are already in deletion order
]

create_models_list = list(reversed(delete_models_list))
