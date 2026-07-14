# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
from collections.abc import Iterable
from itertools import tee
from time import sleep
from typing import Any

from more_itertools import side_effect

from .converters import (
    BenchlingTissueToStsSampleConverter,
    ElasticObjectToBenchlingWorklistItemConverter,
    ElasticObjectToPortaldbObjectConverter,
    ElasticSampleToBenchlingTissueConverter,
    ErrorObjectConverter,
    StsSampleProjectToElasticSampleConverter,
)
from ..benchling.benchling_datasource import BenchlingDataSource
from ..core import (
    DataObject,
    DataSource,
    DataSourceFilter,
    DefaultDataLoader,
    DefaultDataObjectToDataObjectConverter,
    ErrorObject,
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

    @staticmethod
    def _tolid_id_field(object_type: str) -> str:
        return {'tolid': 'id', 'sample': 'sts_tolid.id'}.get(object_type, 'benchling_tolid.id')

    @classmethod
    def record_tolid_events(
        cls,
        eds: DataSource,
        portaldb_ds: DataSource,
        ids: list[str],
        object_type: str,
        user_id: str,
    ) -> Any:
        print('Recording tolid events', flush=True)
        return cls.record_events(
            eds=eds, portaldb_ds=portaldb_ds, ids=ids,
            source_object_type=object_type,
            destination_object_type='tolid_event',
            fields={'date_topup_actioned': datetime.datetime.now(), 'topup_actioned_by': user_id},
            id_field=cls._tolid_id_field(object_type),
            incremental=True,
        )

    @classmethod
    def record_actioned_events(
        cls,
        eds: DataSource,
        portaldb_ds: DataSource,
        ids: list[str],
        object_type: str,
        user_id: str,
    ) -> Any:
        print('Updating actioned events in Elastic', flush=True)
        return cls.record_events(
            eds=eds, portaldb_ds=portaldb_ds, ids=ids,
            source_object_type=object_type,
            destination_object_type=f'{object_type}_event',
            fields={'date_topup_actioned': datetime.datetime.now(), 'topup_actioned_by': user_id},
        )

    @classmethod
    def record_abandoned_events(
        cls,
        eds: DataSource,
        portaldb_ds: DataSource,
        ids: list[str],
        object_type: str,
        user_id: str,
    ) -> Any:
        print('Updating abandoned events in Elastic', flush=True)
        return cls.record_events(
            eds=eds, portaldb_ds=portaldb_ds, ids=ids,
            source_object_type=object_type,
            destination_object_type=f'{object_type}_event',
            fields={
                'date_abandoned': datetime.datetime.now(),
                'abandoned_by': user_id,
                'date_topup_actioned': None
            },
        )

    @classmethod
    def record_review_events(
        cls,
        eds: DataSource,
        portaldb_ds: DataSource,
        ids: list[str],
        object_type: str,
        user_id: str,
        in_review: bool = True,
    ) -> Any:
        print('Updating review events in Elastic', flush=True)
        fields = (
            {
                'date_sent_to_review': datetime.datetime.now(),
                'sent_to_review_by': user_id,
                'in_review': True,
            }
            if in_review
            else {'in_review': False}
        )
        return cls.record_events(
            eds=eds, portaldb_ds=portaldb_ds, ids=ids,
            source_object_type=object_type,
            destination_object_type='tolid_event',
            fields=fields,
            id_field=cls._tolid_id_field(object_type),
        )

    @classmethod
    def record_species_events(
        cls,
        eds: DataSource,
        portaldb_ds: DataSource,
        ids: list[str],
        user_id: str,
        recollection_reason: str = None,
    ) -> Any:
        print('Recording species events', flush=True)
        return cls.record_events(
            eds=eds, portaldb_ds=portaldb_ds, ids=ids,
            source_object_type='species',
            destination_object_type='species_event',
            fields={
                'date_marked_for_recollection': datetime.datetime.now(),
                'marked_for_recollection_by': user_id,
                'marked_for_recollection_reason': recollection_reason,
            },
            id_field='id',
        )

    @classmethod
    def sync_samples_to_portal_by_ids(
            cls,
            eds: DataSource,
            ids: list[str],
            sts_ds: DataSource,
            portaldb_ds: DataSource
    ) -> None:
        """
            Takes a list of sample IDs, finds the associated sample_projects in STS,
            converts them to elastic samples and loads them.
        """
        try:
            f = DataSourceFilter()
            f.and_ = {'sample.id': {'in_list': {'value': ids}}}
            # Here we need to get the requested fields from a loader to avoid hardcoding them
            # here if they change
            loader_data_object = portaldb_ds.get_one('loader', 14)
            loader = DefaultDataLoader(
                source=sts_ds,
                destination=eds,
                audit=None,
                source_object_type='sample_project',
                destination_object_type='sample',
                dependencies=[],
                object_filters=f,
                convert_class=StsSampleProjectToElasticSampleConverter,
                requested_fields=loader_data_object.requested_fields,
                loader_name='STS samples and projects'
            )

            loader.load(provenance='sts')

        except Exception as e:
            print(f'Error updating samples: {e}')
            return []

    @classmethod
    def create_benchling_entities_from_elastic_samples(
        cls,
        ids: list[str],
        eds: DataSource,
        bds: BenchlingDataSource,
        sts_ds: DataSource,
        additional_fields: dict[str, Any] = {}
    ):
        """
        Use a list of sample IDs to load samples from the portal and
        create corresponding entities in Benchling, then update the samples
        in STS with the new Benchling IDs.
        """
        loader = IdsDataLoader(
            source=eds,
            destination=bds,
            audit=None,
            source_object_type='sample',
            destination_object_type='tissue',
            dependencies=[],
            converter=ElasticSampleToBenchlingTissueConverter(
                data_object_factory=bds.data_object_factory,
                config=ElasticSampleToBenchlingTissueConverter.Config(
                    extra_attributes=additional_fields
                )
            ),
            loader_name='Benchling Tissue Inserts',
            object_ids=ids
        )

        returned_objects = side_effect(
            lambda obj: print(f'Created Benchling entity: {obj}', flush=True),
            loader.load(
                method='insert',
                auto_exhaust=False
            )
        )

        # Update samples in STS with Benchling IDs
        loader2 = ObjectsDataLoader(
            source=None,
            destination=sts_ds,
            audit=None,
            source_object_type='tissue',
            destination_object_type='sample',
            dependencies=[],
            convert_class=BenchlingTissueToStsSampleConverter,
            loader_name='STS Sample Update',
            objects=returned_objects
        )

        returned_objects2 = side_effect(
            lambda obj: print(f'STS Sample Updated: {obj}', flush=True),
            loader2.load(auto_exhaust=False)
        )

        return returned_objects2

    @classmethod
    def load_entities_onto_worklist(
        cls,
        eds: DataSource,
        bds: DataSource,
        ids: list[str],
        object_type: str | None,
        worklist: DataObject
    ) -> Iterable[DataObject | ErrorObject]:
        print('Loading entities onto worklist', flush=True)
        try:
            loader = IdsDataLoader(
                source=eds,
                destination=bds,
                audit=None,
                source_object_type=object_type,
                destination_object_type='worklist_item',
                dependencies=[],
                converter=ElasticObjectToBenchlingWorklistItemConverter(
                    data_object_factory=bds.data_object_factory,
                    config=ElasticObjectToBenchlingWorklistItemConverter.Config(
                        object_type=object_type, worklist=worklist
                    )
                ),
                loader_name=f'Elastic {object_type} to Benchling Worklist Item',
                object_ids=ids
            )

            returned_objects = side_effect(
                lambda obj: print(f'Adding {object_type} to Worklist: {obj}', flush=True),
                loader.load(
                    method='insert',
                    auto_exhaust=False
                )
            )
            return returned_objects

        except Exception as e:
            print(f'Error loading samples: {e}')
            return []

    @classmethod
    def perform_topup_action(
        cls,
        eds: DataSource,
        bds: BenchlingDataSource,
        ids: list[str],
        sts_ds: Any,
        portaldb_ds: DataSource,
        data_source_instance: DataObject,
        object_type: str | None,
        worklist: DataObject,
        action: str,
        user_id: str,
        user_name: str,
        recollection_reason: str = None,
        sleep_time: int = 15
    ) -> Iterable[ErrorObject]:
        """
            Performs the requested topup action.
            Returns an iterable of error objects for any entities that failed
            at some point
        """
        if not ids:
            return []

        error_filter = ErrorObjectConverter(
            None,  # We are just passing through, not creating new objects
            config=ErrorObjectConverter.Config(include=True)
        )

        if object_type == 'sample':
            additional_fields = {'assigned_by': user_name}
            yield from error_filter.convert_iterable(
                cls.create_benchling_entities_from_elastic_samples(
                    ids=ids, eds=eds, bds=bds, sts_ds=sts_ds, additional_fields=additional_fields
                )
            )
            cls.sync_samples_to_portal_by_ids(
                eds=eds, ids=ids, sts_ds=sts_ds, portaldb_ds=portaldb_ds
            )
            sleep(sleep_time)

        if worklist is not None:
            yield from error_filter.convert_iterable(
                cls.load_entities_onto_worklist(
                    eds=eds, bds=bds, ids=ids, object_type=object_type, worklist=worklist
                )
            )

        if action == 'tum':
            tolid_events = cls.record_tolid_events(
                eds=eds, portaldb_ds=portaldb_ds, ids=ids, object_type=object_type, user_id=user_id
            )
            yield from error_filter.convert_iterable(tolid_events)
            object_events = cls.record_actioned_events(
                eds=eds, portaldb_ds=portaldb_ds, ids=ids, object_type=object_type, user_id=user_id
            )
            yield from error_filter.convert_iterable(object_events)

            cls.sync_summarise_enrich(
                eds=eds,
                portaldb_ds=portaldb_ds,
                event_objects=tolid_events,
                object_type='tolid',
                data_source_instance=data_source_instance
            )
            cls.sync_summarise_enrich(
                eds=eds,
                portaldb_ds=portaldb_ds,
                event_objects=object_events,
                object_type=object_type,
                data_source_instance=data_source_instance
            )

        elif action in ('in_ara_review', 'out_of_ara_review'):
            review_events = cls.record_review_events(
                eds=eds,
                portaldb_ds=portaldb_ds,
                ids=ids,
                object_type=object_type,
                user_id=user_id,
                in_review=(action == 'in_ara_review')
            )
            yield from error_filter.convert_iterable(review_events)
            cls.sync_summarise_enrich(
                eds=eds,
                portaldb_ds=portaldb_ds,
                event_objects=review_events,
                object_type=object_type,
                data_source_instance=data_source_instance
            )

        elif action == 'abandon':
            object_events = cls.record_abandoned_events(
                eds=eds, portaldb_ds=portaldb_ds, ids=ids, object_type=object_type, user_id=user_id
            )
            yield from error_filter.convert_iterable(object_events)
            cls.sync_summarise_enrich(
                eds=eds,
                portaldb_ds=portaldb_ds,
                event_objects=object_events,
                object_type=object_type,
                data_source_instance=data_source_instance
            )

        elif action == 'recollect':
            species_events = cls.record_species_events(
                eds=eds, portaldb_ds=portaldb_ds, ids=ids, user_id=user_id,
                recollection_reason=recollection_reason
            )
            yield from error_filter.convert_iterable(species_events)
            cls.sync_summarise_enrich(
                eds=eds,
                portaldb_ds=portaldb_ds,
                event_objects=species_events,
                object_type='species',
                data_source_instance=data_source_instance
            )
