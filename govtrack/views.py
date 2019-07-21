from django.shortcuts import get_object_or_404, render, redirect, Http404

from .models import Declaration, Country, Node, NodeType, NodeTypeForm, NodeForm, DeclarationForm

import logging 

# Create your views here.

def index(request):
    # get all governments who have declared
    dlist = Declaration.objects.filter(status='D').order_by('node__country__name','node__sort_name')
    country_list = set([d.node.country for d in dlist])
    countries = []
    for c in country_list:
        dlist = c.declarations
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
    })

def countries(request):
    clist = Country.objects.order_by('name')
    for c in clist:
        c.node_population = c.get_root_node().declared_population()
    return render(request, 'govtrack/countries.html', {'country_list': clist})

def country(request, country_id):
    country = get_object_or_404(Country, pk=country_id)

    structure = country.get_root_nodetype().build_hierarchy()
    records = country.get_root_node().build_hierarchy()

    total_pop = 0
    for item in records:
        if item.is_counted:
            total_pop += item.population
        item.total_population = total_pop
        

    return render(request, 'govtrack/country.html', {
        'country': country,
        'structure_list': structure,
        'records_list': records,
        'total_declared_population': country.get_root_node().declared_population()
        })


def nodetype_edit(request, nodetype_id):
    nodetype = get_object_or_404(NodeType, pk=nodetype_id)
    form = NodeTypeForm(instance=nodetype)
    if request.method == 'POST':
        form = NodeTypeForm(request.POST, instance=nodetype)
        if form.is_valid():
            form.save()
        return redirect('country', country_id=nodetype.country.id)
    return render(request, 'govtrack/nodetype.html', {'action': 'edit', 'nodetype': nodetype, 'form': form, 'country': nodetype.country, 'parents_list': nodetype.ancestors})

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
    node = Node.objects.get(id=node_id)
    if not node:
        raise Http404("No such node")
    form = NodeForm(instance=node)
    # If POST received, save form
    if request.method == 'POST':
        form = NodeForm(request.POST, instance=node)
        if form.is_valid():
            saved = form.save()
            return redirect('country', country_id=node.country.id)
    # Show form
    nodedata = {
        'name': '',
        'parent': node.parent.id,
        'country': node.parent.country.id,
        'nodetype': node.nodetype.id
    }
    return render(request, 'govtrack/node.html', {'action': 'edit', 'record': node, 'form': form, 'country': node.country, 'parents_list': node.ancestors})

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
    return render(request, 'govtrack/node.html', {'action': 'add', 'parent': parent, 'form': form, 'country': parent.country, 'nodetype_name': nodetype.name, 'parents_list': records, 'nodetype_id': nodetype_id})

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
    return render(request, 'govtrack/declare.html', {'action': 'add', 'form': form, 'node': node})

def declaration_edit(request, declaration_id):
    dec = Declaration.objects.get(id=declaration_id)
    if not dec:
        raise Http404("No such declaration")
    form = DeclarationForm(instance=dec)
    # If POST received, save form
    if request.method == 'POST':
        form = DeclarationForm(request.POST, instance=dec)
        if form.is_valid():
            saved = form.save()
            return redirect('node', node_id=dec.node.id)
    # Show form
    return render(request, 'govtrack/declare.html', {'action': 'edit', 'declaration': dec, 'form': form, 'node': dec.node})

# TODO integrate these into edit path
# so we can't delete just by sending a POST
def nodetype_del(request, nodetype_id):
    nodetype = NodeType.objects.get(id=nodetype_id)
    nodetype.delete()
    return redirect('country', country_id=nodetype.country.id)

def node_del(request, node_id):
    node = Node.objects.get(id=node_id)
    node.delete()
    return redirect('country', country_id=node.country.id)
