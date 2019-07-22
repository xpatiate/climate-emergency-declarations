from django.db import models
from django.db.models import Q

import logging

# Create your models here.

class Hierarchy():
    """Mix-in class to provide tree-related methods."""
    def build_hierarchy(self, itemlist=None):
        if itemlist is None:
            itemlist = []
        if len(itemlist) == 0:
            itemlist = [self]
        for child in self.children:
            child.current_parent = self
            itemlist.append(child)
            child.build_hierarchy(itemlist) 
        return itemlist

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
        return self.get_root_node().declared_population()

    @property
    def num_declarations(self):
        return Declaration.objects.filter(status='D', node__country=self.id).count()

    @property
    def num_nodetypes(self):
        return NodeType.objects.filter(country=self.id).count()

    @property
    def num_nodes(self):
        return Node.objects.filter(country=self.id).count()

    def get_root_nodetype(self):
        return NodeType.objects.get(country=self.id, level=1)

    def get_root_node(self):
        return Node.objects.get(country=self.id, nodetype__level=1)

    def __str__(self):
        return self.name


class NodeType(Hierarchy, models.Model):
    name = models.CharField(max_length=64)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    level = models.PositiveSmallIntegerField()
    parent = models.ForeignKey('self', 
        on_delete=models.CASCADE)
    count_population = models.BooleanField(default=True)
    is_governing = models.BooleanField(default=True)

    current_parent = None

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
        children = NodeType.objects.filter(parent=self.id).exclude(pk=self.id).order_by('name')
        return children

    @property
    def all_children(self):
        return self.children

    @property
    def this_parent(self):
        return self.parent

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


class Node(Hierarchy, models.Model):
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
    parent = models.ForeignKey('self', 
        on_delete=models.CASCADE)
    supplements = models.ManyToManyField('self',
        symmetrical=False, related_name='supplement',
        null=True, blank=True)
    sort_name = models.CharField(max_length=64, null=True, blank=True)
    count_population = models.SmallIntegerField(default=0)

    parentlist = []
    current_parent = None

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
    def num_children(self):
        return Node.objects.filter(parent=self.id).exclude(pk=self.id).count()

    @property
    def children(self):
        children = Node.objects.filter(parent=self.id).exclude(pk=self.id).order_by('nodetype','sort_name')
        return children

    @property
    def all_children(self):
        # this alternative method gets *all* children, considering this node
        # both as prime parent and supplementary parent
        combined = Node.objects.filter(
            Q(parent=self.id) | Q(supplements=self.id)
        ).exclude(pk=self.id).order_by('nodetype','sort_name')
        return combined

    @property
    def this_parent(self):
        if self.current_parent:
            return self.current_parent
        return self.parent

    @property
    def ancestors(self):
        self.parentlist = [self]
        if (self.id != self.parent_id):
            self.parentlist.insert(0,self.parent)
        self.get_parent(self.parent.id)
        for s in self.supplements.all():
            if s not in self.parentlist:
                self.parentlist.insert(0,s)
                self.get_parent(s.id)
        return self.parentlist

    def get_parent(self, parent_id):
        parent = Node.objects.get(id=parent_id)
        if parent.parent_id != parent_id:
            self.parentlist.insert(0, parent.parent)
            return self.get_parent(parent.parent_id)

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

    def declared_population(self, total=0):
        if self.is_counted:
            logging.debug("%s adding %s to %s" % (self.name,self.population,total))
            total += self.population
        else:
            for child in self.children:
                total = child.declared_population(total)
        logging.debug("%s returning total of %s" % (self.name,total))
        return total

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

    def get_supplement_choices(self):
        return Node.objects.filter(
            country_id=self.country.id,
            nodetype__level__lte=(self.nodetype.level+1)
            ).exclude(pk=self.id).order_by('nodetype__level','sort_name')


    def __str__(self):
        return self.fullname()

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

