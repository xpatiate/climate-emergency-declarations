from django.db import models
from model_utils.managers import InheritanceManager

from django.forms import ModelForm
import django.forms as forms

import logging

# Create your models here.

class Country(models.Model):
    name = models.CharField(max_length=36)
    region = models.CharField(max_length=36)
    population = models.PositiveIntegerField(default=0)
    country_code = models.CharField(max_length=3)

    def __str__(self):
        return self.name


class NodeType(models.Model):
    name = models.CharField(max_length=64)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    level = models.PositiveSmallIntegerField()
    parent = models.ForeignKey('self', 
        on_delete=models.CASCADE)
    count_population = models.BooleanField(default=True)

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
        records = Node.objects.filter(nodetype=self.id).order_by('name')
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
    # should this be a lookup? or better as arbitrary text? or both
    # -> dropdown of existing areas for country, or add new
    area = models.CharField(max_length=36, blank=True, null=True)
    population = models.PositiveIntegerField(default=0, blank=True, null=True)
    nodetype = models.ForeignKey(NodeType, on_delete=models.CASCADE)
    reference_links = models.TextField(null=True, blank=True)
    comment_public = models.TextField(null=True, blank=True)
    comment_private = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('self', 
        on_delete=models.CASCADE)
    is_governing = models.BooleanField(default=True)
    sort_name = models.CharField(max_length=64, null=True, blank=True)
    count_population = models.SmallIntegerField(default=0)

    objects = InheritanceManager()
    parentlist = []

    @property
    def linkname(self):
        return 'node'

    def fullname(self):
        return '%s (%s)' % (self.name, self.nodetype.name)

    @property
    def children(self):
        children = Node.objects.filter(parent=self.id).exclude(pk=self.id).select_subclasses().order_by('nodetype__level','name')
        return children

    @property
    def ancestors(self):
        self.parentlist = [self]
        if (self.id != self.parent_id):
            self.parentlist.insert(0,self.myparent)
        self.get_parent(self.parent.id)
        return self.parentlist

    @property
    def myparent(self):
        #return self.parent
        return Node.objects.get_subclass(id=self.parent_id)

    def get_parent(self, parent_id):
        parent = Node.objects.get_subclass(id=parent_id)
        if parent.parent_id != parent_id:
            self.parentlist.insert(0, parent.myparent)
            return self.get_parent(parent.parent_id)

    @property
    def level(self):
        return self.nodetype.level

    @property
    def is_declared(self):
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
        # should we separate population summary from delcaration status
        # i.e. do we need to count population regardless of declarations?

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

class Government(Node):
    # status types
    DECLARED = 'D'
    NONDECLARED = 'N'
    PARTIAL = 'P'
    STATUS_TYPES = [
        (DECLARED, 'Declared'),
        (NONDECLARED, 'Non-declared'),
        (PARTIAL, 'In Progress')
    ]
    status = models.CharField(
        max_length=1,
        choices = STATUS_TYPES,
        default=NONDECLARED
    )
    date_declared = models.DateField('date declared', null=True, blank=True)
    declaration_links = models.TextField(null=True, blank=True)

    def __str__(self):
        return '%s | %s' % (self.country.name, self.name)

    @property
    def is_declared(self):
        return self.status == 'D'

    @property
    def linkname(self):
        return 'govt'

    def display_date_declared(self):
        ddate = self.date_declared
        if ddate:
            return ddate.strftime('%d %B, %Y')

class NodeTypeForm(ModelForm):
    class Meta:
        model = NodeType
        fields = ['name','country','level','parent']
        widgets = {
            'country': forms.HiddenInput(),
            'level': forms.HiddenInput(),
            'parent': forms.HiddenInput()
            }

class NodeForm(ModelForm):
    class Meta:
        model = Node
        fields = ['name','nodetype','country','area','population','parent','is_governing','sort_name','comment_public','comment_private','reference_links']
        widgets = {
            'nodetype': forms.HiddenInput(),
            'parent': forms.HiddenInput(),
            'country': forms.HiddenInput()
        }

class GovtForm(NodeForm):
    class Meta:
        model = Government
        fields = ['name','nodetype','country','area','population','parent','is_governing', 'sort_name', 'comment_public','comment_private','reference_links', 'status', 'date_declared', 'declaration_links']
        widgets = {
            'nodetype': forms.HiddenInput(),
            'parent': forms.HiddenInput(),
            'country': forms.HiddenInput(),
        }

    date_declared = forms.DateField(input_formats=['%Y-%m-%d'])
