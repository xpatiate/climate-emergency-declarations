from django.test import TestCase
from django.urls import reverse

from govtrack.models import Country


class GovtrackTests(TestCase):
    def setUp(self):
        Country.objects.create(
            name="Utopia", region="Erewhon", population=123, country_code=666
        )

    def test_list_countries(self):
        response = self.client.get(reverse("countries"))
        self.assertEqual(response.status_code, 200)
        country_list = response.context["country_list"]
        self.assertEqual(len(country_list), 1)
        country = response.context["country_list"][0]
        self.assertEqual(country.id, 1)

    def test_view_country(self):
        c_url = reverse("country", args=[1])
        response = self.client.get(c_url)
        self.assertEqual(response.status_code, 200)
