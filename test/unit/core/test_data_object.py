# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject


class TestDataObject:
    def test_attributes(self):
        obj = DataObject('test')
        obj.test1 = 'nice'
        obj.test2 = 'also nice'
        obj.completely_random = 'yet still nicer'
        expected = {
            'test1': 'nice',
            'test2': 'also nice',
            'completely_random': 'yet still nicer'
        }
        assert obj.attributes == expected
        assert obj.to_one_relationships == {}
        assert obj.to_many_relationships == {}

    def test_to_one_relationships(self):
        greeting = DataObject('greeting')
        person = DataObject('human')
        person.saying = greeting
        expected = {
            'saying': greeting
        }
        assert person.attributes == {}
        assert person.to_one_relationships == expected
        assert person.to_many_relationships == {}

    def test_to_many_relationships(self):
        species = DataObject('species')
        specimens = [
            DataObject('specimen', {'id': i})
            for i in range(50)
        ]
        species.specimens = specimens
        expected = {
            'specimens': specimens
        }
        assert species.attributes == {}
        assert species.to_one_relationships == {}
        assert species.to_many_relationships == expected

    def test_all(self):
        specimen = DataObject('specimen', {'id': 'test'})
        specimen.biospecimen_id = 'I do not know what these look like'
        species = DataObject('species')
        specimen.species = species
        samples = [
            DataObject('sample', {'id': i}) for i in range(32)
        ]
        specimen.assigned_samples = samples
        assert specimen.attributes == {
            'id': 'test',
            'biospecimen_id': 'I do not know what these look like'
        }
        assert specimen.to_one_relationships == {
            'species': species
        }
        assert specimen.to_many_relationships == {
            'assigned_samples': samples
        }
