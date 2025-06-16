# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class GoatTaxonToElasticSpeciesConverter(
        DataObjectToDataObjectOrUpdateConverter):
    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object is not None and data_object.id is not None:
            # Is the ID an integer?
            try:
                int(data_object.id)
            except ValueError:
                return iter([])
            ret = self._data_object_factory(
                'species',
                data_object.id,
                attributes={
                    **data_object.attributes
                }
            )
            for rank in data_object._host.get_ranks():
                rank_object = getattr(data_object, rank)
                if rank_object is not None:
                    setattr(ret, f'{rank}_name', rank_object.scientific_name)
            yield ret
        return iter([])
