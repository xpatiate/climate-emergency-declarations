from django.test import TestCase
from django.urls import reverse

from govtrack.models import Country, Structure, Area

class StructureTests(TestCase):

    fixtures = ['testdata']

    def setUp(self):
        self.country = Country.objects.get(pk=1)
        self.structure_national = Structure.objects.get(pk=1)
        self.structure_neighbourhood = Structure.objects.get(pk=4)
        self.area_national = Area.objects.get(pk=1)
        self.area_north = Area.objects.get(pk=2)
        self.area_south = Area.objects.get(pk=3)
        self.area_southeast = Area.objects.get(pk=4)
        self.area_northwest = Area.objects.get(pk=5)

    def test_has_country(self):
        assert self.country.name == 'Erewhon'

    def test_has_structure(self):
        assert self.structure_national.name == 'National Government'

    def test_has_area(self):
        assert self.area_national.name == 'Erewhon'

    def test_level_descendants(self):
        assert self.area_national.num_level_descendants == 2
        assert self.area_north.num_level_descendants == 1
        assert self.area_northwest.num_level_descendants == 0

        parkside = Area.objects.create(
            name='Parkside Council',
            parent=self.area_northwest,
            country=self.country,
            structure=self.structure_neighbourhood
        )

        assert self.area_national.num_level_descendants == 3
        assert self.area_north.num_level_descendants == 2
        assert self.area_northwest.num_level_descendants == 1
