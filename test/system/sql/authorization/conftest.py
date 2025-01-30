# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pytest import fixture

from tol.core.operator import OperatorMethod
from tol.sql.session import SessionFactory
from tol.sql.auth.blueprint import DbAuthBlueprint


@fixture(autouse=True)
def test_data(
    auth_bp: DbAuthBlueprint,
    session_factory: SessionFactory,
) -> None:

    auth_models = auth_bp.models

    with session_factory() as session:
        super_admin_role = auth_models.role_class(name='super_admin', system_access=True)
        user_role = auth_models.role_class(name='regular', system_access=False)
        session.add_all([super_admin_role, user_role])
        session.flush()

        super_admin_user = auth_models.user_class(id=1, username='super_admin', changed_lol='super_admin')
        regular_user = auth_models.user_class(id=100, username='regular', changed_lol='regular')
        session.add_all([super_admin_user, regular_user])
        session.flush()

        admin_token = auth_models.token_class(token='super_admin', user_id=1)
        regular_token = auth_models.token_class(token='regular', user_id=100)
        session.add_all([admin_token, regular_token])
        session.flush()

        root_membership = auth_models.membership(id=200, name='Root auth_models.membership')
        child_membership = auth_models.membership(id=201, name='Child auth_models.membership', parent=root_membership)
        session.add_all([root_membership, child_membership])
        session.flush()

        admin_membership = auth_models.user_membership(user=super_admin_user, membership=root_membership, role=super_admin_role)
        user_membership = auth_models.user_membership(user=regular_user, membership=child_membership, role=user_role)
        session.add_all([admin_membership, user_membership])
        session.flush()

        source = auth_models.source(name='Main Source')
        data_type = auth_models.data_object_type(name='sample', source=source)
        session.add_all([source, data_type])
        session.flush()

        attribute1 = auth_models.data_object_type_attribute(name='project_id', data_object_type=data_type, system=True)
        attribute2 = auth_models.data_object_type_attribute(name='biosample_id', data_object_type=data_type, system=False)
        session.add_all([attribute1, attribute2])
        session.flush()

        membership_data_object = auth_models.membership_data_object_type(membership=root_membership, data_object_type=data_type)
        session.add(membership_data_object)
        session.flush()

        allowed_attr = auth_models.membership_data_object_type_allowed_attribute(
            membership_data_object_type=membership_data_object, data_object_type_attribute=attribute1
        )
        session.add(allowed_attr)
        session.flush()

        detail_read_method = auth_models.method(
            identifier=str(OperatorMethod.DETAIL)
        )
        detail_delete_method = auth_models.method(
            identifier=str(OperatorMethod.DELETE)
        )
        session.add_all([detail_read_method, detail_delete_method])
        session.flush()
        
        need = auth_models.need(data_object_type=data_type)
        session.add(need)
        session.flush()

        need_method_detail_admin = auth_models.need_method(need=need, method=detail_read_method, role=super_admin_role)
        need_method_delete_admin = auth_models.need_method(need=need, method=detail_delete_method, role=super_admin_role)
        session.add_all([need_method_detail_admin, need_method_delete_admin])

        # tree hierarchy tests
        root = auth_models.membership(id=1, name="Sanger Institute")
        session.add(root)

        # Depth 2
        genomics = auth_models.membership(id=2, name="Genomics", parent_id=root.id)
        informatics = auth_models.membership(id=3, name="Informatics", parent_id=root.id)
        session.add(genomics)
        session.add(informatics)

        # Depth 3 (Genomics Division has two sub-divisions)
        genomics_research = auth_models.membership(id=4, name="Genomics Research", parent_id=genomics.id)
        genomics_services = auth_models.membership(id=5, name="Genomics Services", parent_id=genomics.id)
        session.add(genomics_research)
        session.add(genomics_services)

        # Informatics Division has only one sub-division
        informatics_research = auth_models.membership(id=6, name="Informatics Research", parent_id=informatics.id)
        session.add(informatics_research)

        # Depth 4 (Genomics Research further has some more divisions)
        genomics_research_bioinformatics = auth_models.membership(id=7, name="Bioinformatics", parent_id=genomics_research.id)
        genomics_research_analysis = auth_models.membership(id=8, name="Genomic Analysis", parent_id=genomics_research.id)
        session.add(genomics_research_bioinformatics)
        session.add(genomics_research_analysis)

        session.commit()
