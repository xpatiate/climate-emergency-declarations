from django.shortcuts import get_object_or_404, render, redirect, Http404

from .models import Government, Country, Node, NodeType, NodeTypeForm, NodeForm, GovtForm

import logging 

# Create your views here.

def index(request):
    # get all governments who have declared
    glist = Government.objects.filter(status='D').order_by('date_declared')
    return render(request, 'govtrack/index.html', {'government_list': glist})


def node(request, node_id):
    node = get_object_or_404(Node, pk=node_id)
    return render(request, 'govtrack/node.html', {
        'record': node,
        'country': node.country,
        'parents_list': node.ancestors,
    })

def govt(request, govt_id):
    govt = get_object_or_404(Government, pk=govt_id)
    return render(request, 'govtrack/govt.html', {'record': govt, 'country': govt.country, 'parents_list': govt.ancestors})

def countries(request):
    clist = Country.objects.order_by('name')
    return render(request, 'govtrack/countries.html', {'country_list': clist})

def country(request, country_id):
    country = get_object_or_404(Country, pk=country_id)
    structure = make_hierarchy(NodeType.objects.filter(country=country_id).order_by('level','name'), set())
    cnodes = Node.objects.filter(country=country_id).select_subclasses().order_by('nodetype__level','name')
    records = make_hierarchy(cnodes, set())

    total_pop = 0
    for item in records:
        if item.is_counted:
            total_pop += item.population
        item.total_population = total_pop
        

    return render(request, 'govtrack/country.html', {
        'country': country,
        'structure_list': structure,
        'records_list': records,
        'total_declared_population': total_pop
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
    node = Node.objects.get_subclass(id=node_id)
    if not node:
        raise Http404("No such node")
    # If this is a govt, redirect to govt page
    if node.linkname == 'govt':
        return redirect('govt_edit', govt_id=node_id)
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

def govt_child(request, parent_id, nodetype_id):
    if request.method == 'POST':
        form = GovtForm(request.POST)
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
    form = GovtForm(initial=nodedata)
    return render(request, 'govtrack/govt.html', {'action': 'add', 'parent': parent, 'form': form, 'country': parent.country, 'nodetype_name': nodetype.name, 'parents_list': records, 'nodetype_id': nodetype_id})

def govt_edit(request, govt_id):
    govt = get_object_or_404(Government, pk=govt_id)
    form = GovtForm(instance=govt)
    if request.method == 'POST':
        form = GovtForm(request.POST, instance=govt)
        if form.is_valid():
            saved = form.save()
            return redirect('country', country_id=govt.country.id)
    govtdata = {
        'name': '',
        'parent': govt.parent.id,
        'country': govt.parent.country.id,
        'nodetype': govt.nodetype.id
    }
    return render(request, 'govtrack/govt.html', {'action': 'edit', 'record': govt, 'form': form, 'country': govt.country, 'parents_list': govt.ancestors})



def make_hierarchy(itemlist, seen):
    ordered = []
    # Items are ordered by level, so all the top-level ones come first
    for item in itemlist:
        if not item.id in seen:
            ordered.append(item)
            seen.add(item.id)
        if item.children:
            kidlist = make_hierarchy( item.children, seen )
            ordered.extend( kidlist )
    return ordered

# TODO integrate these into edit path
# so we can't delete just by sending a POST
def nodetype_del(request, nodetype_id):
    nodetype = NodeType.objects.get(id=nodetype_id)
    nodetype.delete()
    return redirect('country', country_id=nodetype.country.id)

def node_convert(request, node_id):
    node = get_object_or_404(Node, pk=node_id)
    nodedata = {
        'name': node.name,
        'parent': node.parent_id,
        'country': node.parent.country.id,
        'nodetype': node.nodetype_id
    }
    records = node.parent.ancestors
    form = GovtForm(initial=nodedata)
    return render(request, 'govtrack/govt.html', {'action': 'convert', 'parent': node.parent, 'form': form, 'country': node.parent.country, 'nodetype_name': node.nodetype.name, 'parents_list': records, 'node': node})

def node_del(request, node_id):
    node = Node.objects.get(id=node_id)
    node.delete()
    return redirect('country', country_id=node.country.id)

def govt_del(request, govt_id):
    govt = Government.objects.get(id=govt_id)
    govt.delete()
    return redirect('country', country_id=govt.country.id)

def govt_convert(request, node_id):
    if request.method == 'POST':
        node = None
        if node_id:
            node = get_object_or_404(Node, pk=node_id)
        # Create a brand-new Government object,
        # and delete the previous Node object.
        # This means that a new ID is issued, which shouldn't matter
        # as there are no other relationships depending on nodeID
        form = GovtForm(request.POST)
        if form.is_valid():
            form.save()
            node.delete()
            country_id = request.POST['country']
            return redirect('country', country_id=country_id)
    return redirect('/')

