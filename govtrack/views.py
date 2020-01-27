from django.shortcuts import get_object_or_404, render, redirect, Http404, HttpResponse
from django.forms.models import formset_factory, modelformset_factory, inlineformset_factory
from django.forms import HiddenInput
from django.http import JsonResponse, HttpResponseBadRequest
import django.urls

from .models import Declaration, Country, Area, Structure, Link, ImportDeclaration
from .forms import StructureForm, AreaForm, DeclarationForm, LinkForm, CountryForm, SelectBulkAreaForm, BulkAreaForm

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
    return render(request, 'govtrack/index.html', {
        'countries': countries
        })

def area(request, area_id):
    area = get_object_or_404(Area, pk=area_id)
    records = area.build_hierarchy()

    import_declarations = ImportDeclaration.objects.filter(country=area.country).order_by('date')

    return render(request, 'govtrack/area.html', {
        'area': area,
        'country': area.country,
        'bulkform': SelectBulkAreaForm(),
        'parents_list': area.direct_ancestors,
        'areas_list': records,
        'import_declaration_list': import_declarations,
        'links': area.links.all(),
        'area_api_link': request.build_absolute_uri( area.api_link ),
        'country_api_trigger_link': area.country.api_recount_link,
    })

def countries(request):
    clist = Country.objects.order_by('name')
    update_needed = False
    for c in clist:
        c.inbox_count = ImportDeclaration.objects.filter(country=c).count()
        c.area_population = c.current_popcount
        if c.is_popcount_needed:
            update_needed = True
    return render(request, 'govtrack/countries.html', {
        'country_list': clist,
        'update_needed': update_needed,
        'update_url': request.build_absolute_uri(
            django.urls.reverse('api_trigger_all_recounts')
            )
        })

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

    import_declarations = ImportDeclaration.objects.filter(country=country).order_by('date')

    total_declared_pop = country.current_popcount

    return render(request, 'govtrack/country.html', {
        'action': action,
        'country': country,
        'structure_list': structure,
        'areas_list': records,
        'import_declaration_list': import_declarations,
        'total_declared_population': total_declared_pop,
        'links': country.links.all(),
        'form': form,
        'linkform': linkform,
        'country_api_link': request.build_absolute_uri( country.api_link ),
        'country_api_trigger_link': request.build_absolute_uri( country.api_recount_link ),
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
    link_initial = {
        'content_type': Structure.content_type_id(),
        'object_id': 'unknown',
    }
    linkform = LinkForm(initial=link_initial)
    if request.method == 'POST':
        do_redir = True
        if request.POST.get('save'):
            do_redir = False
            form = StructureForm(request.POST)
            if form.is_valid():
                new_struct = form.save()
                do_redir=True
                new_link_url = request.POST.get('link-url')
                if new_link_url:
                    post_data = {
                        'link-object_id': new_struct.id,
                        'link-content_type': link_initial['content_type'],
                        'link-url': request.POST.get('link-url')
                    }
                    linkform = LinkForm(post_data)
                    do_redir=False
                    if linkform.is_valid():
                        linkform.save()
                        do_redir=True
                    else:
                        logger.warn("did not save url because %s " % linkform.errors)
        if do_redir:
            return redirect('country', country_id=country_id)
    structuredata = {
        'name': '',
        'parent': parent_id,
        'level': (parent.level+1),
        'country': parent.country.id
    }
    form = StructureForm(initial=structuredata)
    return render(request, 'govtrack/structure.html', {
        'action': 'add',
        'form': form,
        'linkform': linkform,
        'country': parent.country,
        'parent': parent,
        'parents_list': parent.ancestors,
        })


def bulkarea_save(request, area_id):
    area = get_object_or_404(Area, pk=area_id)
    logger.info(f"saving bulk area data for {area}")
    if request.method == 'POST' and request.POST.get('save'):
        idlist = request.POST.get('area_id_str').split(':')
        for aid in idlist:
            logger.info(aid)
        masterform = BulkAreaForm(request.POST)
        if masterform.is_valid():
            cdata = masterform.cleaned_data
            logger.info(f"clean data {cdata}")
            areas = Area.objects.filter(id__in=idlist)
            logger.info(areas)
            if cdata['location']:
                areas.update(location=cdata['location'])
            if request.POST.get('clear_location','') == 'true':
                areas.update(location='')
            supps_to_add_str = request.POST.get('supp_list_add')
            supps_to_rm_str = request.POST.get('supp_list_rm')
            supps_to_add = set(supps_to_add_str.split(':'))
            supps_to_rm = set(supps_to_rm_str.split(':'))
            logger.info(f"adding supps {supps_to_add_str} {supps_to_add}")
            logger.info(f"rming supps {supps_to_rm_str} {supps_to_rm}")

            for area in areas:
                all_current_supps = list(area.supplements.all().values_list('id', flat=True))
                logger.info(f"current supps: { all_current_supps }")
                a_changed = False
                for add_area in supps_to_add:
                    if add_area and int(add_area) not in all_current_supps:
                        if int(add_area) == int(area.id):
                            logger.info(f"Can't add area {add_area} to {area.id} are you crazy?")
                        else:
                            logger.info(f"adding area {add_area} to supps {all_current_supps} for {area.id}: {add_area == area.id}")
                            area.supplements.add(add_area)
                            a_changed = True
                for rm_area in supps_to_rm:
                    if rm_area and int(rm_area) in all_current_supps:
                        logger.info(f"rming area {rm_area} from supps {all_current_supps}")
                        area.supplements.remove(rm_area)
                        a_changed = True
                if a_changed:
                    logger.info(f"about to save area {area.id}")
                    area.save()
                    logger.info(f"done saving area {area.id}")
                all_latest_supps = list(area.supplements.all().values_list('id', flat=True))
                logger.info(f"updated supps: { all_latest_supps }")
            logger.info(f"Completed updating supps for { area }")
    return redirect('area', area_id=area_id)

def bulkarea_edit(request, area_id):
    area = get_object_or_404(Area, pk=area_id)
    parent = area.parent
    logger.info(area)

    bulkform = SelectBulkAreaForm(request.POST)
    bulkform.is_valid()
    alldata = bulkform.cleaned_data
    num_areas = len(alldata.get('areas', []))
    logger.info(f"got {num_areas} areas to bulk edit")
    if num_areas == 0:
        return redirect('area', area_id=area_id)
    if request.method == 'POST' and request.POST.get('delete'):
        logger.info(f"Deleting {num_areas} areas!!!")
        (num_deleted, types_deleted) = alldata['areas'].delete()
        area.country.popcount_update_needed()
        logger.info(f"Deleted {num_deleted} areas: {types_deleted}")
        try:
            # main area still exists, redirect there
            Area.objects.get(pk=area_id)
            return redirect('area', area_id=area_id)
        except Area.DoesNotExist:
            # redirect to parent
            return redirect('area', area_id=parent.id)
    supp_set = set()
    area_initial = [
            { 
                'id': a.id,
                'name': a.name,
                'location': a.location or '',
                'supplements': a.supplement_list,
                'supplement_ids': [s.id for s in a.supplements.all()]
                }
                for a in alldata['areas']
            ]
    combined_supps = [ s for a in area_initial for s in a['supplement_ids'] ]
    supp_set.update(combined_supps)
    logger.info(f"all existing supps: {supp_set}")
    newform = BulkAreaForm()
    main_supps = area.get_supplement_choices()
    current_supps = Area.objects.filter(id__in=supp_set)
    newform.fields['supplements_add'].choices = [ (s.id, s.name) for s in main_supps ]
    newform.fields['supplements_rm'].choices = [ (s.id, s.name) for s in current_supps ]
    logger.info(f"areas: {area_initial}")
    area_ids = [ str(a['id']) for a in area_initial ]
    return render(request, 'govtrack/bulkarea.html', {
        'area': area,
        'country': area.country,
        'form': newform,
        'area_list': area_initial,
        'area_id_str': ':'.join(area_ids),
    })


def area_edit(request, area_id):
    area = get_object_or_404(Area, pk=area_id)
    form = AreaForm(instance=area)
    import_declarations = ImportDeclaration.objects.filter(country=area.country).order_by('date')

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
        if do_redir:
            return redirect('area', area_id=area.id)

    # Show form
    return render(request, 'govtrack/area.html', {
        'action': 'edit',
        'area': area,
        'form': form,
        'links': area.links.all(),
        'linkform': linkform,
        'country': area.country,
        'parents_list': area.direct_ancestors,
        'supplements_list': area.supplements.all(),
        'import_declaration_list': import_declarations,
        })

def area_child(request, parent_id, structure_id):
    link_initial = {
        'content_type': Area.content_type_id(),
        'object_id': 'unknown',
    }
    linkform = LinkForm(initial=link_initial)
    if request.method == 'POST':
        do_redir = True
        if request.POST.get('save'):
            do_redir = False
            form = AreaForm(request.POST)
            if form.is_valid():
                logger.info("Calling form save")
                area = form.save()
                logger.info(f"Now got area {area.id}")
                do_redir = True
                area_id = area.id
                new_link_url = request.POST.get('link-url')
                if new_link_url:
                    # XXX there must be a better way to do this - have tried:
                    #
                    # link_initial['object_id'] = area_id
                    # linkform = LinkForm(request.POST, initial=link_initial)

                    # but it seems that the hidden object_id overrides the set one
                    # so have to make a fake POST data dict
                    post_data = {
                        'link-object_id': area_id,
                        'link-content_type': link_initial['content_type'],
                        'link-url': request.POST.get('link-url')
                    }
                    linkform = LinkForm(post_data)
                    do_redir=False
                    if linkform.is_valid():
                        linkform.save()
                        do_redir=True
                    else:
                        logger.warn("did not save url because %s " % linkform.errors)
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

    return render(request, 'govtrack/area.html', {
        'action': 'add',
        'parent': parent,
        'form': form,
        'linkform': linkform,
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
    link_initial = {
        'content_type': Declaration.content_type_id(),
    }
    linkform = LinkForm(initial=link_initial)
    if request.method == 'POST':
        do_redir = True
        if request.POST.get('save'):
            do_redir = False
            form = DeclarationForm(request.POST, initial=decldata)
            if form.is_valid():
                do_redir = True
                dec = form.save()
                link_initial['object_id'] = dec.id
                request.POST._mutable = True
                request.POST['link-object_id'] = dec.id
                linkform = LinkForm(request.POST, initial=link_initial)
                if linkform.has_changed():
                    do_redir=False
                    if linkform.is_valid():
                        linkform.save()
                        do_redir=True
                if dec.affects_population_count:
                    # Regenerate all stored population counts for the country,
                    # from the date of this declaration onwards
                    dec.area.country.popcount_update_needed(dec.event_date)
        if do_redir:
            return redirect('area', area_id=area_id)
    return render(request, 'govtrack/declare.html', {
        'action': 'add',
        'form': form,
        'linkform': linkform,
        'area': area
        })

def declaration_edit(request, declaration_id):
    dec = Declaration.objects.get(id=declaration_id)
    if not dec:
        raise Http404("No such declaration")
    form = DeclarationForm(instance=dec)
    import_declarations = ImportDeclaration.objects.filter(country=dec.area.country).order_by('date')
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
        'import_declaration_list': import_declarations,
        })

def inbox(request, country_id):
    country = get_object_or_404(Country, pk=country_id)
    return render(request, 'govtrack/inbox.html', {
        'country': country,
        'country_list': Country.objects.order_by('name'),
        'import_declaration_list': ImportDeclaration.objects.filter(country=country).order_by('date'),
    })
