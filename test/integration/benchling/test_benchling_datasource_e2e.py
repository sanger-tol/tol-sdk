# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
import time
import uuid

from tol.benchling import BenchlingDataSource
from tol.core import DataObject, DataSourceFilter, ErrorObject
from tol.sources.benchling import benchling

from .utils import against_types


class TestBenchlingDataSourceE2E:
    """
    Tests `BenchlingDataSource` against a
    real Benchling instance.

    These functions operate only at the
    `DataSource` layer, using only
    standard `Operator` methods, and only confirm
    existence/non-existence.
    """
    _str_values = None

    can_update = ['tissue', 'tissue_prep']

    # @against_types([
    #     'tissue',
    #     'consumables_lot',
    #     'folder',
    #     'worklist',
    #     'storage',
    #     '12x12_box',
    #     'casm_well',
    #     'casm_programme_id'
    # ])
    # def test_get(self, object_type: str) -> None:
    #     """
    #     Gets a single object of specified type.
    #     """

    #     benchling_ds = benchling()
    #     str_key = self.__find_string_key(
    #         object_type,
    #         benchling_ds
    #     )
    #     # get an object list
    #     objs = benchling_ds.get_list(
    #         object_type
    #     )
    #     obj = next(objs)
    #     assert obj.type == object_type
    #     assert getattr(obj, str_key) is not None
    #     self.__assert_relations_filled(obj, benchling_ds)

    #     # now try getting one by ID
    #     obj2 = benchling_ds.get_one(
    #         object_type,
    #         obj.id
    #     )
    #     assert obj2.type == object_type
    #     self.__assert_relations_filled(obj2, benchling_ds)

    # We should add 'storage' to the list but the test user has insufficient privileges
    # to test location types
    @against_types(['tissue', 'tissue_prep', 'folder', 'casm_96_well_plate'])
    def test_many_insert_update_delete(self, object_type: str) -> None:
        """
        Inserts several `DataObject` instances of specified type,
        confirms they are present there, and updates, confirms
        changes.
        """

        benchling_ds = benchling()

        # get the key of a `str` field
        str_key = self.__find_string_key(
            object_type,
            benchling_ds
        )

        # create the objects
        objs = [
            self.__create_test_object(
                object_type,
                benchling_ds,
                string_value=self.__populate_string_value(str_key, i, object_type),
                str_key=str_key
            )
            for i in range(1, 4)
        ]

        # insert them
        res = list(
            benchling_ds.insert(
                object_type,
                objs
            )
        )

        # there should be 3
        assert len(res) == 3

        # they all have the right value for `str_key`
        for i, obj in enumerate(res, start=1):
            str_val = getattr(obj, str_key)
            assert str_val == self.__get_string_value(object_type, str_key, i)

        # get their new ID's
        ids = [
            r.id for r in res
        ]
        expected_str_val = 'A'
        if object_type in self.can_update:
            expected_str_val = 'CBA'
            # update each `str` attribute
            benchling_ds.update(
                object_type,
                [
                    (
                        id_,
                        {
                            str_key: self.__populate_string_value(
                                str_key,
                                i,
                                object_type,
                                expected_str_val
                            )
                        }
                    )
                    for i, id_ in enumerate(ids, start=1)
                ]
            )

        # get them back
        new_objs = list(
            benchling_ds.get_by_id(
                object_type,
                ids
            )
        )

        # assert everything is right (and `str` key is updated if allowed)
        for i, (id_, new_obj) in enumerate(zip(ids, new_objs), start=1):
            assert new_obj.type == object_type
            assert new_obj.id == id_
            str_val = getattr(new_obj, str_key)
            assert str_val == self.__get_string_value(object_type, str_key, i, expected_str_val)
            # Assert that any required relations are filled
            self.__assert_relations_filled(new_obj, benchling_ds)

        benchling_ds.delete(object_type, [obj.id for obj in new_objs])

    @against_types([
        '12x12_box:casm_tube'
    ])
    def test_many_insert_delete_storage_layers(self, object_type: str) -> None:
        benchling_ds = benchling()
        first_object_type, second_object_type = object_type.split(':', 1)
        first_str_key = self.__find_string_key(first_object_type, benchling_ds)
        second_str_key = self.__find_string_key(second_object_type, benchling_ds)

        # ---- Create First Objects in Batch ----
        first_objs = [
            self.__create_test_object(
                first_object_type,
                benchling_ds,
                string_value=self.__populate_string_value(first_str_key, i, first_object_type),
                str_key=first_str_key
            )
            for i in range(1, 4)
        ]

        # Insert in a single batch call
        res = list(benchling_ds.insert(first_object_type, first_objs))
        assert len(res) == 3
        ids = [r.id for r in res]

        # Confirm inserted values in one loop
        for i, obj in enumerate(res, start=1):
            assert getattr(obj, first_str_key) == self.__get_string_value(
                first_object_type,
                first_str_key,
                i
            )

            # ---- Create Second Objects Using First Object IDs ----
            second_objs = [
                self.__create_test_object(
                    second_object_type,
                    benchling_ds,
                    string_value=self.__populate_string_value(
                        str_key=second_str_key,
                        counter=i,
                        object_type=second_object_type
                    ),
                    str_key=second_str_key,
                    parent_storage_id=f'{obj.id}:a{i}'
                )
                for i in range(1, 4)
            ]

            second_res = list(benchling_ds.insert(second_object_type, second_objs))
            assert len(second_res) == 3

            # Confirm inserted second objects
            for i2, obj2 in enumerate(second_res, start=1):
                assert getattr(obj2, second_str_key) == self.__get_string_value(
                    second_object_type,
                    second_str_key,
                    i2
                )
                assert obj2.parent_storage_id == f'{obj.id}:a{i2}'

            benchling_ds.delete(second_object_type, [obj.id for obj in second_res])

        # ---- Clean Up ----
        benchling_ds.delete(first_object_type, ids)

    @against_types(['tissue', 'folder'])
    def test_many_insert_update_delete_with_errors(self, object_type: str) -> None:
        """
        Inserts several `DataObject` instances of specified type,
        confirms they are present there, and updates, confirms
        changes.
        """

        benchling_ds = benchling()

        # get the key of a `str` field
        str_key = self.__find_string_key(
            object_type,
            benchling_ds
        )

        # create the objects
        objs = [
            self.__create_test_object(
                object_type,
                benchling_ds,
                string_value='A' * i,
                str_key=str_key
            )
            for i in range(1, 4)
        ]
        # Unset that string key to cause an error in one object
        objs[1].attributes[str_key] = None

        # insert them
        res = list(
            benchling_ds.insert(
                object_type,
                objs
            )
        )

        # there should be 3
        assert len(res) == 3
        assert isinstance(res[0], DataObject)
        assert isinstance(res[1], ErrorObject)
        assert res[1].object_ is objs[1]
        assert isinstance(res[2], DataObject)

        # Test the error message
        assert 'Invalid field value' in res[1].details \
            or 'must be of type string' in res[1].details

        # Update the first object with something invalid
        if object_type in self.can_update:
            res2 = list(benchling_ds.update(
                object_type,
                [
                    (
                        res[0].id,
                        {
                            str_key: None
                        }
                    )
                ]
            ))
            assert len(res2) == 1
            assert isinstance(res2[0], ErrorObject)

            # Get the object back
            new_obj = benchling_ds.get_one(
                object_type,
                res[0].id
            )
            # Assert that the string key has not been updated
            assert getattr(new_obj, str_key) == 'A'

        benchling_ds.delete(object_type, [res[0].id, res[2].id])

    @against_types(['tissue', 'tissue_prep'])
    def test_worklists(self, object_type: str) -> None:
        """
        Creates a worklist, adds a tissue to it, and then
        deletes the worklist.
        """

        benchling_ds = benchling()

        # create the worklist
        worklist_to_add = benchling_ds.data_object_factory(
            'worklist',
            None,
            attributes={
                'name': 'Test Worklist',
                'worklist_type': 'bioentity'
            }
        )
        # insert it
        worklists_added = list(
            benchling_ds.insert(
                'worklist',
                [worklist_to_add]
            )
        )
        worklist_added = worklists_added[0]
        # create the worklist items
        all_entities = benchling_ds.get_list(object_type)
        items_to_add = [
            next(all_entities)
            for _ in range(3)
        ]
        worklist_items = [
            benchling_ds.data_object_factory(
                'worklist_item',
                None,
                to_one={
                    'worklist': worklist_added,
                    'item': items_to_add[i]
                }
            )
            for i in range(3)
        ]
        # insert them
        res = list(
            benchling_ds.insert(
                'worklist_item',
                worklist_items
            )
        )
        # there should be 3
        assert len(res) == 3
        # We won't test the return values as Benchling doesn't return the worklist

        # Try listing the worklist items via the worklist
        worklist = benchling_ds.get_one('worklist', worklist_added.id)

        worklist_items = list(worklist.worklist_items)
        assert len(worklist_items) == 3
        assert worklist_items[0].item.id == items_to_add[0].id
        assert worklist_items[0].item.type == object_type
        assert worklist_items[1].item.id == items_to_add[1].id
        assert worklist_items[1].item.type == object_type
        assert worklist_items[2].item.id == items_to_add[2].id
        assert worklist_items[2].item.type == object_type

        # delete the worklist
        benchling_ds.delete('worklist', [worklist_added.id])

    @against_types(['tissue', 'tissue_prep'])
    def test_folders(self, object_type: str) -> None:
        """
        Creates a folder, adds a tissue to it, and then removes the tissue from it.
        """

        benchling_ds = benchling()

        folder = self.__get_example_object('folder')
        entity = self.__get_example_object(object_type)

        # Remove from folder
        updates = [
            (entity.id, {'folder': None})
        ]
        res = list(benchling_ds.update(object_type, updates))
        assert len(res) == 1

        refetched_entity = benchling_ds.get_one(object_type, entity.id)
        assert refetched_entity.folder is None

        # Add to a folder
        updates = [
            (entity.id, {'folder': folder})
        ]

        res = list(benchling_ds.update(object_type, updates))
        assert len(res) == 1

        refetched_entity = benchling_ds.get_one(object_type, entity.id)
        assert refetched_entity.folder is not None
        assert refetched_entity.folder.id == folder.id

    @against_types([
        'casm_programme_id',
        # 'casm_sample_status'
    ])
    def test_assay_results_casm(self, object_type: str) -> None:
        """
        Retrieves a custom entity and attaches an assay result to it and
        then removes the assay result
        """

        benchling_ds = benchling()
        custom_entity = self.__get_example_object('casm_sample')

        str_key = self.__find_string_key(
            object_type,
            benchling_ds
        )
        # create the objects
        objs = [
            self.__create_test_object(
                object_type,
                benchling_ds,
                string_value='A' * i,
                str_key=str_key
            )
            for i in range(1, 4)
        ]

        for obj in objs:
            obj.attributes['sample_id'] = custom_entity.id

        res = list(
            benchling_ds.insert(
                object_type,
                objs
            )
        )

        # there should be 3
        assert len(res) == 3

        # get their new ID's
        for r in res:
            assert r.type == 'assay_result'
            assert r.id is not None

        benchling_ds.delete(object_type, [obj.id for obj in res])

    def __get_example_object(self, object_type: str) -> DataObject:
        benchling_ds = benchling()
        f = DataSourceFilter()
        if object_type == 'folder':
            f.and_ = {'name': {'eq': {'value': 'Core Lab Entities'}}}
        if object_type == 'tissue':
            f.and_ = {'project': {'eq': {'value': 'DTOL'}}}
        if object_type == 'tissue_prep':
            # A specific tissue prep
            return benchling_ds.get_one('tissue_prep', 'bfi_ZNh4kTQZ')
        if object_type == 'location':
            # A specific storage location used for testing
            return benchling_ds.get_one('storage', 'loc_9rnbkEzo')
        objs = benchling_ds.get_list(object_type, object_filters=f)
        return next(objs)

    def __assert_relations_filled(
        self,
        obj: DataObject,
        benchling_ds: BenchlingDataSource
    ) -> None:
        if obj.type in benchling_ds.benchling_types:
            benchling_type = benchling_ds.benchling_types[obj.type]
            # Native relationships
            native_relations = self.__get_native_relations(benchling_type)
            # Schema relationships
            schema_relations = {}
            if benchling_type in benchling_ds.schemas \
                    and obj.type in benchling_ds.schemas[benchling_type]:
                for att, field_def in benchling_ds.schemas[benchling_type][obj.type].items():
                    if isinstance(field_def, dict) and field_def['required'] \
                            and field_def['benchling_type'] == 'entity_link':
                        schema_relations[att] = benchling_ds.schema_names[field_def['schema_id']]
            for att, type_ in (native_relations | schema_relations).items():
                related_object = getattr(obj, att)
                assert related_object is not None
                assert related_object.type == type_
                # Assert that the related object has a string key
                # (i.e. has been unstubbed)
                related_str_key = self.__find_string_key(
                    related_object.type,
                    benchling_ds
                )
                assert getattr(related_object, related_str_key) is not None

    def __get_native_relations(
        self,
        benchling_type: str
    ) -> list[str]:
        if benchling_type == 'custom_entity':
            return {'folder': 'folder'}
        return {}

    def __find_string_key(
        self,
        object_type: str,
        benchling_ds: BenchlingDataSource
    ) -> str:
        """This used to be automatic but it would return computed fields.
        For now, just hard code an appropriate string field"""
        if object_type in ['tissue']:
            return 'programme_id'
        if object_type == 'tissue_prep':
            return 'submission_id'
        if object_type == 'consumables_lot':
            return 'batch_lot_number'
        if object_type in ['folder', 'worklist', 'storage']:
            return 'name'
        if benchling_ds.benchling_types[object_type] in ['box', 'plate', 'container']:
            return 'barcode'
        if benchling_ds.benchling_types[object_type] == 'assay_result':
            return 'programme_id'
        if object_type == 'casm_sample':
            return 'programme_id_manual'

        # Else do it the way we did before
        attribute_types = benchling_ds.attribute_types[object_type]
        benchling_type = benchling_ds.benchling_types[object_type]
        for k, v in attribute_types.items():
            if benchling_ds.schemas[benchling_type][object_type][k]['benchling_type'] == 'text' \
                    and benchling_ds.schemas[benchling_type][object_type][k]['required']:
                return k

        raise Exception('no `str` key was found.')

    def __populate_string_value(
            self,
            str_key,
            counter,
            object_type: str,
            string_override: str = 'A'
    ):
        if self._str_values is None:
            self._str_values = {}

        if object_type not in self._str_values:
            self._str_values[object_type] = {}

        if str_key not in self._str_values[object_type]:
            self._str_values[object_type][str_key] = {}

        string_value = string_override * counter

        if 'barcode' == str_key:
            timestamp = int(time.time() * 1000)  # Current time in milliseconds
            unique_id = uuid.uuid4()
            string_value = f'{timestamp}-{unique_id}'

            self._str_values[object_type][str_key][counter] = string_value

        return string_value

    def __get_string_value(self, object_type: str, str_key, counter, string_override: str = 'A'):
        string_value = string_override * counter

        if 'barcode' == str_key:
            string_value = self._str_values[object_type][str_key][counter]

        return string_value

    def __create_test_object(
        self,
        object_type: str,
        benchling_ds: BenchlingDataSource,
        string_value: str = 'test',
        str_key: str = None,
        int_value: int = 1,
        float_value: float = 1.0,
        datetime_value: datetime.datetime = datetime.datetime(2021, 1, 1),
        parent_storage_id: str | None = None
    ) -> str:
        """Creates test data for an example object"""
        atts = {}
        to_ones = {}
        for att, att_type in benchling_ds.attribute_types[object_type].items():
            # Does this object have a schema?
            if object_type in benchling_ds.benchling_types \
                    and benchling_ds.benchling_types[object_type] in benchling_ds.schemas \
                    and object_type in benchling_ds.schemas[benchling_ds.benchling_types[object_type]]:  # noqa E501
                benchling_type = benchling_ds.benchling_types[object_type]
                defs = benchling_ds.schemas[benchling_type][object_type]
                if att in defs:
                    field_def = defs[att]
                    # Easy way to avoid computed fields
                    if not field_def['required']:
                        continue
                    if field_def['benchling_type'] == 'dropdown':
                        attribute_values = benchling_ds.get_attribute_value_options(
                            object_type,
                            att
                        )
                        atts[att] = next(iter(attribute_values.values()))
            if att not in atts:
                if att_type == 'str':
                    atts[att] = string_value
                if att_type == 'int':
                    atts[att] = int_value
                if att_type == 'float':
                    atts[att] = float_value
                if att_type == 'datetime':
                    atts[att] = datetime_value

        if (
            object_type in benchling_ds.relationship_config
            and benchling_ds.relationship_config[object_type].to_one is not None
        ):
            for rel, rel_type in benchling_ds.relationship_config[object_type].to_one.items():
                if isinstance(rel_type, list):
                    rel_type = rel_type[0]
                example_object = next(benchling_ds.get_list(rel_type))
                to_ones[rel] = example_object
        # Explicitly set the string key
        if str_key is not None:
            atts[str_key] = string_value

        # Explicitly set the parent_storage_id
        if parent_storage_id is not None:
            atts['parent_storage_id'] = parent_storage_id
        return benchling_ds.data_object_factory(
            object_type,
            None,
            attributes=atts,
            to_one=to_ones
        )
