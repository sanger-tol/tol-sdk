import json

from ..core import ErrorObject


class PipelineError(Exception):
    def __init__(
        self,
        obj: ErrorObject,
        step_name: str,
    ) -> None:

        self.__obj = obj
        self.__step_name = step_name

        details = json.dumps(obj.details, indent=2)

        self.__message = (
            'An error occured during the pipeline, '
            f'in step "{step_name}", '
            f'on ID "{obj.object_id}".\n\n'
            f'Details:\n{details}'
        )

        super().__init__(self.__message)

    @property
    def message(self) -> str:
        return self.__message

    @property
    def error_object(self) -> ErrorObject:
        return self.__obj

    @property
    def step_name(self) -> str:
        return self.__step_name
