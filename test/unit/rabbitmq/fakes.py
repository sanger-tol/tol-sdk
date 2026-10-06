# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

"""Handler and dispatcher fakes, built from specs like real ones."""

from dataclasses import dataclass
from typing import Any

from tol.core import DataObject, Handler
from tol.rabbitmq.dispatchers import Dispatcher
from tol.rabbitmq.schema import NotificationDelivery


def spec(class_name, **config_details):
    """Return a spec for a class in this module."""
    return {
        'module': __name__,
        'class_name': class_name,
        'config_details': config_details
    }


def recording_channels(**sinks):
    """Return channel specs that record deliveries into `sinks`."""
    return {
        channel: spec('RecordingDispatcher', sink=sink)
        for channel, sink in sinks.items()
    }


def notification_handler_spec(**sinks):
    """Return a `NotificationHandler` spec recording into `sinks`."""
    return {
        'module': 'tol.rabbitmq.handlers',
        'class_name': 'NotificationHandler',
        'config_details': {'channels': recording_channels(**sinks)}
    }


class RecordingHandler(Handler):
    """Appends every message to `config.sink`."""

    @dataclass(frozen=True, kw_only=True)
    class Config:
        sink: list[DataObject]

    def __init__(self, config: Config, **kwargs: Any) -> None:
        self.__sink = config.sink

    def handle(self, obj: DataObject) -> None:
        self.__sink.append(obj)


class RaisingHandler(Handler):
    """Rejects every message."""

    @dataclass(frozen=True, kw_only=True)
    class Config:
        pass

    def __init__(self, config: Config, **kwargs: Any) -> None:
        pass

    def handle(self, obj: DataObject) -> None:
        raise RuntimeError('handler blew up')


class RecordingDispatcher(Dispatcher):
    """Appends every delivery to `config.sink`."""

    @dataclass(frozen=True, kw_only=True)
    class Config:
        sink: list[NotificationDelivery]

    def __init__(self, config: Config, **kwargs: Any) -> None:
        self.__sink = config.sink

    def dispatch(self, delivery: NotificationDelivery) -> None:
        self.__sink.append(delivery)


class NotAHandler:
    """Has a Config but does not subclass Handler."""

    @dataclass(frozen=True, kw_only=True)
    class Config:
        pass

    def __init__(self, config: Config, **kwargs: Any) -> None:
        pass
