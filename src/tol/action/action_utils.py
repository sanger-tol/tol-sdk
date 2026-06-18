# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
from typing import Any

from tol.core import DataSource, DataSourceError


class ActionUtils:
    @staticmethod
    def run_action(
            action: Any,
            params: dict[str, Any],
            user_id: str,
            ids: list[str],
            object_type: str,
            action_ds: DataSource | None = None
    ) -> dict[str, bool]:
        # Try to import the class from tol.actions first, then fall back to main.actions
        action_class = None
        try:
            tol_actions_module = importlib.import_module('tol.action.actions')
            if hasattr(tol_actions_module, action.class_name):
                action_class = getattr(tol_actions_module, action.class_name)

                if action_class is None:
                    main_actions_module = importlib.import_module('main.actions')
                    if hasattr(main_actions_module, action.class_name):
                        action_class = getattr(main_actions_module, action.class_name)

        except ImportError:
            raise DataSourceError(
                'Action Class Import Error',
                'Class not found in tol.actions or main.actions',
                500
            )

        if action_class is None:
            raise DataSourceError(
                'Action Class Not Found',
                f'Action class "{action.class_name}" not found in '
                'tol.action.actions or main.actions',
                404
            )

        # Always add the action params in here
        class_params = params | action.params | {'user_id': user_id}

        action_instance = action_class()
        status = action_instance.run(
            ids=ids, params=class_params,
            object_type=object_type,
            datasource=action_ds
        )
        return status
