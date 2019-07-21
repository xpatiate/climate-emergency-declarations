from django.db import models

from django.forms import ModelForm
import django.forms as forms

import logging
from .utils import make_hierarchy

# Create your models here.

class Country(models.Model):
    name = models.CharField(max_length=36)
    region = models.CharField(max_length=36)
    population = models.PositiveIntegerField(default=0)
    country_code = models.CharField(max_length=3)

    @property
    def declarations(self):
        dlist = Declaration.objects.filter(status='D', node__country=self.id).order_by('node__sort_name')
        return dlist

    @property
    def declared_population(self):
        dlist = Declaration.objects.filter(status='D', node__country=self.id).order_by('node__nodetype__level','node__sort_name')
        nodes = set([d.node for d in dlist])
        records = make_hierarchy(nodes, set())

        total_pop = 0
        for item in records:
            if item.is_counted:
                total_pop += item.population
        return total_pop
            

        def __str__(self):
            return self.name


class NodeType(models.Model):
    name = models.CharField(max_length=64)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    level = models.PositiveSmallIntegerField()
    parent = models.ForeignKey('self', 
        on_delete=models.CASCADE)
    count_population = models.BooleanField(default=True)
    is_governing = models.BooleanField(default=True)

    def fullname(self):
        name = ''
        if (self.level > 1):
            # will need to recurse here for multiple levels
            myparent = self.parent
            name = '%s | %s: %s ' % (self.country.name, myparent.name, self.name)
        else:
            name = '%s | %s' % (self.country.name, self.name)
        return name

    @property
    def children(self):
        children = NodeType.objects.filter(parent=self.id).exclude(pk=self.id).order_by('level','name')
        return children

    @property
    def records(self):
        records = Node.objects.filter(nodetype=self.id).order_by('sort_name')
        return records

    @property
    def ancestors(self):
        self.parentlist = [self]
        if (self.id != self.parent_id):
            self.parentlist.insert(0,self.parent)
        self.get_parent(self.parent.id)
        return self.parentlist

    def get_parent(self, parent_id):
        parent = NodeType.objects.get(id=parent_id)
        if parent.parent_id != parent_id:
            self.parentlist.insert(0, parent.parent)
            return self.get_parent(parent.parent_id)
    
    @property
    def num_records(self):
        num_records = Node.objects.filter(nodetype=self.id).count()
        return num_records

    def __str__(self):
        return self.fullname()


class Node(models.Model):
    name = models.CharField(max_length=64)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    # Leave this in the model for now, but currently unused - 
    # nodetype structure should give enough geographical context
    area = models.CharField(max_length=36, blank=True, null=True)
    population = models.PositiveIntegerField(default=0, blank=True, null=True)
    nodetype = models.ForeignKey(NodeType, on_delete=models.CASCADE)
    reference_links = models.TextField(null=True, blank=True)
    comment_public = models.TextField(null=True, blank=True)
    comment_private = models.TextField(null=True, blank=True)
    parents = models.ManyToManyField('self', symmetrical=False)
        #on_delete=models.CASCADE)
    sort_name = models.CharField(max_length=64, null=True, blank=True)
    count_population = models.SmallIntegerField(default=0)

    parentlist = []

    def save(self, *args, **kwargs):
        if not self.sort_name:
            self.sort_name = self.name
        super().save(*args, **kwargs)

    @property
    def declarations(self):
        children = Declaration.objects.filter(node=self.id).order_by('date_declared')
        return children

    @property
    def linkname(self):
        return 'node'

    def fullname(self):
        return '%s (%s)' % (self.name, self.nodetype.name)

    @property
    def children(self):
        children = Node.objects.filter(parents__id=self.id).exclude(pk=self.id).order_by('nodetype__level','sort_name')
        return children

    """
    Problem with trying to allow nodes to have multiple parents
    is that it makes a tree structure very difficult
    Can't create a simple hierarchy of ancestors

    What if we kept each node with a single main parent
    but also added an optional extra parent?
    Like saying "this is my proper place in the tree, but when doing population
    count, also take this other parent into account"
    Safe enough to assume there wouldn't be nodes that have more than two parents?

    If we did that how would population counting work?
    Suppose we are drawing up the England tree and calculating cumulative population
    Get to Southwest region first, go thru ceremonial counties
    Bath & North East Somerset:
        * is declared
        * main parent is Somerset (ceremonial), not declared
        * other parent is West England Combined, which is declared but not counted yet
        * so count West England Combined, not this one
    Bristol 
        * is declared
        * main parent is Southwest Region (ceremonial), not declared
        * other parent is West England Combined, which is declared and counted 
        * so do not count this one
    South Gloucestershire:
        * is not declared
        * so no need to check parents
    West England Combined Authority
        * is declared
        * is already counted
    
    Another question for Philip: do we store accurate population for each node?
    Or in some cases should we be calculating population by totalling sub-nodes?
    
    
    """
    @property
    def ancestors(self):
        self.parentlist = [self]
        for p in self.parents.all():
            if (self.id != p.id):
                self.parentlist.insert(0,p)
                self.get_parent(p.id)
        return self.parentlist

    def get_parent(self, parent_id):
        parent = Node.objects.get(id=parent_id)
        for p in parent.parents.all():
            if p.id != parent_id:
                self.parentlist.insert(0, p)
                self.get_parent(p.id)

    @property
    def level(self):
        return self.nodetype.level

    @property
    def latest_declaration(self):
        try:
            return Declaration.objects.filter(node=self.id).latest('date_declared')
        except Declaration.DoesNotExist as ex:
            pass

    @property
    def is_declared(self):
        # Consider a node to be declared based on the status of its most
        # recent declaration
        latest = self.latest_declaration
        if latest:
            return self.latest_declaration.status == 'D'
        return False

    @property
    def sub_types(self):
        thistype = self.nodetype
        typekids = thistype.children
        return typekids

    def total_population(self):
        for child in self.children:
            # is child a node or a govt?
            # if govt, has it declared?
            # if not declared, recurse
            pass

    @property
    def is_counted(self):
        logging.debug("should we count item %s?" % self.id)
        # count population if:
            # count setting is true (always count)
            # OR
            # count setting is inherit
                # AND
                # this govt has declared
                    # AND
                    # none above it have
        do_count = None
        if self.count_population == 1:
            logging.debug("yes always count %s" % self.id)
            do_count = True
        elif self.count_population == -1:
            logging.debug("no never count %s" % self.id)
            do_count = False
        else:
            # calculate inherited setting

            # am I declared? If so, then count, unless a parent has
            if self.is_declared:
                logging.debug("Item %s has declared, so will count unless parent has" % self.id)
                do_count = True
                # loop through all parents, see if any have declared
                # get ancestor list, reversed (in asc order) and with self removed
                rev_ancestors = self.ancestors[:-1]
                rev_ancestors.reverse()
                logging.debug('item %s has %s ancestors: %s' % (self.id,len(rev_ancestors), rev_ancestors))
                for parent in rev_ancestors:
                    logging.debug("item %s checking parent %s for inherited setting: %s" % (self.id,parent.id,parent.is_declared))
                    if parent.is_declared:
                        logging.debug("item %s has a declared parent, will not count" % self.id)
                        do_count = False
                        break
                    # If this parent is not declared, go up another level to next parent
                logging.debug("item %s finished parent loop, do count is %s" % (self.id,do_count))
            else:
                do_count = False
            if not do_count:
                logging.debug("No definite value for %s so setting to false" % self.id)
                do_count = False
        return do_count

    def __str__(self):
        return '%s | %s' % (self.country.name, self.name)

class Declaration(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    # status types
    DECLARED = 'D'
    NONDECLARED = 'N'
    REJECTED = 'R'
    PROVISIONAL = 'P'
    STATUS_TYPES = [
        (DECLARED, 'Declared'),
        (NONDECLARED, 'Non-declared'),
        (REJECTED, 'Rejected'),
        (PROVISIONAL, 'Provisional')
    ]
    STATUS_MAP = { s[0]: s[1] for s in STATUS_TYPES }
    status = models.CharField(
        max_length=1,
        choices = STATUS_TYPES,
        default=DECLARED,
    )
    date_declared = models.DateField('date declared', null=True, blank=True)
    declaration_links = models.TextField(null=True, blank=True)
    # Should this be a dropdown of defined types?
    # >> How can we record the different ways that climate emergency declaration
    # decisions can be made by a particular node eg. by the legislature or the
    # key administrative decision-maker (collective decision-makers
    # [councils/parliaments] or individuals in the case of ‘elected “monarchs”
    # like presidents or governors or perhaps some mayors?
    declaration_type = models.TextField(null=True, blank=True)

    @property
    def status_name(self):
        return self.STATUS_MAP[self.status]

    def __str__(self):
        return '%s: %s' % (self.status_name, self.display_date_declared())

    @property
    def is_declared(self):
        return self.status == 'D'

    def display_date_declared(self):
        ddate = self.date_declared
        if ddate:
            return ddate.strftime('%d %B, %Y')

class NodeTypeForm(ModelForm):
    class Meta:
        model = NodeType
        fields = ['name','country','level','parent', 'is_governing']
        widgets = {
            'country': forms.HiddenInput(),
            'level': forms.HiddenInput(),
            'parent': forms.HiddenInput()
            }

class NodeForm(ModelForm):
    class Meta:
        model = Node
        fields = ['name','sort_name','nodetype','country','population','parents','comment_public','comment_private','reference_links']
        widgets = {
            'nodetype': forms.HiddenInput(),
            #'parents': forms.HiddenInput(),
            'country': forms.HiddenInput()
        }

class DeclarationForm(NodeForm):
    class Meta:
        model = Declaration
        fields = ['node','status', 'date_declared', 'declaration_links', 'declaration_type']
        widgets = {
            'node': forms.HiddenInput(),
        }

    date_declared = forms.DateField(input_formats=['%Y-%m-%d'])
