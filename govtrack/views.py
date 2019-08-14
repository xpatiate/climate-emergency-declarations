from django.shortcuts import get_object_or_404, render, redirect, Http404, HttpResponse
from django.forms import formset_factory
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .models import Declaration, Country, Area, Structure, Link
from .forms import StructureForm, AreaForm, DeclarationForm, LinkForm, CountryForm

from bs4 import BeautifulSoup
import csv
import datetime
import html
import io
import logging 
logger = logging.getLogger('govtrack')
DATE_FORMAT='%Y-%m-%d'

# Create your views here.

def index(request):
    # get all governments who have declared
    dlist = Declaration.objects.filter(status='D').order_by('area__country__name','area__sort_name')
    country_list = set([d.area.country for d in dlist])
    countries = []
    for c in country_list:
        dlist = c.declarations()
        if dlist:
            countries.append(({
                'name': c.name,
                'id': c.id,
                'num_areas': len(dlist),
                'declared_population': c.declared_population
            },
            dlist))
    return render(request, 'govtrack/index.html', {'countries': countries})


def area(request, area_id):
    area = get_object_or_404(Area, pk=area_id)
    records = area.build_hierarchy()
    return render(request, 'govtrack/area.html', {
        'record': area,
        'country': area.country,
        'parents_list': area.ancestors,
        'records_list': records,
        'links': area.links.all(),
    })

def countries(request):
    clist = Country.objects.order_by('name')
    for c in clist:
        c.area_population = c.declared_population
    return render(request, 'govtrack/countries.html', {'country_list': clist})

def country(request, country_id, action='view'):
    country = get_object_or_404(Country, pk=country_id)
    form = CountryForm(instance=country)

    link_initial = {
        'content_type': Country.content_type_id(),
        'object_id': country_id,
    }
    linkform = LinkForm(initial=link_initial)
    
    # If POST received, save form
    if request.method == 'POST':
        form = CountryForm(request.POST, instance=country)
        linkform = LinkForm(request.POST, initial=link_initial)
        do_redir = False
        if form.is_valid():
            saved = form.save()
            action='view'
            if linkform.has_changed():
                if linkform.is_valid():
                    linkform.save()
                else:
                    logger.warn("did not save url because %s " % linkform.errors)
                    action='edit'

    structure = country.get_root_structure().build_hierarchy()
    logger.debug("*** building hierarchy for records")
    records = country.get_root_area().build_hierarchy()
    logger.debug("*** done building hierarchy for records")

    total_pop = 0
    item_seen = set()
    for item in records:
        if item not in item_seen:
            total_pop += item.contribution()
            item.show_contribution = item.contribution()
            item.cumulative_pop += total_pop
            item_seen.add(item)
        else:
            item.cumulative_pop = total_pop

    logger.debug("*** counting total declared population")
    total_declared_pop = country.get_root_area().declared_population()
    logger.debug("*** done counting total declared population")

    return render(request, 'govtrack/country.html', {
        'action': action,
        'country': country,
        'structure_list': structure,
        'records_list': records,
        'total_declared_population': total_declared_pop,
        'total_pop_by_contribution': total_pop,
        'links': country.links.all(),
        'form': form,
        'linkform': linkform,
        })


def structure_edit(request, structure_id):
    structure = get_object_or_404(Structure, pk=structure_id)
    form = StructureForm(instance=structure)
    link_initial = {
        'content_type': Structure.content_type_id(),
        'object_id': structure_id,
    }
    if request.method == 'POST':
        form = StructureForm(request.POST, instance=structure)
        linkform = LinkForm(request.POST, initial=link_initial)
        if form.is_valid():
            form.save()
            if linkform.has_changed() and linkform.is_valid():
                linkform.save()
        return redirect('country', country_id=structure.country.id)

    linkform = LinkForm(initial=link_initial)
    return render(request, 'govtrack/structure.html', {
        'action': 'edit',
        'structure': structure,
        'form': form,
        'country': structure.country,
        'parents_list': structure.ancestors,
        'links': structure.links.all(),
        'linkform': linkform,
        })

def structure_child(request, parent_id):
    parent = get_object_or_404(Structure, pk=parent_id)
    if request.method == 'POST':
        form = StructureForm(request.POST)
        if form.is_valid():
            form.save()
            country_id = request.POST['country']
            return redirect('country', country_id=country_id)
    structuredata = {
        'name': '',
        'parent': parent_id,
        'level': (parent.level+1),
        'country': parent.country.id
    }
    form = StructureForm(initial=structuredata)
    return render(request, 'govtrack/structure.html', {'action': 'add', 'form': form, 'country': parent.country, 'parent': parent, 'parents_list': parent.ancestors})

def area_edit(request, area_id):
    area = get_object_or_404(Area, pk=area_id)
    form = AreaForm(instance=area)

    link_initial = {
        'content_type': Area.content_type_id(),
        'object_id': area_id,
    }
    linkform = LinkForm(initial=link_initial)
    # If POST received, save form
    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        linkform = LinkForm(request.POST, initial=link_initial)
        do_redir = False
        if form.is_valid():
            do_redir=True
            saved = form.save()
            if linkform.has_changed():
                do_redir=False
                if linkform.is_valid():
                    linkform.save()
                    do_redir=True
                else:
                    logger.warn("did not save url because %s " % linkform.errors)
            if do_redir:
                return redirect('country', country_id=area.country.id)

    # Show form
    form.fields['supplements'].queryset = area.parent.get_supplement_choices(exclude=area.id)
    return render(request, 'govtrack/area.html', {
        'action': 'edit',
        'record': area,
        'form': form,
        'links': area.links.all(),
        'linkform': linkform,
        'country': area.country,
        'parents_list': area.ancestors,
        'supplements_list': area.supplements.all()
        })

def area_child(request, parent_id, structure_id):
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            form.save()
            country_id = request.POST['country']
            return redirect('country', country_id=country_id)
    parent = get_object_or_404(Area, pk=parent_id)
    structure = get_object_or_404(Structure, pk=structure_id)
    areadata = {
        'name': '',
        'parent': parent_id,
        'country': parent.country.id,
        'location': parent.location,
        'structure': structure_id
    }
    records = parent.ancestors
    form = AreaForm(initial=areadata)
    form.fields['supplements'].queryset = parent.get_supplement_choices()

    return render(request, 'govtrack/area.html', {
        'action': 'add',
        'parent': parent,
        'form': form,
        'country': parent.country,
        'structure_name': structure.name,
        'parents_list': records,
        'structure_id': structure_id
        })

def declaration(request, declaration_id):
    dec = get_object_or_404(Declaration, pk=declaration_id)
    return render(request, 'govtrack/declare.html', {
        'action': 'view',
        'declaration': dec,
        'area': dec.area,
        'links': dec.links.all(),
        })

def declaration_add(request, area_id):
    if request.method == 'POST':
        form = DeclarationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('area', area_id=area_id)
    area = get_object_or_404(Area, pk=area_id)
    decldata = {
        'area': area_id,
    }
    form = DeclarationForm(initial=decldata)
    return render(request, 'govtrack/declare.html', {
        'action': 'add',
        'form': form,
        'area': area
        })

def declaration_edit(request, declaration_id):
    dec = Declaration.objects.get(id=declaration_id)
    if not dec:
        raise Http404("No such declaration")
    form = DeclarationForm(instance=dec)
    link_initial = {
        'content_type': Declaration.content_type_id(),
        'object_id': declaration_id,
    }
    linkform = LinkForm(initial=link_initial)
    # If POST received, save form
    if request.method == 'POST':
        form = DeclarationForm(request.POST, instance=dec)
        linkform = LinkForm(request.POST, initial=link_initial)
        do_redir = False
        if form.is_valid():
            do_redir=True
            saved = form.save()
            if linkform.has_changed():
                do_redir=False
                if linkform.is_valid():
                    linkform.save()
                    do_redir=True
                else:
                    logger.warn("did not save url because %s " % linkform.errors)
            if do_redir:
                return redirect('area', area_id=dec.area.id)
    # Show form
    return render(request, 'govtrack/declare.html', {
        'action': 'edit',
        'declaration': dec,
        'form': form,
        'linkform': linkform,
        'area': dec.area,
        'links': dec.links.all(),
        })

# API methods
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

