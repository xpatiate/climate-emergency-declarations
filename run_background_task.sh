from django.conf import settings
import ced_bg.settings as app_settings
import sys

settings.configure(
    INSTALLED_APPS=app_settings.INSTALLED_APPS,
    DATABASES=app_settings.DATABASES)

import django
django.setup()

from govtrack.models import Country

def handler(event, context):
    print("Called with event data " + str(event))
    task = event.get('task','')

    if task == 'generate-timeline':
        generate_timeline(event, context)

def generate_timeline(event, context):
    print("Called with event data " + str(event))
    try:
        print(f"Finding country {event['country_code']} from class {Country}={Country.content_type_id()}")
        country = Country.find_by_code(event['country_code'])
        print(f"got country {country}")
        country.generate_population_count()
        print(f"Finished generating population count for {event['country_code']}")
    except KeyError as ex:
        print(f"No country code specified: {ex}")
    except Country.DoesNotExist() as ex:
        print(f"No country found with code {event['country_code']} {ex}")
    print("All done")

if __name__ == '__main__':
    try:
        country_code = sys.argv[1] 
        print(country_code)
        generate_timeline({'country_code': country_code}, {})
        print("DOne generating timeline")
    except:
        pass
