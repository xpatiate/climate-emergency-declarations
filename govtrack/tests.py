from django.test import TestCase
from django.urls import reverse

from govtrack.models import Country, Structure, Area, Declaration

class StructureTests(TestCase):

    fixtures = ['testdata']

    def setUp(self):
        self.country = Country.objects.get(pk=1)
        self.structure_national = Structure.objects.get(pk=1)

    def test_has_country(self):
        self.assertEqual(self.country.name, 'Erewhon')

    def test_has_structure(self):
        self.assertEqual(self.structure_national.name, 'National Government')

class AreaTests(TestCase):

    fixtures = ['testdata']

    def setUp(self):
        self.country = Country.objects.get(pk=1)
        self.structure_local = Structure.objects.get(pk=3)
        self.structure_neighbourhood = Structure.objects.get(pk=4)
        self.area_national = Area.objects.get(pk=1)
        self.area_north = Area.objects.get(pk=2)
        self.area_south = Area.objects.get(pk=3)
        self.area_southeast = Area.objects.get(pk=4)
        self.area_northwest = Area.objects.get(pk=5)

    def test_has_area(self):
        self.assertEqual(self.area_national.name, 'Erewhon')

    def test_level_descendants(self):
        self.assertEqual(self.area_national.height, 2)
        self.assertEqual(self.area_north.height, 1)
        self.assertEqual(self.area_northwest.height, 0)

        parkside = Area.objects.create(
            name='Parkside Council',
            parent=self.area_northwest,
            country=self.country,
            structure=self.structure_neighbourhood
        )

        # After adding a new child, the number of descendant levels
        # should have gone up by 1
        self.assertEqual(self.area_national.height, 3)
        self.assertEqual(self.area_north.height, 2)
        self.assertEqual(self.area_northwest.height, 1)

        northeast = Area.objects.create(
            name='North-East Locality',
            country=self.country,
            structure=self.structure_local,
            parent=self.area_north
        )
        northnortheast = Area.objects.create(
            name='North-North-East Locality',
            country=self.country,
            structure=self.structure_local,
            parent=self.area_north
        )
        
        # After adding more siblings, height should not change
        self.assertEqual(self.area_national.height, 3)
        self.assertEqual(self.area_north.height, 2)
        self.assertEqual(self.area_northwest.height, 1)
        self.assertEqual(northeast.height, 0)

    def test_area_properties(self):
        self.assertEqual(self.area_national.num_children, 2)

    def test_adjacency_list(self):
        as_bfs = self.area_national.bfs()

    def test_kids_by_level(self):
        area_national = Area.objects.get(pk=1)
        by_level = area_national.get_children_by_level()
        self.assertEqual(len(by_level['1']), 1)
        self.assertEqual(len(by_level['2']), 2)
        self.assertEqual(len(by_level['3']), 2)

    def test_tree_integrity(self):
        tree_ok = self.area_national.check_tree_integrity()
        self.assertIs(tree_ok, True)

class DeclarationTests(TestCase):

    fixtures = ['testdata']

    def setUp(self):
        pass

    def test_declaration_changed(self):
        dec = Declaration.objects.get(pk=1)
        self.assertIs(dec.area.country.is_popcount_needed, False)
        dec.event_date = '2020-01-15'
        dec.save()
        self.assertIs(dec.area.country.is_popcount_needed, True)

    def test_delete_declaration(self):
        dec = Declaration.objects.get(pk=1)
        dec.delete()
        try:
            dec2 = Declaration.objects.get(pk=1)
        except:
            dec2 = None
        self.assertIs(dec2, None)

    def test_delete_declared_area(self):
        area_nw = Area.objects.get(pk=5)
        area_nw.delete()
        try:
            nw = Area.objects.get(pk=5)
        except:
            nw = None
        self.assertIs(nw, None)
