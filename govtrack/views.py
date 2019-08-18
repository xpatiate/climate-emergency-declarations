from django.shortcuts import get_object_or_404, render, redirect, Http404, HttpResponse
from django.forms import formset_factory
from django.http import JsonResponse, HttpResponseBadRequest

from .models import Declaration, Country, Area, Structure, Link
from .forms import StructureForm, AreaForm, DeclarationForm, LinkForm, CountryForm

import csv
import datetime
import html
import logging 
logger = logging.getLogger('cegov')

# Create your views here.

def index(request):
    # first get all countries with active declarations
    dlist = Declaration.objects.filter(status='D').order_by('area__country__name','area__sort_name')
    declared_countries = set([d.area.country for d in dlist])
    country_list = sorted(list(declared_countries), key=lambda c: c.name)
    countries = []
    # now get the actual declarations for each country
    for c in country_list:
        dlist = c.active_declarations()
        if dlist:
            countries.append(({
                'name': c.name,
                'id': c.id,
                'num_areas': len(dlist),
                'declared_population': c.current_popcount
            },
            dlist))
    return render(request, 'govtrack/index.html', {'countries': countries})


def area(request, area_id):
    area = get_object_or_404(Area, pk=area_id)
    records = area.build_hierarchy()

    return render(request, 'govtrack/area.html', {
        'area': area,
        'country': area.country,
        'parents_list': area.direct_ancestors,
        'areas_list': records,
        'links': area.links.all(),
        'area_api_link': request.build_absolute_uri( area.api_link ),
    })

def countries(request):
    clist = Country.objects.order_by('name')
    for c in clist:
        c.area_population = c.current_popcount
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
        action='view'
        if request.POST.get('save'):
            form = CountryForm(request.POST, instance=country)
            linkform = LinkForm(request.POST, initial=link_initial)
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
    records = country.get_root_area().build_hierarchy()

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
            item.show_contribution = 0

    total_declared_pop = country.current_popcount

    return render(request, 'govtrack/country.html', {
        'action': action,
        'country': country,
        'structure_list': structure,
        'areas_list': records,
        'total_declared_population': total_declared_pop,
        'total_pop_by_contribution': total_pop,
        'links': country.links.all(),
        'form': form,
        'linkform': linkform,
        'country_api_link': request.build_absolute_uri( country.api_link ),
        })


def structure_edit(request, structure_id):
    structure = get_object_or_404(Structure, pk=structure_id)
    form = StructureForm(instance=structure)
    link_initial = {
        'content_type': Structure.content_type_id(),
        'object_id': structure_id,
    }
    if request.method == 'POST':
        do_redir = True
        if request.POST.get('save'):
            do_redir = False
            form = StructureForm(request.POST, instance=structure)
            linkform = LinkForm(request.POST, initial=link_initial)
            if form.is_valid():
                form.save()
                if linkform.has_changed() and linkform.is_valid():
                    linkform.save()
        if do_redir:
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
    country_id = parent.country.id
    if request.method == 'POST':
        do_redir = True
        if request.POST.get('save'):
            do_redir = False
            form = StructureForm(request.POST)
            if form.is_valid():
                form.save()
        if do_redir:
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
        do_redir=True
        if request.POST.get('save'):
            form = AreaForm(request.POST, instance=area)
            linkform = LinkForm(request.POST, initial=link_initial)
            do_redir = False
            if form.is_valid():
                saved = form.save()
                do_redir=True
                if linkform.has_changed():
                    do_redir=False
                    if linkform.is_valid():
                        linkform.save()
                        do_redir=True
                    else:
                        logger.warn("did not save url because %s " % linkform.errors)
            return redirect('area', area_id=area.id)

    # Show form
    form.fields['supplements'].queryset = area.parent.get_supplement_choices(exclude=area.id)
    return render(request, 'govtrack/area.html', {
        'action': 'edit',
        'area': area,
        'form': form,
        'links': area.links.all(),
        'linkform': linkform,
        'country': area.country,
        'parents_list': area.direct_ancestors,
        'supplements_list': area.supplements.all(),
        })

def area_child(request, parent_id, structure_id):
    if request.method == 'POST':
        do_redir = True
        if request.POST.get('save'):
            do_redir = False
            form = AreaForm(request.POST)
            if form.is_valid():
                area = form.save()
                do_redir = True
                area_id = area.id
        else:
            area_id = parent_id
        if do_redir:
            return redirect('area', area_id=area_id)
    parent = get_object_or_404(Area, pk=parent_id)
    structure = get_object_or_404(Structure, pk=structure_id)
    areadata = {
        'name': '',
        'parent': parent_id,
        'country': parent.country.id,
        'location': parent.location,
        'structure': structure_id
    }
    records = parent.direct_ancestors
    form = AreaForm(initial=areadata)
    form.fields['supplements'].queryset = parent.get_supplement_choices()

    return render(request, 'govtrack/area.html', {
        'action': 'add',
        'parent': parent,
        'form': form,
        'country': parent.country,
        'structure_name': structure.name,
        'parents_list': records,
        'structure_id': structure_id,
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
    area = get_object_or_404(Area, pk=area_id)
    decldata = {
        'area': area_id,
    }
    form = DeclarationForm(initial=decldata)
    if request.method == 'POST':
        do_redir = True
        if request.POST.get('save'):
            do_redir = False
            form = DeclarationForm(request.POST, initial=decldata)
            if form.is_valid():
                do_redir = True
                dec = form.save()
                if dec.affects_population_count:
                    # Regenerate all stored population counts for the country,
                    # from the date of this declaration onwards
                    dec.area.country.generate_population_count(dec.event_date)
        if do_redir:
            return redirect('area', area_id=area_id)
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
        do_redir = True
        if request.POST.get('save'):
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

