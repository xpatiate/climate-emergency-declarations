from django.shortcuts import get_object_or_404, render, redirect, Http404, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from govtrack.models import Declaration, Country, Area, Structure, Link
from govtrack.forms import AreaForm

from bs4 import BeautifulSoup
import csv
import datetime
import html
import io
import logging

logger = logging.getLogger('cegov')
DATE_FORMAT='%Y-%m-%d'

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
    if request.method == 'POST':
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

