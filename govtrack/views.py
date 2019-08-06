from django.shortcuts import get_object_or_404, render, redirect, Http404, HttpResponse
from django.forms import formset_factory
from django.http import HttpResponseBadRequest

from .models import Declaration, Country, Node, NodeType, Link
from .forms import NodeTypeForm, NodeForm, DeclarationForm, LinkForm, CountryForm

import csv
import datetime
import logging 
logger = logging.getLogger('govtrack')
DATE_FORMAT='%Y-%m-%d'

# Create your views here.

def index(request):
    # get all governments who have declared
    dlist = Declaration.objects.filter(status='D').order_by('node__country__name','node__sort_name')
    country_list = set([d.node.country for d in dlist])
    countries = []
    for c in country_list:
        dlist = c.declarations()
        if dlist:
            countries.append(({
                'name': c.name,
                'id': c.id,
                'num_nodes': len(dlist),
                'declared_population': c.declared_population
            },
            dlist))
    return render(request, 'govtrack/index.html', {'countries': countries})


def node(request, node_id):
    node = get_object_or_404(Node, pk=node_id)
    return render(request, 'govtrack/node.html', {
        'record': node,
        'country': node.country,
        'parents_list': node.ancestors,
        'links': node.links.all(),
    })

def countries(request):
    clist = Country.objects.order_by('name')
    for c in clist:
        c.node_population = c.declared_population
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

    structure = country.get_root_nodetype().build_hierarchy()
    logger.debug("*** building hierarchy for records")
    records = country.get_root_node().build_hierarchy()
    logger.debug("*** done building hierarchy for records")

    total_pop = 0
    for item in records:
        total_pop += item.contribution()
        item.cumulative_pop += total_pop
        
    logger.debug("*** counting total declared population")
    total_declared_pop = country.get_root_node().declared_population()
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


def nodetype_edit(request, nodetype_id):
    nodetype = get_object_or_404(NodeType, pk=nodetype_id)
    form = NodeTypeForm(instance=nodetype)
    link_initial = {
        'content_type': NodeType.content_type_id(),
        'object_id': nodetype_id,
    }
    if request.method == 'POST':
        form = NodeTypeForm(request.POST, instance=nodetype)
        linkform = LinkForm(request.POST, initial=link_initial)
        if form.is_valid():
            form.save()
            if linkform.has_changed() and linkform.is_valid():
                linkform.save()
        return redirect('country', country_id=nodetype.country.id)

    linkform = LinkForm(initial=link_initial)
    return render(request, 'govtrack/nodetype.html', {
        'action': 'edit',
        'nodetype': nodetype,
        'form': form,
        'country': nodetype.country,
        'parents_list': nodetype.ancestors,
        'links': nodetype.links.all(),
        'linkform': linkform,
        })

def nodetype_child(request, parent_id):
    parent = get_object_or_404(NodeType, pk=parent_id)
    if request.method == 'POST':
        form = NodeTypeForm(request.POST)
        if form.is_valid():
            form.save()
            country_id = request.POST['country']
            return redirect('country', country_id=country_id)
    nodetypedata = {
        'name': '',
        'parent': parent_id,
        'level': (parent.level+1),
        'country': parent.country.id
    }
    form = NodeTypeForm(initial=nodetypedata)
    return render(request, 'govtrack/nodetype.html', {'action': 'add', 'form': form, 'country': parent.country, 'parent': parent, 'parents_list': parent.ancestors})

def node_edit(request, node_id):
    node = get_object_or_404(Node, pk=node_id)
    form = NodeForm(instance=node)

    link_initial = {
        'content_type': Node.content_type_id(),
        'object_id': node_id,
    }
    linkform = LinkForm(initial=link_initial)
    # If POST received, save form
    if request.method == 'POST':
        form = NodeForm(request.POST, instance=node)
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
                return redirect('country', country_id=node.country.id)

    # Show form
    form.fields['supplements'].queryset = node.parent.get_supplement_choices()
    return render(request, 'govtrack/node.html', {
        'action': 'edit',
        'record': node,
        'form': form,
        'links': node.links.all(),
        'linkform': linkform,
        'country': node.country,
        'parents_list': node.ancestors,
        'supplements_list': node.supplements.all()
        })

def node_child(request, parent_id, nodetype_id):
    if request.method == 'POST':
        form = NodeForm(request.POST)
        if form.is_valid():
            form.save()
            country_id = request.POST['country']
            return redirect('country', country_id=country_id)
    parent = get_object_or_404(Node, pk=parent_id)
    nodetype = get_object_or_404(NodeType, pk=nodetype_id)
    nodedata = {
        'name': '',
        'parent': parent_id,
        'country': parent.country.id,
        'nodetype': nodetype_id
    }
    records = parent.ancestors
    form = NodeForm(initial=nodedata)
    form.fields['supplements'].queryset = parent.get_supplement_choices()

    return render(request, 'govtrack/node.html', {
        'action': 'add',
        'parent': parent,
        'form': form,
        'country': parent.country,
        'nodetype_name': nodetype.name,
        'parents_list': records,
        'nodetype_id': nodetype_id
        })

def declaration(request, declaration_id):
    dec = get_object_or_404(Declaration, pk=declaration_id)
    return render(request, 'govtrack/declare.html', {
        'action': 'view',
        'declaration': dec,
        'node': dec.node,
        'links': dec.links.all(),
        })

def declaration_add(request, node_id):
    if request.method == 'POST':
        form = DeclarationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('node', node_id=node_id)
    node = get_object_or_404(Node, pk=node_id)
    decldata = {
        'node': node_id,
    }
    form = DeclarationForm(initial=decldata)
    return render(request, 'govtrack/declare.html', {
        'action': 'add',
        'form': form,
        'node': node
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
                return redirect('node', node_id=dec.node.id)
    # Show form
    return render(request, 'govtrack/declare.html', {
        'action': 'edit',
        'declaration': dec,
        'form': form,
        'linkform': linkform,
        'node': dec.node,
        'links': dec.links.all(),
        })

# API methods
def nodetype_del(request, nodetype_id):
    status=403
    if request.user.is_authenticated:
        status=200
        nodetype = get_object_or_404(NodeType, pk=nodetype_id)
        nodetype.delete()
    return HttpResponse(status=status)

def node_del(request, node_id):
    status=403
    if request.user.is_authenticated:
        status=200
        node = get_object_or_404(Node, pk=node_id)
        node.delete()
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
        writer.writerow([dec.node.name, dec.node.location, dec.node.population, dec.date_declared, dec.node.num_declared_ancestors()])

    return response
