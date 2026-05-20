# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable
from itertools import tee
from time import sleep
from typing import Any

from more_itertools import side_effect

from .converters import (
    BenchlingEntityToBenchlingWorklistItemConverterFactory,
    ElasticObjectToPortaldbObjectConverter,
    ElasticSampleToBenchlingTissueConverter,
)
from ..core import (
    ChainedConverter,
    DataObject,
    DataSource,
    DataSourceFilter,
    DefaultDataObjectToDataObjectConverter,
    IdsDataLoader,
    ObjectsDataLoader,
)
from ..elastic.elastic_utils import ElasticUtils


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

    @classmethod
    def sync_summarise_enrich(
        cls,
        eds: DataSource,
        portaldb_ds: DataSource,
        event_objects: Iterable[DataObject],
        object_type: str,
        data_source_instance: DataObject,
        sleep_time: int = 15
    ) -> None:
        """
            Sync the given events to the portal, then do a best attempt at
            summarising and enriching the related objects in the portal.
        """
        generators_object = tee(event_objects, 3)
        cls.sync_events_to_portal(
            eds=eds,
            portaldb_ds=portaldb_ds,
            objects=generators_object[0],
            object_type=object_type,
        )
        sleep(sleep_time)

        changes = ElasticUtils.summarise_objects(
            eds=eds,
            portaldb_ds=portaldb_ds,
            object_type=object_type,
            ids=[obj.id for obj in generators_object[1]],
            data_source_instance=data_source_instance
        )
        sleep(sleep_time)
        # We do another enrich step here to enrich any of the summarised fields that
        # might have been added in the summarisation step
        for dest_type, rel_ids in changes.items():
            if rel_ids:
                ElasticUtils.enrich_objects(eds=eds, object_type=dest_type, ids=rel_ids)

        ElasticUtils.enrich_objects(
            eds=eds,
            object_type=object_type,
            ids=[obj.id for obj in generators_object[2]]
        )

    @classmethod
    def sync_events_to_portal(
        cls,
        eds: DataSource,
        portaldb_ds: DataSource,
        objects: Iterable[DataObject],
        object_type: str
    ) -> None:
        """
            Sync the given event objects from portaldb to the portal
        """
        try:
            loader = ObjectsDataLoader(
                source=portaldb_ds,
                destination=eds,
                audit=None,
                source_object_type=f'{object_type}_event',
                destination_object_type=object_type,
                dependencies=[],
                convert_class=DefaultDataObjectToDataObjectConverter,
                loader_name='',
                objects=objects
            )

            loader.load(
                provenance='portaldb'
            )

        except Exception as e:
            print(f'Error loading samples: {e}')
            return []

    @classmethod
    def record_events(
        cls,
        eds: DataSource,
        portaldb_ds: DataSource,
        ids: list[str],
        source_object_type: str,
        destination_object_type: str,
        fields: dict[str, Any],
        id_field: str | None = None,
        incremental: bool = False,
    ) -> Any:
        """
            Helper for recording events in the portaldb, with error handling and logging.
            This is used to record events for samples, extractions and
            extraction containers, but can be used for any object type.
        """
        try:
            config_kwargs = {
                'destination_object_type': destination_object_type,
                'fields': fields,
                'incremental': incremental,
            }
            if id_field is not None:
                config_kwargs['id_field'] = id_field

            loader = IdsDataLoader(
                source=eds,
                destination=portaldb_ds,
                audit=None,
                source_object_type=source_object_type,
                destination_object_type=destination_object_type,
                dependencies=[],
                converter=ElasticObjectToPortaldbObjectConverter(
                    data_object_factory=portaldb_ds.data_object_factory,
                    config=ElasticObjectToPortaldbObjectConverter.Config(**config_kwargs)
                ),
                loader_name='',
                object_ids=ids
            )
            return side_effect(
                lambda obj: print(f'Adding {source_object_type} to Portaldb: {obj}', flush=True),
                loader.load(auto_exhaust=False)
            )
        except Exception as e:
            print(f'Error recording {source_object_type} events: {e}')
            return []

    @classmethod
    def create_sts_to_benchling_worklist_converter_factory(
        cls,
        object_type: str,
        worklist: DataObject
    ):
        object_type_mapping = {
            'sample': 'tissue',
            'extraction': 'dna_extract',
            'extraction_container': 'tube'
        }

        def factory(data_object_factory=None):
            destination_object_type = object_type_mapping.get(object_type, object_type)
            converters = []
            # Can put the object directly on to the worklist
            if worklist.worklist_type == 'bioentity' or object_type == 'extraction_container':
                converters.append(
                    ElasticSampleToBenchlingTissueConverter(
                        data_object_factory,
                        config=ElasticSampleToBenchlingTissueConverter.Config()
                    )
                    if object_type == 'sample'
                    else DefaultDataObjectToDataObjectConverter(
                        data_object_factory,
                        config=DefaultDataObjectToDataObjectConverter.Config(
                            destination_object_type=destination_object_type
                        )
                    )
                )
            # Need to convert to a container first
            elif worklist.worklist_type == 'container':
                converters.append(
                    DefaultDataObjectToDataObjectConverter(
                        data_object_factory,
                        config=DefaultDataObjectToDataObjectConverter.Config(
                            destination_object_type='tube',
                            id_field='benchling_fluidx_container_id'
                        )
                    )
                )
            converter_class = BenchlingEntityToBenchlingWorklistItemConverterFactory(worklist) \
                .get_converter_class()
            converters.append(
                converter_class(data_object_factory, config=converter_class.Config())
            )
            return ChainedConverter(*converters)
        return factory
