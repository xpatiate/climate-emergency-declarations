from django.db import models

from django.db.models import CharField
from django.shortcuts import render_to_response
from django.core.exceptions import ValidationError
from django_dag.models import node_factory, edge_factory
from django_dag.tree_test_output import expected_tree_output

# Create your models here.
class ConcreteNode(node_factory('ConcreteEdge')):
    """
    Test node, adds just one field
    """
    name = CharField(max_length=32)

    def __str__(self):
        return '# %s' % self.name


class ConcreteEdge(edge_factory('ConcreteNode', concrete=False)):
    """
    Test edge, adds just one field
    """
    name = CharField(max_length=32, blank=True, null=True)

