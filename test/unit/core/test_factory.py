# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject, DataSource, core_data_object
from tol.core.datasource import unsupported


class _MockDataSource1(DataSource):
    @property
    def supported_types(self):
        return []

    def get_attribute_types(self, object_type: str):
        return {}

    @unsupported
    def get_by_id(*args, **kwargs):
        pass

    @unsupported
    def get_list(*args, **kwargs):
        pass

    @unsupported
    def get_list_page(*args, **kwargs):
        pass

    @unsupported
    def get_aggregations(*args, **kwargs):
        pass


class TestCoreDataObject:
    def test_data_object_returned(self):
        """returns a DataObject implementation"""

        result = core_data_object(_MockDataSource1({}))
        assert issubclass(result, DataObject)

    def test_data_source_given_factory(self):
        """
        A DataSource instance given to core_data_object is given a factory
        """

        ds = _MockDataSource1({})
        core_data_object(ds)
        assert ds.data_object_factory is not None
