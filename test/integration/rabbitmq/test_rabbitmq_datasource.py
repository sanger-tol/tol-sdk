# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import uuid
from dataclasses import dataclass
from typing import Any

from tol.core import DataObject, Handler
from tol.sources.rabbitmq import (
    rabbitmq
)


class RecordingHandler(Handler):
    received: list[DataObject] = []

    @dataclass(frozen=True, kw_only=True)
    class Config:
        pass

    def __init__(self, config: Config, **kwargs: Any) -> None:
        pass

    def handle(self, obj: DataObject) -> None:
        RecordingHandler.received.append(obj)


class TestRabbitmqDataSource:

    def test_supported_types(self):
        rds = rabbitmq()
        assert 'bus_message' in rds.supported_types
        assert 'output_message' in rds.supported_types

    def test_attribute_types(self):
        rds = rabbitmq()

        assert 'bus_message' in rds.attribute_types
        assert rds.attribute_types['bus_message']['message_type'] == 'str'
        assert rds.attribute_types['bus_message']['context'] == 'dict[str, Any]'

    # Disabled for now due to flakiness in Rabbit prod service
    def aaa_test_round_trip(self):
        rds = rabbitmq()
        RecordingHandler.received.clear()
        handlers = {
            'test': {
                'module': __name__,
                'class_name': RecordingHandler.__name__,
                'config_details': {}
            }
        }

        # Declare the queue first, otherwise the mandatory publish is unroutable
        rds.consume(handlers, time_limit=0.1)
        RecordingHandler.received.clear()

        context = {'key': 'value', 'run_id': str(uuid.uuid4())}
        test_message = rds.data_object_factory(
            'bus_message',
            attributes={
                'message_type': 'test',
                'context': context
            }
        )
        rds.insert('bus_message', [test_message])

        rds.consume(handlers, time_limit=5)

        assert len(RecordingHandler.received) == 1
        received = RecordingHandler.received[0]
        assert received.type == 'output_message'
        assert received.message_type == 'test'
        assert received.context == context
