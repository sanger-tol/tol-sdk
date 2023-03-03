# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import wraps
from typing import Callable


def deferred_attr(function: Callable) -> Callable:
    """
    Indicates that the function will return the
    value for the given attribute name. Its execution
    is deferred until after all classes have been setup.
    """
    function._deferred_attr = True

    @wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
    return wrapper
