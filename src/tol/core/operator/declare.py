# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC


def get_operator_member_names(
    class_: type[ABC]
) -> list[str]:
    """
    Gets a list of all operator methods
    """

    return [
        k
        for k in vars(class_).keys()
        if not k.startswith('_')
    ]
