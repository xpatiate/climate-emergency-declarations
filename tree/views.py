from django.shortcuts import render
from .models import Category

# Create your views here.
def index(request):

    get = lambda node_id: Category.objects.get(pk=node_id)
    root = Category.add_root(name='Computer Hardware')
    node = get(root.pk).add_child(name='Memory')
    get(node.pk).add_sibling(name='Hard Drives')
    get(node.pk).add_sibling(name='SSD')
    get(node.pk).add_child(name='Desktop Memory')
    get(node.pk).add_child(name='Laptop Memory')
    get(node.pk).add_child(name='Server Memory')
    print(Category.dump_bulk())

    clist = Category.get_annotated_list()
    print("got %s items in list" % len(clist))
    return render(request, 'treebeard.html', 
        {
            'head': 'Tree Tree 1 2 3', 
            'dump': Category.dump_bulk(),
            'annotated_list': clist
        } )
