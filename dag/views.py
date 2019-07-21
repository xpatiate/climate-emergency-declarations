from django.shortcuts import render

from .models import ConcreteNode, ConcreteEdge

# Create your views here.
def index(request):
    dag_list = []
    for i in range(1, 11):
        ConcreteNode(name="%s" % i).save()
    for i in range(1, 11):
        globals()["p%s" % i] = ConcreteNode.objects.get(pk=i)

    # create a graph
    p1.add_child(p5)
    p5.add_child(p7)

    tree = p1.descendants_tree()
    dag_list = ConcreteNode.objects.all()
    return render(request, 'tree.html', { 'dag_list': dag_list} )
