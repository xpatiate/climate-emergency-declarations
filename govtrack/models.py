from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

import datetime
import logging
logger = logging.getLogger('cegov')
poplog = logging.getLogger('popcount')


DATE_FORMAT='%Y-%m-%d'
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
            # will have a different area as their 'actual' parent
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

    def declared_population(self, area, total=0):
        if not self.counted:
            self.counted = set()

        poplog.debug("%s,%s,%s" % (total,0,area.name))
        logger.debug("#### COUNTING declared population for %s ####" % area.name)
        logger.debug("#### total %s, already counted: %s" % (total,self.counted))
        if area.is_declared:
            # Check if any descendents are already counted
            current_desc = area.all_descendants
            overlap = current_desc.intersection(self.counted)
            logger.debug("overlap between [%s] and [%s] is [%s]" % (current_desc, self.counted, overlap))

            if not overlap:
                # Current area is declared and has no overlap:
                # - Add self and all descendants (inc indirect) to counted
                self.counted.add(area)
                self.counted.update(area.all_descendants)
                # - Count total population
                logger.debug("%s adding %s to %s" % (area.name,area.population,total))
                total += area.population
                poplog.debug("%s,%s,%s" % (area.population,total,area.name))
            else:
                # Current area is declared and has overlap
                # Figure out which overlapping areas to subtract
                logger.debug("%s is declared but has overlapping descendants" % area.name)
                subtotal = area.population
                # Need to process these subareas as a tree, not a list
                for kid in overlap:
                    if kid in area.all_children:
                        logger.debug("subtracting %s (pop of %s) from subtotal %s" % (kid.population, kid.name, subtotal))
                        subtotal -= kid.population
                logger.debug("total to add for %s is %s" % (area.name, subtotal))
                self.counted.add(area)
                self.counted.update(area.all_descendants)

                total += subtotal
                poplog.debug("%s,%s,%s" % (area.population,total,area.name))
        else:
            # Current area is not declared, look at children
            logger.debug("%s not declared, looking at children" % area.name)
            for child in area.children:
                logger.debug("has %s been counted? %s" % (child, self.counted))
                if child in self.counted:
                    logger.debug("already counted child %s" % child)
                    continue
                total = self.declared_population(child, total)
                logger.debug("after counting %s, counted set is %s" % (child,self.counted))
            logger.debug("Children of %s returned %s" % (area.name, total))
        logger.debug("#### %s returning total of %s ####" % (area.name,total))
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
    description = models.TextField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True)
    links = GenericRelation(Link, null=True, related_query_name='link')

    @classmethod
    def content_type_id(cls):
        return ContentType.objects.get_for_model(cls).pk

    @classmethod
    def find_by_code(cls, country_code):
        return Country.objects.get(country_code=country_code)

    def declarations(self, **kwargs):
        order_by = kwargs.get('order_by')
        order_name = 'area__sort_name'
        if order_by == 'date':
            # XXX ideally pass order_name as well
            # and allow asc/desc
            order_by = 'event_date'
        else:
            order_by = order_name
        filter_args = {
            'status': 'D',
            'area__country': self.id
        }
        before_date = kwargs.get('before')
        if before_date:
            date_obj = None
            try:
                date_obj = datetime.datetime.strptime(before_date, DATE_FORMAT)
            except ValueError as ex:
                pass
            if date_obj:
                filter_args['event_date__lt']=before_date
        after_date = kwargs.get('after')
        if after_date:
            date_obj = None
            try:
                date_obj = datetime.datetime.strptime(after_date, DATE_FORMAT)
            except ValueError as ex:
                pass
            if date_obj:
                filter_args['event_date__gt']=after_date

        dlist = Declaration.objects.filter(**filter_args).order_by(order_by)
        return dlist

    @property
    def declared_population(self):
        try:
            return self.get_root_area().declared_population()
        except AttributeError as ex:
            return 0

    @property
    def num_declarations(self):
        return Declaration.objects.filter(status='D', area__country=self.id).count()

    @property
    def num_structures(self):
        return Structure.objects.filter(country=self.id).count()

    @property
    def num_areas(self):
        return Area.objects.filter(country=self.id).count()

    def get_root_structure(self):
        try:
            return Structure.objects.get(country=self.id, level=1)
        except Structure.DoesNotExist as ex:
            logger.error("no root structure for country %s: %s" % (self.id,self.name))

    def get_root_area(self):
        try:
            return Area.objects.get(country=self.id, structure__level=1)
        except Area.DoesNotExist as ex:
            logger.error("no root area for country %s: %s" % (self.id,self.name))
        return None

    def __str__(self):
        return self.name


class Structure(Hierarchy, models.Model):
    name = models.CharField(max_length=64)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    level = models.PositiveSmallIntegerField()
    parent = models.ForeignKey('self', 
        on_delete=models.CASCADE)
    admin_notes = models.TextField(blank=True)
    links = GenericRelation(Link, null=True, blank=True, related_query_name='link')

    # These two fields currently unused
    count_population = models.BooleanField(default=True)
    is_governing = models.BooleanField(default=True)

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
        children = Structure.objects.filter(parent=self.id).exclude(pk=self.id).order_by('name')
        return children

    @property
    def all_children(self):
        return self.children

    @property
    def records(self):
        records = Area.objects.filter(structure=self.id).order_by('sort_name')
        return records

    @property
    def ancestors(self):
        self.parentlist = [self]
        if (self.id != self.parent_id):
            self.parentlist.insert(0,self.parent)
        self.get_parent(self.parent.id)
        return self.parentlist

    def get_parent(self, parent_id):
        parent = Structure.objects.get(id=parent_id)
        if parent.parent_id != parent_id:
            self.parentlist.insert(0, parent.parent)
            return self.get_parent(parent.parent_id)
    
    @property
    def num_records(self):
        num_records = Area.objects.filter(structure=self.id).count()
        return num_records

    def __str__(self):
        return self.fullname()


class Area(Hierarchy, models.Model):
    name = models.CharField(max_length=64)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    location = models.CharField(max_length=36, null=True, blank=True)
    population = models.PositiveIntegerField(default=0, blank=True, null=True)
    structure = models.ForeignKey(Structure, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('self', 
        on_delete=models.CASCADE)
    supplements = models.ManyToManyField('self',
        symmetrical=False, related_name='supplement',
        blank=True)
    sort_name = models.CharField(max_length=64, null=True, blank=True)
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
        children = Declaration.objects.filter(area=self.id).order_by('event_date')
        return children

    @property
    def linkname(self):
        return 'area'

    def fullname(self):
        return '%s (%s)' % (self.name, self.structure.name)

    @property
    def num_children(self):
        return Area.objects.filter(parent=self.id).exclude(pk=self.id).count()

    @property
    def children(self):
        children = Area.objects.filter(parent=self.id).exclude(pk=self.id).order_by('structure','sort_name')
        return children

    @property
    def indirect_children(self):
        children = Area.objects.filter(supplements=self.id).exclude(pk=self.id).order_by('structure','sort_name')
        return children

    @property
    def num_indirect_children(self):
        return Area.objects.filter(supplements=self.id).exclude(pk=self.id).count()

    @property
    def all_children(self):
        # this alternative method gets *all* children, considering this area
        # both as prime parent and supplementary parent
        combined = Area.objects.filter(
            Q(parent=self.id) | Q(supplements=self.id)
        ).exclude(pk=self.id).order_by('structure','sort_name')
        return combined

    @property
    def num_all_children(self):
        return Area.objects.filter(
            Q(parent=self.id) | Q(supplements=self.id)
        ).exclude(pk=self.id).count()

    @property
    def num_supplementary_children(self):
        return Area.objects.filter(supplements=self.id).exclude(pk=self.id).count()

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
        parent = Area.objects.get(id=parent_id)
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
        area_total = 0
        logger.debug("num declared ancestors for %s is %s" % (self.name, self.num_declared_ancestors()))
        if (self.is_declared and self.num_declared_ancestors() == 0):
            area_total = self.population
        elif (self.num_declared_ancestors() > 1):
            area_total = -1 * (self.num_declared_ancestors() - 1) * self.population
        return area_total

    @property
    def count_population(self):
        return self.structure.count_population

    @property
    def is_governing(self):
        return self.structure.is_governing

    @property
    def level(self):
        return self.structure.level

    @property
    def latest_declaration(self):
        try:
            return Declaration.objects.filter(area=self.id).latest('event_date')
        except Declaration.DoesNotExist as ex:
            pass

    @property
    def is_declared(self):
        # Consider an area to be declared based on the status of its most
        # recent declaration
        latest = self.latest_declaration
        if latest:
            return self.latest_declaration.status == 'D'
        return False

    @property
    def sub_types(self):
        thistype = self.structure
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

    def get_supplement_choices(self, **kwargs):
        exclude_list = [self.id]
        if kwargs.get('exclude'):
            exclude_list.append(kwargs.get('exclude'))
        arealist = Area.objects.filter(
            country_id=self.country.id,
            structure__level__lte=(self.structure.level+1)
            ).exclude(id__in=exclude_list).order_by('structure__level','sort_name')
        return arealist

    def __str__(self):
        return self.fullname()

class Declaration(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    # status types
    DECLARED = 'D'
    INACTIVE = 'N'
    REJECTED = 'R'
    REVOKED = 'V'
    PROGRESS = 'P'
    # Temporary setting - for now we will use declaration to hold information
    # on decisions to reject listing for a government
    # Eventually this data should be moved out into a separate 'decision' object
    LISTING_REJECTED = 'J'
    STATUS_TYPES = [
        (DECLARED, 'Declared'),
        (INACTIVE, 'Inactive'),
        (REJECTED, 'Rejected'),
        (REVOKED, 'Revoked'),
        (PROGRESS, 'In Progress'),
        (LISTING_REJECTED, 'Listing Rejected'),
    ]
    STATUS_MAP = { s[0]: s[1] for s in STATUS_TYPES }
    status = models.CharField(
        max_length=1,
        choices = STATUS_TYPES,
        default=DECLARED,
    )
    event_date = models.DateField(verbose_name='Event date')
    links = GenericRelation(Link, null=True, related_query_name='link')
 
    declaration_type = models.CharField(max_length=256, blank=True)
    description_short = models.CharField(max_length=256, blank=True)
    description_long = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    verified = models.BooleanField(default=False)

    @classmethod
    def content_type_id(cls):
        return ContentType.objects.get_for_model(cls).pk

    @property
    def status_name(self):
        return self.STATUS_MAP[self.status]

    def __str__(self):
        return '%s: %s' % (self.status_name, self.display_event_date())

    @property
    def is_declared(self):
        return self.status == 'D'

    def display_event_date(self):
        ddate = self.event_date
        if ddate:
            return ddate.strftime('%d %B, %Y')

