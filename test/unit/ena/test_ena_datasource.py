# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock, create_autospec

import pytest
from requests.exceptions import HTTPError

from tol.core import (
    core_data_object,
    DataObject,
    DataSourceError,
    DataSourceFilter,
)
from tol.ena import EnaDataSource


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {},
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes

    return data_object


class TestEnaDataSource:
    def test_get_by_id_found(self):
        """200 response"""

        mock_client = Mock()

        mock_response = {
            'study_accession': 'PRJEB48587',
        }

        mock_client.get_detail.return_value = ([mock_response])

        mock_lc_converter = Mock()

        ds = EnaDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter,
            None
        )

        ds.data_object_factory = lambda: Mock()

        mock_data_object = _get_mock_data_object(
            type_='study',
            id_='an ID',
        )

        mock_lc_converter.convert_list.return_value = ([mock_data_object], 1)

        observed = list(ds.get_by_id('study', ['an ID']))
        assert observed == [mock_data_object]

        mock_client.get_detail.assert_called_once_with(
            'study',
            ['an ID'],
        )

        mock_lc_converter.convert_list.assert_called_once_with(
            'study',
            [mock_response]
        )

    def test_get_by_id_not_found(self):
        """404 response"""

        mock_client = Mock()

        # mock a 404 returning 'None'
        mock_client.get_detail.return_value = []
        mock_response = {
            'study_accession': 'PRJEB48587',
        }
        mock_client.get_fields.return_value = mock_response

        mock_lc_converter = Mock()
        mock_lc_converter.convert_list.return_value = ([], 0)

        ds = EnaDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter,
            None
        )
        ds.data_object_factory = lambda: Mock()

        (observed,) = list(ds.get_by_id('study', ['an ID']))
        assert observed is None

        mock_client.get_detail.assert_called_once_with(
            'study',
            ['an ID'],
        )

        mock_lc_converter.convert_list.assert_called_once_with(
            'study',
            []
        )

    def test_bad_object_type(self):
        """A bad object type -> raise DataSourceError()"""
        mock_client = Mock()

        # mock a 404 returning 'None'
        mock_client.get_detail.return_value = []
        mock_response = {
            'study_accession': 'PRJEB48587',
        }
        mock_client.get_fields.return_value = mock_response

        ds = EnaDataSource(
            lambda: mock_client,
            lambda: None,
            None
        )
        with pytest.raises(DataSourceError):
            list(ds.get_by_id('test', ['does not matter at all']))

    def test_get_list_populated(self):
        """
        `EnaDataSource().get_listpage()` gets populated list
        from client. `filter` is populated.
        """

        mock_objs = [Mock() for _ in range(3)]

        mock_json = Mock()

        mock_client = Mock()
        mock_client.config.attribute_types.return_value = {
            'assembly': {},
        }
        mock_client.get_list_page.return_value = (mock_json)
        mock_response = {}
        mock_client.get_fields.return_value = mock_response
        mock_converter = Mock()
        mock_converter.convert_list.return_value = (mock_objs, 3)

        mock_filter = Mock()
        mock_filter.dumps.return_value = 'tax_id="9662"'

        ena_ds = EnaDataSource(
            lambda: mock_client,
            lambda: mock_converter,
            lambda: mock_filter
        )

        f = DataSourceFilter()
        f.and_ = {'tax_id': {'eq': {'value': '9662'}}}

        observed = list(ena_ds.get_list(
            'assembly',
            object_filters=f
        ))

        mock_client.get_list.assert_called_once_with(
            'assembly',
            filter_string='tax_id="9662"'
        )
        mock_filter.dumps.assert_called_once_with(f)
        assert observed == (list(mock_objs))

    def test_supported_types(self):
        expected = [
            'assembly', 'read_run', 'sample', 'study', 'taxon',
            'checklist', 'submittable_taxon', 'read_experiment', 'analysis'
        ]
        mock_client = Mock()
        mock_response = {}

        mock_client.get_fields.return_value = mock_response
        ds = EnaDataSource(
            lambda: mock_client,
            lambda: None,
            None
        )

        observed = ds.supported_types
        assert observed == expected

    def test_get_to_one_relation_assembly_study(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='assembly', study_accession='123')

        observed = EnaDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'study'
        )

        mock_ds.get_one.assert_called_once_with('study', '123')
        assert observed is mock_ds.get_one.return_value

        # Missing and empty references must not trigger another lookup.
        mock_ds.get_one.reset_mock()
        for accession in (None, ''):
            mock_object.study_accession = accession
            assert EnaDataSource.get_to_one_relation(
                mock_ds, mock_object, 'study'
            ) is None
        mock_ds.get_one.assert_not_called()

    def test_get_to_one_relation_assembly_sample(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='assembly', sample_accession='123')

        observed = EnaDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'sample'
        )

        mock_ds.get_one.assert_called_once_with('sample', '123')
        assert observed is mock_ds.get_one.return_value

        # Missing and empty references must not trigger another lookup.
        mock_ds.get_one.reset_mock()
        for accession in (None, ''):
            mock_object.sample_accession = accession
            assert EnaDataSource.get_to_one_relation(
                mock_ds, mock_object, 'sample'
            ) is None
        mock_ds.get_one.assert_not_called()

    def test_get_to_one_relation_assembly_taxon(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='assembly', tax_id='123')

        observed = EnaDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'taxon'
        )

        mock_ds.get_one.assert_called_once_with('taxon', '123')
        assert observed is mock_ds.get_one.return_value

        # Missing and empty references must not trigger another lookup.
        mock_ds.get_one.reset_mock()
        for accession in (None, ''):
            mock_object.tax_id = accession
            assert EnaDataSource.get_to_one_relation(
                mock_ds, mock_object, 'taxon'
            ) is None
        mock_ds.get_one.assert_not_called()

    def test_get_to_one_relation_read_run_experiment(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='read_run', experiment_accession='123')

        observed = EnaDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'experiment'
        )

        mock_ds.get_one.assert_called_once_with('read_experiment', '123')
        assert observed is mock_ds.get_one.return_value

        # Missing and empty references must not trigger another lookup.
        mock_ds.get_one.reset_mock()
        for accession in (None, ''):
            mock_object.experiment_accession = accession
            assert EnaDataSource.get_to_one_relation(
                mock_ds, mock_object, 'experiment'
            ) is None
        mock_ds.get_one.assert_not_called()

    def test_get_to_one_relation_read_run_sample(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='read_run', sample_accession='123')

        observed = EnaDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'sample'
        )

        mock_ds.get_one.assert_called_once_with('sample', '123')
        assert observed is mock_ds.get_one.return_value

        # Missing and empty references must not trigger another lookup.
        mock_ds.get_one.reset_mock()
        for accession in (None, ''):
            mock_object.sample_accession = accession
            assert EnaDataSource.get_to_one_relation(
                mock_ds, mock_object, 'sample'
            ) is None
        mock_ds.get_one.assert_not_called()

    def test_get_to_one_relation_read_run_study(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='read_run', study_accession='123')

        observed = EnaDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'study'
        )

        mock_ds.get_one.assert_called_once_with('study', '123')
        assert observed is mock_ds.get_one.return_value

        # Missing and empty references must not trigger another lookup.
        mock_ds.get_one.reset_mock()
        for accession in (None, ''):
            mock_object.study_accession = accession
            assert EnaDataSource.get_to_one_relation(
                mock_ds, mock_object, 'study'
            ) is None
        mock_ds.get_one.assert_not_called()

    def test_get_to_one_relation_read_run_taxon(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='read_run', tax_id='123')

        observed = EnaDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'taxon'
        )

        mock_ds.get_one.assert_called_once_with('taxon', '123')
        assert observed is mock_ds.get_one.return_value

        # Missing and empty references must not trigger another lookup.
        mock_ds.get_one.reset_mock()
        for accession in (None, ''):
            mock_object.tax_id = accession
            assert EnaDataSource.get_to_one_relation(
                mock_ds, mock_object, 'taxon'
            ) is None
        mock_ds.get_one.assert_not_called()

    def test_get_to_one_relation_read_experiment_study(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='read_experiment', study_accession='123')

        observed = EnaDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'study'
        )

        mock_ds.get_one.assert_called_once_with('study', '123')
        assert observed is mock_ds.get_one.return_value

        # Missing and empty references must not trigger another lookup.
        mock_ds.get_one.reset_mock()
        for accession in (None, ''):
            mock_object.study_accession = accession
            assert EnaDataSource.get_to_one_relation(
                mock_ds, mock_object, 'study'
            ) is None
        mock_ds.get_one.assert_not_called()

    def test_get_to_one_relation_read_experiment_sample(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='read_experiment', sample_accession='123')

        observed = EnaDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'sample'
        )

        mock_ds.get_one.assert_called_once_with('sample', '123')
        assert observed is mock_ds.get_one.return_value

        # Missing and empty references must not trigger another lookup.
        mock_ds.get_one.reset_mock()
        for accession in (None, ''):
            mock_object.sample_accession = accession
            assert EnaDataSource.get_to_one_relation(
                mock_ds, mock_object, 'sample'
            ) is None
        mock_ds.get_one.assert_not_called()

    def test_get_to_one_relation_sample_taxon(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='sample', tax_id='123')

        observed = EnaDataSource.get_to_one_relation(
            mock_ds,
            mock_object,
            'taxon'
        )

        mock_ds.get_one.assert_called_once_with('taxon', '123')
        assert observed is mock_ds.get_one.return_value

        # Missing and empty references must not trigger another lookup.
        mock_ds.get_one.reset_mock()
        for accession in (None, ''):
            mock_object.tax_id = accession
            assert EnaDataSource.get_to_one_relation(
                mock_ds, mock_object, 'taxon'
            ) is None
        mock_ds.get_one.assert_not_called()

    def test_get_to_many_relations_read_experiment_runs(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='read_experiment', id='123')

        observed = EnaDataSource.get_to_many_relations(
            mock_ds,
            mock_object,
            'runs'
        )

        mock_ds.get_list.assert_called_once()
        args, kwargs = mock_ds.get_list.call_args
        assert args == ('read_run',)
        assert kwargs['object_filters'].and_ == {
            'experiment_accession': {'eq': {'value': '"123"'}}
        }
        assert observed is mock_ds.get_list.return_value

    def test_get_to_many_relations_sample_experiments(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='sample', id='123')

        observed = EnaDataSource.get_to_many_relations(
            mock_ds,
            mock_object,
            'experiments'
        )

        mock_ds.get_list.assert_called_once()
        args, kwargs = mock_ds.get_list.call_args
        assert args == ('read_experiment',)
        assert kwargs['object_filters'].and_ == {
            'sample_accession': {'eq': {'value': '"123"'}}
        }
        assert observed is mock_ds.get_list.return_value

    def test_get_to_many_relations_study_experiments(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='study', id='123')

        observed = EnaDataSource.get_to_many_relations(
            mock_ds,
            mock_object,
            'experiments'
        )

        mock_ds.get_list.assert_called_once()
        args, kwargs = mock_ds.get_list.call_args
        assert args == ('read_experiment',)
        assert kwargs['object_filters'].and_ == {
            'study_accession': {'eq': {'value': '"123"'}}
        }
        assert observed is mock_ds.get_list.return_value

    def test_unsupported_relations_read_run(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='read_run')

        assert EnaDataSource.get_to_one_relation(mock_ds, mock_object, 'unknown') is None
        assert EnaDataSource.get_to_many_relations(mock_ds, mock_object, 'unknown') == []
        mock_ds.get_one.assert_not_called()
        mock_ds.get_list.assert_not_called()

    def test_unsupported_relations_study(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='study')

        assert EnaDataSource.get_to_one_relation(mock_ds, mock_object, 'sample') is None
        assert EnaDataSource.get_to_many_relations(mock_ds, mock_object, 'sample') == []
        mock_ds.get_one.assert_not_called()
        mock_ds.get_list.assert_not_called()

    def test_unsupported_relations_analysis(self):
        mock_ds = create_autospec(EnaDataSource)
        mock_object = Mock(type='analysis')

        assert EnaDataSource.get_to_one_relation(mock_ds, mock_object, 'experiment') is None
        assert EnaDataSource.get_to_many_relations(mock_ds, mock_object, 'experiment') == []
        mock_ds.get_one.assert_not_called()
        mock_ds.get_list.assert_not_called()

    def test_numeric_taxon_accession(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        ds.get_one = Mock()
        source = Mock(type='sample', tax_id=9606)

        assert ds.get_to_one_relation(source, 'taxon') is ds.get_one.return_value
        ds.get_one.assert_called_once_with('taxon', '9606')

    def test_missing_accession_attribute(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        ds.get_one = Mock()
        source = Mock(spec=['type'], type='read_run')

        assert ds.get_to_one_relation(source, 'experiment') is None
        ds.get_one.assert_not_called()

    def test_assembly_no_run_references(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        factory = core_data_object(ds)
        source = factory('assembly', id_='GCA_922984935.2', attributes={
            'run_accession': None,
        })
        ds.get_by_id = Mock()

        assert list(source.runs) == []
        ds.get_by_id.assert_not_called()

    def test_assembly_empty_run_references(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        factory = core_data_object(ds)
        source = factory('assembly', id_='GCA_922984935.2', attributes={
            'run_accession': '',
        })
        ds.get_by_id = Mock()

        assert list(source.runs) == []
        ds.get_by_id.assert_not_called()

    def test_assembly_blank_run_references(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        factory = core_data_object(ds)
        source = factory('assembly', id_='GCA_922984935.2', attributes={
            'run_accession': ' ; ; ',
        })
        ds.get_by_id = Mock()

        assert list(source.runs) == []
        ds.get_by_id.assert_not_called()

    def test_assembly_missing_run_attribute(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        factory = core_data_object(ds)
        source = factory('assembly', id_='GCA_922984935.2')
        ds.get_by_id = Mock()

        assert list(source.runs) == []
        ds.get_by_id.assert_not_called()

    def test_assembly_runs_batched_and_unique(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        factory = core_data_object(ds)
        run_ids = [f'ERR{i}' for i in range(ds.page_size + 1)]
        runs = [factory('read_run', id_=id_) for id_ in run_ids]
        source = factory('assembly', id_='GCA_922984935.2', attributes={
            'run_accession': ';'.join(run_ids + [run_ids[0], ' ', '']),
        })
        ds.get_by_id = Mock(side_effect=[runs[:-1], runs[-1:]])

        observed = list(source.runs)

        assert [obj.type for obj in observed] == ['read_run'] * len(run_ids)
        assert [obj.id for obj in observed] == run_ids
        assert ds.get_by_id.call_count == 2
        assert ds.get_by_id.call_args_list[0].args == ('read_run', run_ids[:-1])
        assert ds.get_by_id.call_args_list[1].args == ('read_run', run_ids[-1:])
        assert ds.relationship_config['assembly'].to_many == {'runs': 'read_run'}

    def test_assembly_runs_skip_unavailable_records(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        factory = core_data_object(ds)
        source = factory('assembly', id_='GCA_922984935.2', attributes={
            'run_accession': 'ERR123;ERR456',
        })
        run = factory('read_run', id_='ERR123')
        ds.get_by_id = Mock(return_value=[run, None])

        assert list(source.runs) == [run]
        ds.get_by_id.assert_called_once_with('read_run', ['ERR123', 'ERR456'])

    def test_assembly_missing_study_reference(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        factory = core_data_object(ds)
        source = factory('assembly', id_='GCA_922984935.2')
        ds.get_one = Mock()

        assert source.study is None
        ds.get_one.assert_not_called()

    def test_assembly_missing_sample_reference(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        factory = core_data_object(ds)
        source = factory('assembly', id_='GCA_922984935.2')
        ds.get_one = Mock()

        assert source.sample is None
        ds.get_one.assert_not_called()

    def test_assembly_missing_taxon_reference(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        factory = core_data_object(ds)
        source = factory('assembly', id_='GCA_922984935.2')
        ds.get_one = Mock()

        assert source.taxon is None
        ds.get_one.assert_not_called()

    def test_assembly_runs_preserve_http_errors(self):
        ds = EnaDataSource(lambda: None, lambda: None, None)
        factory = core_data_object(ds)
        source = factory('assembly', id_='GCA_922984935.2', attributes={
            'run_accession': 'ERR123',
        })
        ds.get_by_id = Mock(side_effect=HTTPError('ENA server error'))

        with pytest.raises(HTTPError, match='ENA server error'):
            list(source.runs)
