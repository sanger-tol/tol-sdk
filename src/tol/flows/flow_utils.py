# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..core import (
    DataSource,
    DataSourceFilter,
)


class FlowUtils:

    @classmethod
    def get_user_name_and_eln_api_key(
        cls,
        portaldb_ds: DataSource,
        sts_ds: DataSource,
        portal_user_id: str
    ) -> tuple[str, str]:
        """
            Get the user's full name and ELN API key from STS, using the portal user ID to find
            the user's email address and then using that to find the user in STS.
            This is needed because the portal user ID is not the same as the STS user ID,
            but the email address is the same in both systems.
        """
        portal_user = portaldb_ds.get_one('user', portal_user_id)
        email = portal_user.oidc_id
        f = DataSourceFilter(
            and_={
                'email': {
                    'eq': {
                        'value': email
                    }
                }
            }
        )
        sts_list_users = list(
            sts_ds.get_list(
                'user',
                object_filters=f
            )
        )
        assert len(sts_list_users) == 1
        sts_user = sts_list_users[0]
        sts_user_id = sts_user.id

        user_extra = sts_ds.get_one('user_extra', sts_user_id)
        if user_extra is None:
            raise ValueError(f'User extra with id {sts_user_id} not found')
        return sts_user.fullname, user_extra.eln_api_key

    @classmethod
    def get_worklist(cls, bds: DataSource, worklist_name: str) -> str:
        """
        Get the worklist with the given name from Benchling, or return None
        if it doesn't exist. Benchling does not allow searching by name so
        we have to get all worklists and filter in Python.
        """
        if worklist_name is None:
            return None

        try:
            for worklist in bds.get_list('worklist'):
                if worklist.name == worklist_name:
                    return worklist
            return None
        except Exception:
            return None

    @classmethod
    def get_folder(cls, bds: DataSource, folder_name: str) -> str:
        if folder_name is None:
            return None
        try:
            f = DataSourceFilter()
            f.and_ = {'name': {'eq': {'value': folder_name}}}
            folder = next(bds.get_list('folder', object_filters=f))
        except StopIteration:
            return None
        return folder
