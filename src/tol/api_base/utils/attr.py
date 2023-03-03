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
    Must be at the bottom of the decorator stack, if there
    are others.
    """
    function._deferred_attr = True
    name = function.__name__

    @classmethod
    @wraps(function)
    def wrapper(cls, *args, **kwargs):
        value = function(cls, *args, **kwargs)
        setattr(cls, name, value)
    return wrapper
