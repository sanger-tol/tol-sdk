# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable, Mapping
from os import PathLike

from jinja2 import (
    ChoiceLoader,
    Environment,
    FileSystemLoader,
    PackageLoader,
    StrictUndefined,
    select_autoescape
)


class TemplateRenderer:
    """
    Renders '<name>.subject.txt and '<name>.body.html' email templates.

    App directories are searched in order, then the SDK's own templates,
    so an app can extend or shadow 'tol_base.html'.
    """

    __slots__ = ('__env',)

    def __init__(
        self,
        template_dirs: Iterable[str | PathLike[str]] = ()
    ) -> None:
        if isinstance(template_dirs, str):
            raise TypeError(
                'template_dirs must be a list of directories, not one path'
            )

        self.__env = Environment(
            loader=ChoiceLoader([
                FileSystemLoader(list(template_dirs)),
                PackageLoader('tol.notify', 'templates')
            ]),
            autoescape=select_autoescape(),
            undefined=StrictUndefined
        )

    def render(
        self,
        name: str,
        context: Mapping[str, object],
    ) -> tuple[str, str]:
        """Return (subject, html) for the named email."""
        subject = self.__env.get_template(f'{name}.subject.txt').render(context)
        html = self.__env.get_template(f'{name}.body.html').render(context)

        return ' '.join(subject.split()), html
