# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
from typing import Any, cast

from tol.core import (
    DataObjectFactory,
)
from tol.pipeline import (
    ConverterFactory,
    Step,
    StepConfig,
    ValidatorFactory,
)


class PipelineUtils:

    @classmethod
    def import_class(
        cls,
        module: str,
        factory: str,
    ) -> Any:

        __module = importlib.import_module(module)
        return getattr(__module, factory)

    @classmethod
    def instantiate_step(
        cls,
        config: StepConfig,
        data_object_factory: DataObjectFactory,
    ) -> Step:
        step_class = cls.import_class(
            config.module,
            config.class_name,
        )

        if config.is_validator:
            # Access Config directly on the class
            validator_config = step_class.Config(**config.config_details)
            validator_factory = cast(
                ValidatorFactory,
                step_class,
            )
            return validator_factory(
                data_object_factory=data_object_factory,
                config=validator_config,
            )
        else:
            converter_factory = cast(
                ConverterFactory,
                step_class,
            )
            converter_config = step_class.Config(**config.config_details)  # type: ignore
            return converter_factory(
                data_object_factory,
                config=converter_config,
            )
