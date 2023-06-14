# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, List

from ..core import CoreDataObject, DataObject


class SqlDataObject(CoreDataObject):
    """
    Implements the DataObject ABC, as the result of the conversion
    of a Model instance (i.e. Sqlalchemy Model).

    Will one day support lazy loading of relationships, but for now
    they are unsupported.
    """

    @property
    def to_one_relationships(self) -> Dict[str, DataObject]:
        raise NotImplementedError(
            'Relationships are unsupported on SqlDataSource for now.'
        )

    @property
    def to_many_relationships(self) -> Dict[str, List[DataObject]]:
        raise NotImplementedError(
            'Relationships are unsupported on SqlDataSource for now.'
        )
