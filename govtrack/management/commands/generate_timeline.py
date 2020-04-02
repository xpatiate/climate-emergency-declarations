from django.core.management.base import BaseCommand, CommandError
from govtrack.models import Country


class Command(BaseCommand):
    help = "Generates a population timeline for specified country"

    #    def add_arguments(self, parser):
    #        parser.add_argument('country_code', nargs='+', type=str)

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("About to generate population count for some country")
        )
        try:
            country_code = options.get("country_code", "VUT")
            country = Country.find_by_code(country_code)
            country.generate_population_count()
        except Country.DoesNotExist:
            raise CommandError('Country "%s" does not exist' % country_code)

        self.stdout.write(
            self.style.SUCCESS(
                'Generated population count for country "%s"' % country_code
            )
        )
