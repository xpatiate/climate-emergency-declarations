from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

import logging
logger = logging.getLogger('govtrack')
poplog = logging.getLogger('popcount')

# Create your models here.

class Hierarchy():
    """Mix-in class to provide tree-related methods."""
    def build_hierarchy(self, itemlist=None):
        if itemlist is None:
            itemlist = []
        if len(itemlist) == 0:
            itemlist = [self]
        for child in self.all_children:
            # Children that are included here via supplementary relationships 
            # will have a different node as their 'actual' parent
            if self != child.parent:
                child.is_supplementary = True
            itemlist.append(child)
            child.build_hierarchy(itemlist) 
        return itemlist

class PopulationCounter():
    """Utility class to perform population counting on tree structures."""

    def __init__(self):
        self.counted = None
        self.count_all = False

    def declared_population(self, node, total=0):
        if not self.counted:
            self.counted = set()

        poplog.debug("%s,%s,%s" % (total,0,node.name))
        logger.debug("#### COUNTING declared population for %s ####" % node.name)
        logger.debug("#### total %s, already counted: %s" % (total,self.counted))
        if node.is_declared:
            # Check if any descendents are already counted
            current_desc = node.all_descendants
            overlap = current_desc.intersection(self.counted)
            logger.debug("overlap between [%s] and [%s] is [%s]" % (current_desc, self.counted, overlap))

            if not overlap:
                # Current node is declared and has no overlap:
                # - Add self and all descendants (inc indirect) to counted
                self.counted.add(node)
                self.counted.update(node.all_descendants)
                # - Count total population
                logger.debug("%s adding %s to %s" % (node.name,node.population,total))
                total += node.population
                poplog.debug("%s,%s,%s" % (node.population,total,node.name))
            else:
                # Current node is declared and has overlap
                # Figure out which overlapping nodes to subtract
                logger.debug("%s is declared but has overlapping descendants" % node.name)
                subtotal = node.population
                # Need to process these subnodes as a tree, not a list
                for kid in overlap:
                    if kid in node.all_children:
                        logger.debug("subtracting %s (pop of %s) from subtotal %s" % (kid.population, kid.name, subtotal))
                        subtotal -= kid.population
                logger.debug("total to add for %s is %s" % (node.name, subtotal))
                self.counted.add(node)
                self.counted.update(node.all_descendants)

                total += subtotal
                poplog.debug("%s,%s,%s" % (node.population,total,node.name))
        else:
            # Current node is not declared, look at children
            logger.debug("%s not declared, looking at children" % node.name)
            for child in node.children:
                logger.debug("has %s been counted? %s" % (child, self.counted))
                if child in self.counted:
                    logger.debug("already counted child %s" % child)
                    continue
                total = self.declared_population(child, total)
                logger.debug("after counting %s, counted set is %s" % (child,self.counted))
            logger.debug("Children of %s returned %s" % (node.name, total))
        logger.debug("#### %s returning total of %s ####" % (node.name,total))
        logger.debug("#### have now counted: %s" % self.counted)
        return total

class Link(models.Model):
    url = models.CharField(max_length=1024)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def html(self):
        return f"<a href='{self.url}'>{self.url}</a>"
    def __str__(self):
        return self.url

class Country(models.Model):
    name = models.CharField(max_length=36)
    region = models.CharField(max_length=36)
    population = models.PositiveIntegerField(default=0)
    country_code = models.CharField(max_length=3)
    links = GenericRelation(Link, null=True, related_query_name='link')

    @classmethod
    def content_type_id(cls):
        return ContentType.objects.get_for_model(cls).pk

    @property
    def declarations(self):
        dlist = Declaration.objects.filter(status='D', node__country=self.id).order_by('node__sort_name')
        return dlist

    @property
    def declared_population(self):
        try:
            return self.get_root_node().declared_population()
        except AttributeError as ex:
            return 0

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
        try:
            return NodeType.objects.get(country=self.id, level=1)
        except NodeType.DoesNotExist as ex:
            logger.error("no root nodetype for country %s: %s" % (self.id,self.name))

    def get_root_node(self):
        try:
            return Node.objects.get(country=self.id, nodetype__level=1)
        except Node.DoesNotExist as ex:
            logger.error("no root node for country %s: %s" % (self.id,self.name))
        return None

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
    links = GenericRelation(Link, null=True, blank=True, related_query_name='link')

    is_supplementary = False

    @classmethod
    def content_type_id(cls):
        return ContentType.objects.get_for_model(cls).pk

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
    area = models.CharField(max_length=36, null=True, blank=True)
    population = models.PositiveIntegerField(default=0, blank=True, null=True)
    nodetype = models.ForeignKey(NodeType, on_delete=models.CASCADE)
    comment_public = models.TextField(null=True, blank=True)
    comment_private = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('self', 
        on_delete=models.CASCADE)
    supplements = models.ManyToManyField('self',
        symmetrical=False, related_name='supplement',
        blank=True)
    sort_name = models.CharField(max_length=64, null=True, blank=True)
    count_population = models.SmallIntegerField(default=0)
    links = GenericRelation(Link, null=True, related_query_name='link')

    parentlist = []
    descendant_list = set()
    is_supplementary = False
    cumulative_pop = 0

    @classmethod
    def content_type_id(cls):
        return ContentType.objects.get_for_model(cls).pk

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
    def indirect_children(self):
        children = Node.objects.filter(supplements=self.id).exclude(pk=self.id).order_by('nodetype','sort_name')
        return children

    @property
    def num_indirect_children(self):
        return Node.objects.filter(supplements=self.id).exclude(pk=self.id).count()

    @property
    def all_children(self):
        # this alternative method gets *all* children, considering this node
        # both as prime parent and supplementary parent
        combined = Node.objects.filter(
            Q(parent=self.id) | Q(supplements=self.id)
        ).exclude(pk=self.id).order_by('nodetype','sort_name')
        logger.debug("all_children: node %s has %s direct or indirect children" % (self.name,len(combined)))
        return combined

    @property
    def num_supplementary_children(self):
        return Node.objects.filter(supplements=self.id).exclude(pk=self.id).count()

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

    def declared_population(self):
        popcounter = PopulationCounter()
        return popcounter.declared_population(self)

    @property
    def descendants(self):
        self.descendant_list = set()
        return self.get_descendants( set() )

    def get_descendants(self, desclist):
        for child in self.children:
            desclist.add(child)
            desclist.update(child.get_descendants(desclist))
        return desclist

    @property
    def all_descendants(self):
        self.descendant_list = set()
        return self.get_all_descendants( set() )

    def get_all_descendants(self, desclist):
        for child in self.all_children:
            desclist.add(child)
            desclist.update(child.get_all_descendants(desclist))
        return desclist

    @property
    def num_indirect_descendants(self):
        return (len(self.all_descendants) - len(self.descendants))

    def num_declared_ancestors(self):
        num_declared = 0
        for parent in self.ancestors:
            if parent == self:
                continue
            if parent.is_declared:
                logger.debug("parent %s is declared" % parent.name)
                num_declared += 1
        return num_declared

    def contribution(self):
        node_total = 0
        logger.debug("num declared ancestors for %s is %s" % (self.name, self.num_declared_ancestors()))
        if (self.is_declared and self.num_declared_ancestors() == 0):
            node_total = self.population
        elif (self.num_declared_ancestors() > 1):
            node_total = -1 * (self.num_declared_ancestors() - 1) * self.population
        return node_total

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

    @property
    def is_counted(self):
        logger.debug("should we count item %s?" % self.name)
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
            logger.debug("yes always count %s" % self.name)
            do_count = True
        elif self.count_population == -1:
            logger.debug("no never count %s" % self.name)
            do_count = False
        else:
            # calculate inherited setting

            # am I declared? If so, then count, unless a parent has
            if self.is_declared:
                logger.debug("Item %s has declared, so will count unless parent has" % self.name)
                do_count = True
                # loop through all parents, see if any have declared
                # get ancestor list, reversed (in asc order) and with self removed
                rev_ancestors = self.ancestors[:-1]
                rev_ancestors.reverse()
                logger.debug('item %s has %s ancestors: %s' % (self.name,len(rev_ancestors), rev_ancestors))
                for parent in rev_ancestors:
                    logger.debug("item %s checking parent %s for inherited setting: %s" % (self.name,parent.name,parent.is_declared))
                    if parent.is_declared:
                        logger.debug("item %s has a declared parent, will not count" % self.name)
                        do_count = False
                        break
                    # If this parent is not declared, go up another level to next parent
                logger.debug("item %s finished parent loop, do count is %s" % (self.name,do_count))
            else:
                do_count = False
            if not do_count:
                logger.debug("No definite value for %s so setting to false" % self.name)
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
    REVOKED = 'V'
    PROVISIONAL = 'P'
    STATUS_TYPES = [
        (DECLARED, 'Declared'),
        (NONDECLARED, 'Non-declared'),
        (REJECTED, 'Rejected'),
        (REVOKED, 'Revoked'),
        (PROVISIONAL, 'Provisional')
    ]
    STATUS_MAP = { s[0]: s[1] for s in STATUS_TYPES }
    status = models.CharField(
        max_length=1,
        choices = STATUS_TYPES,
        default=DECLARED,
    )
    date_declared = models.DateField('date declared')
    links = GenericRelation(Link, null=True, related_query_name='link')
 
    # Should this be a dropdown of defined types?
    # >> How can we record the different ways that climate emergency declaration
    # decisions can be made by a particular node eg. by the legislature or the
    # key administrative decision-maker (collective decision-makers
    # [councils/parliaments] or individuals in the case of ‘elected “monarchs”
    # like presidents or governors or perhaps some mayors?
    declaration_type = models.TextField(blank=True)

    @classmethod
    def content_type_id(cls):
        return ContentType.objects.get_for_model(cls).pk

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

