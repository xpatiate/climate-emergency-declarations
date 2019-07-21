"""
WSGI config for ced project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ced.settings')

application = get_wsgi_application()

from govtrack.models import Country, NodeType

country = Country.objects.get(pk=68)
print(country.name)

if sys.argv[1] == 'add':
    nodedata = {
        'level':1,
        'count_population':'f',
        'country_id':68,
        'is_governing':'t',
        'name': ''
    }
    get = lambda node_id: NodeType.objects.get(pk=node_id)
    nodedata['name'] = 'National Government'
    root = NodeType.add_root(**nodedata)
    nodedata['name'] = 'Region'
    region = get(root.pk).add_child(**nodedata)
    nodedata['name'] = 'Ceremonial County'
    ceremonial = get(region.pk).add_child(**nodedata)
    nodedata['name'] = 'Unitary Authority'
    unitary = get(ceremonial.pk).add_child(**nodedata)
    nodedata['name'] = 'Parish'
    parish = get(unitary.pk).add_child(**nodedata)
    nodedata['name'] = 'Combined Authority'
    combined = get(region.pk).add_child(**nodedata)
else:

    print("whole tree")
    mytree = NodeType.get_tree()
#    print(mytree)
    for node in mytree:
        print('%s: %s' % (node.get_depth(), node.name))

    print("traversal")
    top = NodeType.get_first_root_node()
    print(top)
    for c in top.get_children():
        print("- %s" % c.name)
        for d in c.get_children():
            print("-- %s" % d.name)
            for e in d.get_children():
                print("--- %s" % e.name)
                for f in e.get_children():
                    print("---- %s" % f.name)

    print("annotated list")
    for item, info in NodeType.get_annotated_list():
        print("%s: %s" % (item, info))
