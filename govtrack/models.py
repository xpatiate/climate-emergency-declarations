from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
import django.urls

import boto3
import json
import datetime
import logging
import os

logger = logging.getLogger('cegov')
poplog = logging.getLogger('popcount')

DATE_FORMAT = '%Y-%m-%d'
# Create your models here.

class Hierarchy():
    '''Mix-in class to provide tree-related methods.'''
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
                child.override_indent_level = self.indent_level + 1
            #if self.is_supplementary:
            #    child.is_supplementary = True
            itemlist.append(child)
            if not child.is_supplementary:
                child.build_hierarchy(itemlist)
        return itemlist

class PopulationCounter():
    '''Utility class to perform population counting on tree structures.'''

    def declared_population(self, area, date=None):
        count = []
        declared_aggloms = []
        total = 0
        area.proxy_declared = False
        queue = [area]
        while queue:
            this = queue.pop(0)
            is_agglom = Area.objects.filter(supplements=this.id).exists()
            try:
                this.proxy_declared
            except AttributeError:
                this.proxy_declared = False
                for parent in [*Area.objects.filter(supplement=this.id), this.parent]:
                    if parent.id in declared_aggloms or parent.is_declared_at(date):
                        this.proxy_declared = True
            would_count = this.proxy_declared or this.is_declared_at(date)
            if would_count and not is_agglom:
                count.append(this)
            if would_count and is_agglom:
                declared_aggloms.append(this.id)
            if not would_count or would_count and is_agglom:
                for child in this.children:
                    queue.append(child)
        
        for counted in count:
            total += counted.population
        
        return total

class Link(models.Model):
    url = models.CharField(max_length=1024)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def html(self):
        return f'<a href=\'{self.url}\'>{self.url}</a>'
    
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
    popcount_ready = models.PositiveSmallIntegerField(default=0)
    popcount_since = models.DateField(null=True, blank=True)
    # redundant field for perf reasons,
    # equal to self.popcounts.latest('date').population
    current_popcount = models.PositiveIntegerField(default=0)


    @classmethod
    def content_type_id(cls):
        return ContentType.objects.get_for_model(cls).pk

    @classmethod
    def find_by_code(cls, country_code):
        logger.info(f"Looking up country with code {country_code}")
        return Country.objects.get(country_code=country_code)

    @property
    def api_link(self):
        return django.urls.reverse('api_country_population', args=[self.country_code])

    @property
    def api_recount_link(self):
        return django.urls.reverse('api_country_trigger_recount', args=[self.country_code])

    @property
    def earliest_declaration(self):
        fromdate = None
        filter_args = {
            'status': 'D',
            'area__country': self.id,
        }
        decs = Declaration.objects.filter(**filter_args).order_by('-event_date')
        if decs:
            fromdate=decs.latest('-event_date').event_date
        return fromdate

    def active_declarations(self, **kwargs):
        '''Return a list of declarations for a country which are active
        at a specified (or current) date.'''

        as_at_date = kwargs.get('date', datetime.date.today())
        filter_args = {
            'status': 'D',
            'area__country': self.id,
            'event_date__lt': as_at_date,
        }
        areas_declared = set()
        dlist = Declaration.objects.filter(**filter_args).order_by('-event_date')
        active = []
        for dec in dlist:
            # only show the latest active declaration for an area
            if dec.is_active_at_date(as_at_date):
                if not dec.area in areas_declared:
                    active.insert(0,dec)
                    areas_declared.add(dec.area)
        return active

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
    def num_declarations(self):
        return len(self.active_declarations())

    @property
    def declared_population(self):
        try:
            return self.get_root_area().declared_population()
        except AttributeError as ex:
            return 0

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
            logger.error('no root structure for country %s: %s' % (self.id,self.name))

    def get_root_area(self):
        try:
            return Area.objects.get(country=self.id, structure__level=1)
        except Area.DoesNotExist as ex:
            logger.error('no root area for country %s: %s' % (self.id,self.name))
        return None

    @property
    def popcounts(self):
        return PopCount.objects.filter(country=self).order_by('date')

    @property
    def not_current_popcount(self):
        try:
            latest = self.popcounts.latest('date')
            return latest.population
        except PopCount.DoesNotExist as ex:
            pass
        return 0

    def popcount_update_needed(self, since=None):
        logger.info(f"Need an update for {self.country_code}?")
        if self.num_declarations > 0:
            logger.info("yep")
            self.popcount_ready = 0
            self.popcount_needed_since(since)
            self.save()

    def popcount_update_running(self):
        self.popcount_ready = 2
        self.save()

    def popcount_update_complete(self):
        self.popcount_ready = 1
        self.popcount_since = self.earliest_declaration
        self.save()

    # Keep track of the earliest date that a popcount is needed from
    def popcount_needed_since(self, since=None):
        if not since:
            since = self.earliest_declaration
        if not self.popcount_since or self.popcount_since > since:
            self.popcount_since = since

    @property
    def is_popcount_needed(self):
        return self.popcount_ready == 0

    @property
    def is_popcount_running(self):
        return self.popcount_ready == 2

    def trigger_population_recount(self):
        # mark as update in progress
        self.popcount_update_running()

        aws_region=os.environ.get('AWS_REGION', '')
        aws_lambda=os.environ.get('AWS_LAMBDA_NAME', '')
        response = {'errstr': 'cannot trigger recount'}
        since_date_str = ''
        if aws_region and aws_lambda:
            # create lambda client
            client = boto3.client('lambda',
                region_name=aws_region,
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
                )
            logger.info(f"client {client}")
            if self.popcount_since:
                since_date_str = self.popcount_since.isoformat()

            if client:
                payload = {
                    'task': 'generate_timeline',
                    'country_code': self.country_code,
                    'since_date': since_date_str
                    }
                logger.info(f"payload {payload}")
                l_response = client.invoke(
                    FunctionName=aws_lambda,
                    InvocationType='Event',
                    Payload=json.dumps(payload)
                    )
                logger.info(f"response {l_response}")
                response = l_response.get('ResponseMetadata')
        else:
            logger.info(f"AWS details [{aws_region}] [{aws_lambda}] not specified, running locally")
            self.generate_population_count(since_date_str)
            response = {"complete": 1}
        return response


    def generate_population_count(self, fromdate=None):
        '''Recalculate all stored population counts from the given date onwards.'''
        logger.info('Counting population update from %s' % fromdate)
        start_time = datetime.datetime.now()
        filter_args = {
            'country': self,
        }
        if fromdate:
            filter_args['date__gte'] = fromdate

        # delete any popcounts after this point
        existing_popcounts = PopCount.objects.filter(**filter_args)
        logger.info('going to delete %s existing popcounts' % len(existing_popcounts))
        existing_popcounts.delete()

        # find declarations for this country, only of status D or V
        filter_args = {
            'area__country': self.id,
            'status__in': Declaration.POPULATION_STATUS.keys()
        }
        if fromdate:
            filter_args['event_date__gte'] = fromdate
        future_decs = Declaration.objects.filter(**filter_args).order_by('event_date')
        logger.info('got %s declarations' % len(future_decs))

        # Make a dict of the unique dates for all declarations,
        # and the declarations linked to each date
        date_dict = { str(d.event_date): [] for d in future_decs }
        for d in future_decs:
            date_dict[str(d.event_date)].append(d)
        change_dates = sorted(date_dict.keys())
        logger.info('got change dates: %s' % change_dates)

        root = self.get_root_area()
        latest = 0
        for cdate in change_dates:
            # Calculate the population as at this date
            pc = PopulationCounter()
            date_pop = pc.declared_population(root, date=cdate)
            logger.info(f"pop at date {cdate} is {date_pop}")
            # Note we add a unique popcount for each declaration on this date,
            # but they all have the same population,
            # because we can't break down population change by declaration at this stage
            for decln in date_dict[cdate]:
                pop = PopCount.create(self, decln, date_pop)
                latest = pop.population

        self.current_popcount = latest
        end_time = datetime.datetime.now()
        delta = str(end_time - start_time)
        logger.info(f"Popcount for {self.country_code} took {delta}")

        # mark as update complete
        self.popcount_update_complete()

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

    @property
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
    def num_areas(self):
        num_areas = Area.objects.filter(structure=self.id).count()
        return num_areas

    @property
    def indent_level(self):
        return max(0, self.level - 1)

    def __str__(self):
        return self.fullname

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
    agglomeration = models.BooleanField(default=False)
    supplements = models.ManyToManyField('self',
        symmetrical=False, related_name='supplement',
        blank=True)
    sort_name = models.CharField(max_length=64, null=True, blank=True)
    links = GenericRelation(Link, null=True, related_query_name='link')

    __original_population = None

    parentlist = []
    descendant_list = set()
    is_supplementary = False
    cumulative_pop = 0
    override_indent_level = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_population = self.population

    @classmethod
    def content_type_id(cls):
        return ContentType.objects.get_for_model(cls).pk

    def save(self, *args, **kwargs):
        if not self.sort_name:
            self.sort_name = self.name
        
        changed_pop = False
        if self.population != self.__original_population:
            changed_pop = True
        
        super().save(*args, **kwargs)
        self.__original_population = self.population

        if changed_pop:
            self.country.popcount_update_needed()

    @property
    def declarations(self):
        children = Declaration.objects.filter(area=self.id).order_by('event_date')
        return children
    
    @property
    def linkname(self):
        return 'area'

    @property
    def fullname(self):
        return '%s' % self.name

    @property
    def supplement_list(self):
        return ', '.join(sorted([s.name for s in self.supplements.all()]))

    @property
    def num_children(self):
        return Area.objects.filter(parent=self.id).exclude(pk=self.id).count()

    @property
    def children(self):
        children = Area.objects.filter(parent=self.id).exclude(pk=self.id).order_by('structure', 'sort_name')
        return children

    def regen_from_oldest_dec(self):
        decs = self.declarations
        if decs:
            self.country.generate_population_count(fromdate=decs.latest('-event_date').event_date)

    @property
    def indirect_children(self):
        children = Area.objects.filter(supplements=self.id).exclude(pk=self.id).order_by('structure', 'sort_name')
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
        ).distinct().exclude(pk=self.id).order_by('structure', 'sort_name')
        return combined

    @property
    def num_all_children(self):
        return Area.objects.filter(
            Q(parent=self.id) | Q(supplements=self.id)
        ).distinct().exclude(pk=self.id).count()

    @property
    def num_supplementary_children(self):
        return Area.objects.filter(supplements=self.id).exclude(pk=self.id).count()

    @property
    def ancestors(self):
        self.parentlist = set([self])
        if (self.id != self.parent_id):
            self.parentlist.add(self.parent)
        self.get_parent(self.parent.id)
        for s in self.supplements.all():
            if s not in self.parentlist:
                self.parentlist.add(s)
                self.get_parent(s.id)
        return self.parentlist

    def get_parent(self, parent_id):
        parent = Area.objects.get(id=parent_id)
        if parent.parent_id != parent_id:
            self.parentlist.add( parent.parent)
            self.get_parent(parent.parent_id)
        for s in parent.supplements.all():
            if s not in self.parentlist:
                self.parentlist.add(s)
                self.get_parent(s.id)
        return self.parentlist

    @property
    def direct_ancestors(self):
        self.direct_parentlist = [self]
        if (self.id != self.parent_id):
            self.direct_parentlist.append(self.parent)
        self.get_direct_parent(self.parent.id)
        return self.direct_parentlist

    def get_direct_parent(self, parent_id):
        parent = Area.objects.get(id=parent_id)
        if parent.parent_id != parent_id:
            self.direct_parentlist.append( parent.parent)
            self.get_direct_parent(parent.parent_id)
        return self.direct_parentlist

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

    def num_declared_ancestors(self, dec_date=None):
        num_declared = 0
        for parent in self.ancestors:
            if parent == self:
                continue
            if parent.is_declared_at(dec_date):
                logger.debug('parent %s is declared at %s' % (parent.name, dec_date))
                num_declared += 1
        return num_declared

    def contribution(self):
        area_total = 0
        num_dec_anc = self.num_declared_ancestors()
        poplog.info('num declared ancestors for %s is %s' % (self.name, num_dec_anc))
        # This area is declared and nothing above it has declared
        if (self.is_declared and num_dec_anc == 0):
            poplog.info('%s is declared and has no declared ancestors' % self.name)
            area_total = self.population
        # Multiple areas above this one have declared
        elif (num_dec_anc > 1):
            poplog.info('%s has %s declared ancestors' % (self.name, num_dec_anc))
            area_total = -1 * (num_dec_anc - 1) * self.population
        else:
            poplog.info('%s has exactly 1 declared ancestor' % self.name)
        poplog.info('so %s contribution is %s' % (self.name, area_total))
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
    def indent_level(self):
        if self.override_indent_level:
            return self.override_indent_level
        return self.structure.indent_level

    @property
    def api_link(self):
        return django.urls.reverse('api_area_data', args=[self.id])

    @property
    def latest_declaration(self):
        try:
            return self.declarations.latest('event_date')
        except Declaration.DoesNotExist as ex:
            pass

    @property
    def latest_declaration_date(self):
        dec = self.latest_declaration
        decdate = ''
        if dec:
            decdate = dec.display_event_date()
        return decdate

    @property
    def is_declared(self):
        '''Return true if the Area's most recent declaration, at the current date,
        is DECLARED.'''
        # Consider an area to be declared based on the status of its most
        # recent declaration
        latest = self.latest_declaration
        if latest:
            return self.latest_declaration.status == 'D'
        return False

    def is_declared_at(self, dec_date):
        '''Return true if the Area's most recent declaration, at the given date,
        is DECLARED.'''
        if not dec_date:
            return self.is_declared

        latest_dec = None
        try:
            latest_dec = self.declarations.filter(event_date__lte=dec_date).latest('event_date')
        except ValidationError as ex:
            logger.error('invalid date: %s' % dec_date)
        except Declaration.DoesNotExist as ex:
            pass
        if latest_dec:
            return latest_dec.status == 'D'
        return False

    @property
    def sub_types(self):
        thistype = self.structure
        typekids = thistype.children
        return typekids

    @property
    def skip_is_counted(self):
        logger.debug('should we count item %s?' % self.name)
        # count population if:
            # count setting is true (always count)
            # OR
            # count setting is inherit
                # AND
                # this govt has declared
                    # AND
                    # none above it have
        do_count = None

        # am I declared? If so, then count, unless a parent has
        if self.is_declared:
            logger.debug('Item %s has declared, so will count unless parent has' % self.name)
            do_count = True
            # loop through all parents, see if any have declared
            # get ancestor list, reversed (in asc order) and with self removed
            rev_ancestors = self.ancestors[:-1]
            rev_ancestors.reverse()
            logger.debug('item %s has %s ancestors: %s' % (self.name,len(rev_ancestors), rev_ancestors))
            for parent in rev_ancestors:
                logger.debug('item %s checking parent %s for inherited setting: %s' % (self.name,parent.name,parent.is_declared))
                if parent.is_declared:
                    logger.debug('item %s has a declared parent, will not count' % self.name)
                    do_count = False
                    break
                # If this parent is not declared, go up another level to next parent
            logger.debug('item %s finished parent loop, do count is %s' % (self.name,do_count))
        else:
            do_count = False
        if not do_count:
            logger.debug('No definite value for %s so setting to false' % self.name)
            do_count = False

        return do_count

    def get_supplement_choices(self, **kwargs):
        exclude_list = [self.id]
        if kwargs.get('exclude'):
            exclude_list.append(kwargs.get('exclude'))
        arealist = Area.objects.filter(
            country_id=self.country.id,
            #structure__level__lte=(self.structure.level+1)
            agglomeration=True,
            ).exclude(id__in=exclude_list).order_by('sort_name')
        return arealist

    def add_link(self, url):
        link_urls = self.links.values_list('url', flat=True)
        if url not in link_urls:
            self.links.create(url=url)

    def __str__(self):
        return self.fullname

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
    LISTING_UNDER_REVIEW = 'U'
    STATUS_TYPES = [
        (DECLARED, 'Declared'),
        (INACTIVE, 'Inactive'),
        (REJECTED, 'Rejected'),
        (REVOKED, 'Revoked'),
        (PROGRESS, 'In Progress'),
        (LISTING_REJECTED, 'Listing Rejected'),
        (LISTING_UNDER_REVIEW, 'Listing Under Review'),
    ]
    STATUS_MAP = { s[0]: s[1] for s in STATUS_TYPES }
    # These status values can affect population counts -
    # other types of status are tracked but are not included in counts
    POPULATION_STATUS = {
        'D': True,
        'V': True
    }

    status = models.CharField(
        max_length=1,
        choices=STATUS_TYPES,
        default=DECLARED,
    )
    event_date = models.DateField(verbose_name='Event date')
    links = GenericRelation(Link, null=True, related_query_name='link')
    declaration_type = models.CharField(max_length=256, blank=True)
    description_short = models.CharField(max_length=256, blank=True)
    description_long = models.TextField(blank=True)
    key_contact = models.CharField(max_length=128, blank=True)
    admin_notes = models.TextField(blank=True)
    verified = models.BooleanField(default=False)

    @classmethod
    def content_type_id(cls):
        return ContentType.objects.get_for_model(cls).pk
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__event_date = self.event_date
        self.__status = self.status

    def save(self, *args, **kwargs):
        new = False
        if not self.pk:
            new = True

        changed = False
        if self.event_date != self.__event_date or self.status != self.__status:
            changed = True

        super().save(*args, **kwargs)
        self.__event_date = self.event_date

        if changed:
            self.area.country.popcount_update_needed(self.event_date)

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

    def is_currently_active(self):
        if self.is_declared:
            return self.is_active_at_date(datetime.date.today())
        return False

    @property
    def affects_population_count(self):
        '''Return true if this declaration status will potentially alter
        population counts (only Declared or Revoked)'''
        return self.POPULATION_STATUS.get(self.status)

    def is_active_at_date(self, date):
        siblings = Declaration.objects.filter(
            area=self.area.id,
            event_date__lt=date,
            event_date__gt=self.event_date,
            ).exclude(pk=self.id)
        for sib in siblings:
            if sib.status != 'D':
                logger.info('excluding area %s due to declaration with non-D status %s at date %s' % (sib.area, sib.status, sib.event_date))
                return False
        return True

class PopCount(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    declaration = models.ForeignKey(Declaration, on_delete=models.CASCADE)
    population = models.PositiveIntegerField()
    date = models.DateField(verbose_name='Declaration date')
    # This status field mirrors the one in Declaration class
    # except it will only include those status values which change the population count
    status = models.CharField(
        max_length=1,
        choices=Declaration.STATUS_TYPES,
        default=Declaration.DECLARED,
    )

    def __str__(self):
        return self.population

    @classmethod
    def create(cls, country, declaration, population):
        pop = cls(country=country, declaration=declaration, population=population)
        pop.status = declaration.status
        pop.date = declaration.event_date
        pop.save()
        return pop

class ImportDeclaration(models.Model):
    name = models.TextField(null=True, blank=True)
    num_govs = models.PositiveSmallIntegerField(null=True, blank=True)
    area = models.TextField(null=True, blank=True)
    population = models.PositiveIntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    due = models.TextField(null=True, blank=True)
    contact = models.TextField(null=True, blank=True)
    link = models.TextField(null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

from django.db.models.signals import m2m_changed

def supplements_changed(sender, **kwargs):
    update = False
    if (kwargs['action'] == 'post_add'):
        update = True
    if (kwargs['action'] == 'post_remove'):
        update = True
    if (kwargs['action'] == 'post_clear'):
        update = True
    if update:
        kwargs['instance'].country.popcount_update_needed()

m2m_changed.connect(supplements_changed, sender=Area.supplements.through)
