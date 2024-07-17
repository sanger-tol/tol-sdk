# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from datetime import datetime, timedelta, timezone
from tempfile import NamedTemporaryFile

import pandas as pd

import requests

from tol.core import OperableDataSource
from tol.core.operator import RelationWriteMode

from ..dec import against_api
from ..fixtures import all_api


class TestExcel:
    """
    The excel download/export feature on `api_base2`.
    """

    @against_api(*all_api)
    def test_export_one(
        self,
        data_source: OperableDataSource,
        url: str,
        ds_sleep
    ):
        """
        upserting one and getting it back

        includes:
        - relationship fields
        - and relationship field filtering
        - `datetime` fields with tzinfo
          (Regression TOLP-7749)
        - hidden fields
        """

        tzinfo = timezone(
            timedelta(hours=-1)
        )

        now = datetime.now(tz=tzinfo)

        related = data_source.data_object_factory(
            'related',
            '100',
            attributes={
                'str_column': 'match please',
                'datetime_column': now
            }
        )
        root = data_source.data_object_factory(
            'root',
            '200',
            attributes={
                'int_column': 23898,
                'bool_column': False
            },
            to_one={
                'related_object': related
            }
        )

        if data_source.write_mode['root'] == RelationWriteMode.SEPARATE:
            data_source.upsert('related', [related])
        data_source.upsert('root', [root])

        ds_sleep(5)

        # filter out archetypes
        filters = json.dumps(
            {
                'and_': {
                    'int_column': {
                        'eq': {
                            'value': 42,
                            'negate': True
                        }
                    }
                }
            }
        )
        fields = [
            {
                'display_name': 'String Mine',
                'hidden': False,
                'key': 'related_object.str_column'
            },
            {
                'display_name': 'TOLP-7749 begone',
                'hidden': False,
                'key': 'related_object.datetime_column'
            },
            {
                'display_name': 'A Fun Integer',
                'hidden': False,
                'key': 'int_column'
            },
            {
                'display_name': 'No Matter I am hidden',
                'hidden': True,
                'key': 'bool_column'
            }
        ]

        df = self.__fetch_excel(
            f'{url}/data/root:export?filter={filters}',
            body={
                'data': fields
            }
        )

        expected_columns = [
            'String Mine',
            'TOLP-7749 begone',
            'A Fun Integer'
        ]
        observed_columns = list(df.columns)
        assert observed_columns == expected_columns

        assert len(df) == 1
        observed_values = list(df.iloc[0])

        assert observed_values[0] == 'match please'
        assert observed_values[2] == 23898

        # compare dates, accounting for precision
        expected_date = now.replace(microsecond=0, tzinfo=None)
        observed_date = observed_values[1].to_pydatetime().replace(
            microsecond=0
        ) + timedelta(hours=-1)  # modify with new timezone
        assert observed_date == expected_date

    def __fetch_excel(
        self,
        url: str,
        body: dict | None = None,
        sheet_name: str = 'Sheet1',
        engine: str = 'openpyxl',
    ) -> pd.DataFrame:

        with NamedTemporaryFile(suffix='.xlsx') as temp_file:
            filepath = temp_file.name

            r = requests.post(url, json=body)
            r.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(r.content)

            return pd.read_excel(
                filepath,
                sheet_name=sheet_name,
                engine=engine
            )
