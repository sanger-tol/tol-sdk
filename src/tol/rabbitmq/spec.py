# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
from collections.abc import Mapping
from typing import Any, TypeVar

T = TypeVar('T')


def instantiate(spec: Mapping[str, Any], base: type[T], **kwargs: Any) -> T:
    """
    Build `{'module', 'class_name', 'config_details'}` the way pipelines
    build steps: `cls(config=cls.Config(**config_details), **kwargs)`.

    Raises `TypeError` unless the class subclasses `base`.
    """
    module = importlib.import_module(spec['module'])
    cls = getattr(module, spec['class_name'])
    if not (isinstance(cls, type) and issubclass(cls, base)):
        raise TypeError(
            f'{spec["module"]}.{spec["class_name"]} is not a {base.__name__}'
        )

    config = getattr(cls, 'Config')(**spec.get('config_details', {}))
    return cls(config=config, **kwargs)  # type: ignore
