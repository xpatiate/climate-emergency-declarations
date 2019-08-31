from django.shortcuts import get_object_or_404, render, redirect, Http404, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from govtrack.models import Declaration, Country, Area, Structure, Link, PopCount, ImportDeclaration
from govtrack.forms import AreaForm

from bs4 import BeautifulSoup
import csv
import datetime
import html
import io
import logging

logger = logging.getLogger('cegov')
DATE_FORMAT='%Y-%m-%d'

## PUBLIC METHODS ##

def area_data(request, area_id):
    area = get_object_or_404(Area, pk=area_id)
    decl = area.latest_declaration
    dec_date = ''
    bestlink = ''
    contact = ''
    if decl and decl.is_currently_active():
        dec_date = decl.display_event_date()
        contact = decl.key_contact
        # TODO: add a 'best link' field
        #links = decl.links.all()
        #if links:
        #    bestlink = links[0].url
    areadata = [
        area.name,
        1,
        area.location,
        area.population,
        dec_date,
        '', # empty col
        contact,
        bestlink, # key document/reference
        area.contribution()
    ]
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(areadata)
    return response

def country_population(request, country_code):
    country = Country.find_by_code(country_code)
    if not country:
        raise Http404("No country for specified code")
    return HttpResponse(str(country.current_popcount), content_type='text/plain')

def country_regenerate_timeline(request, country_code):
    status=403
    if request.user.is_authenticated:
        country = Country.find_by_code(country_code)
        if not country:
            raise Http404("No country for specified code")
        country.generate_population_count()
        return HttpResponse(str(country.current_popcount), content_type='text/plain')
    else:
        return HttpResponse(status=status)

def country_population_timeline(request, country_code):
    country = Country.find_by_code(country_code)
    if not country:
        raise Http404("No country for specified code")
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    for pc in country.popcounts:
        area = pc.declaration.area
        writer.writerow([pc.declaration.event_date, country.name, area.name, area.population, pc.status, pc.population])
    return response

# unused
def country_declarations(request, country_code):
    country = Country.find_by_code(country_code)
    if not country:
        raise Http404("No country for specified code")
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(['Area', 'Location', 'Population', 'Date Declared', 'Declared Ancestors'])
    query_args = {
        'order_by': 'date',
    }

    before_date = request.GET.get('before')
    after_date = request.GET.get('after')
    if before_date:
        date_obj = None
        try:
            date_obj = datetime.datetime.strptime(before_date, DATE_FORMAT)
        except ValueError as ex:
           return HttpResponseBadRequest('Bad date format')
        query_args['before'] = before_date
    if after_date:
        date_obj = None
        try:
            date_obj = datetime.datetime.strptime(after_date, DATE_FORMAT)
        except ValueError as ex:
           return HttpResponseBadRequest('Bad date format')
        query_args['after'] = after_date

    declist = country.declarations(**query_args)
    for dec in declist:
        writer.writerow([dec.area.name, dec.area.location, dec.area.population, dec.display_event_date(), dec.area.num_declared_ancestors()])

    return response

## ADMIN METHODS ##

def structure_del(request, structure_id):
    status=403
    if request.user.is_authenticated:
        status=200
        structure = get_object_or_404(Structure, pk=structure_id)
        structure.delete()
    return HttpResponse(status=status)

def area_del(request, area_id):
    status=403
    if request.user.is_authenticated:
        status=200
        area = get_object_or_404(Area, pk=area_id)
        area.delete()
    return HttpResponse(status=status)

def declaration_del(request, declaration_id):
    status=403
    if request.user.is_authenticated:
        status=200
        declaration = get_object_or_404(Declaration, pk=declaration_id)
        declaration.delete()
    return HttpResponse(status=status)

def link_del(request, link_id):
    status=403
    if request.user.is_authenticated:
        status=200
        link = get_object_or_404(Link, pk=link_id)
        link.delete()
    return HttpResponse(status=status)

def import_declaration_del(request, import_declaration_id):
    status=403
    if request.user.is_authenticated:
        status=200
        import_declaration = get_object_or_404(ImportDeclaration, pk=import_declaration_id)
        import_declaration.delete()
    return HttpResponse(status=status)

# TODO: add CSRF to AJAX form
@csrf_exempt
def extract_area_data(request):

    # get pasted text from POST data
    area_table = request.POST.get('area_table')
    area_unescaped = html.unescape(area_table)

    soup = BeautifulSoup( area_unescaped, 'html.parser')
    areas = []
    areastring = io.StringIO()
    writer = csv.writer(areastring)
    for td in soup.find_all('td'):
        a = td.find('a')
        if a:
            writer.writerow([a.get_text(), a['href']])
        else:
            tdtext = td.get_text()
            writer.writerow([tdtext])
    return JsonResponse({'areas': areastring.getvalue()})

# Create multiple areas at once from CSV-like text
def add_multi_areas(request, parent_id, structure_id):
    if request.method == 'POST' and request.user.is_authenticated:
        area_data = request.POST.get('area_csv_data')
        areastring = io.StringIO(area_data)
        reader = csv.reader(areastring)
        parent = Area.objects.get(id=parent_id)
        for row in reader:
            newarea_name = row[0]
            form = AreaForm({
                'country': parent.country_id,
                'location': parent.location,
                'parent': parent_id,
                'structure': structure_id,
                'name': newarea_name,
                'sort_name': newarea_name
            })
            if form.is_valid():
                newarea = form.save()
                logger.info("Created new area %s" % newarea)
                if len(row) == 2:
                    newurl = row[1]
                    link_data = {
                        'content_type_id': Area.content_type_id(),
                        'object_id': newarea.id,
                        'url': newurl,
                    }
                    newlink = Link(**link_data)
                    try:
                        newlink.full_clean()
                        newlink.save()
                        logger.info("Created new link %s" % newlink)
                    except ValidationError as ex:
                        logger.error("couldn't save new link: %s" % ex)
    return redirect('area', area_id=parent_id)

# Bin methods
def add_multi_import_declarations(request, country_code):
    lines = request.POST.get('paste_data').split('\n')
    for line in lines:
        values = line.split('|')
        if (len(values[4].split(' ')[0]) == 1):
            values[4] = '0' + values[4]
        importDeclaration = ImportDeclaration({
            'name': values[0],
            'num_govs': int(''.join(values[1].split(','))),
            'area': values[2],
            'population': int(''.join(values[3].split(','))),
            'date': datetime.datetime.strptime(values[4], '%d %b %Y').date(),
            'due': values[5],
            'contact': values[6],
            'link': values[7],
            'country': Country.objects.filter(country_code=country_code).first()
        })
        importDeclaration.save()

    return redirect('country', Country.objects.filter(country_code=country_code).first().id)

def import_declaration_pro(request, parent_id, structure_id, import_declaration_id):
    importDeclaration = ImportDeclaration.objects.filter(id=import_declaration_id).first()
    parent = Area.objects.filter(id=parent_id).first()
    structure = Structure.objects.filter(id=structure_id).first()

    area = Area(**{
        'name': importDeclaration.name,
        'country': importDeclaration.country,
        'location': importDeclaration.area,
        'population': importDeclaration.population,
        'structure': structure,
        'parent': parent,
    })
    area.save()

    declaration = Declaration(**{
        'area': area,
        'status': 'D',
        'event_date': importDeclaration.date,
    })
    declaration.save()

    if declaration.affects_population_count:
        # Regenerate all stored population counts for the country,
        # from the date of this declaration onwards
        area.country.generate_population_count(declaration.event_date)

    Link(**{
        'content_type_id': Declaration.content_type_id(),
        'object_id': declaration.id,
        'url': importDeclaration.link,
    }).save()

    importDeclaration.delete()

    return redirect('country', importDeclaration.country.id)

def declaration_from_import(request, area_id, import_declaration_id):
    importDeclaration = ImportDeclaration.objects.filter(id=import_declaration_id).first()
    area = Area.objects.filter(id=area_id).first()

    declaration = Declaration(**{
        'area': area,
        'status': 'D',
        'event_date': importDeclaration.date,
    })
    declaration.save()

    if declaration.affects_population_count:
        # Regenerate all stored population counts for the country,
        # from the date of this declaration onwards
        area.country.generate_population_count(declaration.event_date)

    Link(**{
        'content_type_id': Declaration.content_type_id(),
        'object_id': declaration.id,
        'url': importDeclaration.link,
    }).save()

    importDeclaration.delete()

    return redirect('country', importDeclaration.country.id)

