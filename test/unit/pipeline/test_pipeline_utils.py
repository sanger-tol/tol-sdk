# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.pipeline import (
    PipelineUtils,
    StepConfig,
)


class TestPipelineUtils:
    def test_import_class(self) -> None:
        """
        `import_class` imports the class specified by the module and factory
        name.
        """

        # import a class we know exists
        cls = PipelineUtils.import_class(
            'tol.validators',
            'AllowedKeysValidator',
        )

        # it's the class we expect
        assert cls.__name__ == 'AllowedKeysValidator'

    def test_instantiate_step_validator(self) -> None:
        """
        `instantiate_step` instantiates a step class specified by the module and
        factory name in the config, passing the config details to the class.
        """

        # define a config for a step we know exists
        config = StepConfig(
            module='tol.validators',
            class_name='AllowedKeysValidator',
            is_validator=True,
            config_details={
                'allowed_keys': ['a', 'b', 'c'],
            },
        )

        # instantiate the step
        step = PipelineUtils.instantiate_step(
            config,
            data_object_factory=None,
        )

        # it's an instance of the class we expect
        assert step.__class__.__name__ == 'AllowedKeysValidator'
        # it has the config we expect
        assert step._AllowedKeysValidator__config.allowed_keys == ['a', 'b', 'c']

    def test_instantiate_step_converter(self) -> None:
        """
        `instantiate_step` instantiates a step class specified by the module and
        factory name in the config, passing the config details to the class.
        """

        # define a config for a step we know exists
        config = StepConfig(
            module='tol.flows.converters',
            class_name='PrefixFieldConverter',
            is_validator=False,
            config_details={
                'field_name': 'field1',
                'prefix': 'pre',
            },
        )

        # instantiate the step
        step = PipelineUtils.instantiate_step(
            config,
            data_object_factory=None,
        )

        # it's an instance of the class we expect
        assert step.__class__.__name__ == 'PrefixFieldConverter'
        # it has the config we expect
        assert step._PrefixFieldConverter__config.field_name == 'field1'
        assert step._PrefixFieldConverter__config.prefix == 'pre'
