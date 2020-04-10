from django.shortcuts import get_object_or_404, render, redirect, Http404, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from api.serializers import AreaSerializer, StructureSerializer
from rest_framework import generics, mixins, viewsets, permissions

from govtrack.models import (
    Declaration,
    Country,
    Area,
    Structure,
    Link,
    PopCount,
    ImportDeclaration,
)
from govtrack.forms import AreaForm

import csv
import datetime
import html
import io
import logging
from datetime import timedelta

logger = logging.getLogger("cegov")
DATE_FORMAT = "%Y-%m-%d"

## PUBLIC METHODS ##


def area_data(request, area_id):
    area = get_object_or_404(Area, pk=area_id)
    decl = area.latest_declaration
    dec_date = ""
    bestlink = ""
    contact = ""
    if decl and decl.is_currently_active():
        dec_date = decl.display_event_date()
        contact = decl.key_contact
        # TODO: add a 'best link' field
        # links = decl.links.all()
        # if links:
        #    bestlink = links[0].url
    areadata = [
        area.name,
        1,
        area.location,
        area.population,
        dec_date,
        "",  # empty col
        contact,
        bestlink,  # key document/reference
        area.contribution(),
    ]
    response = HttpResponse(content_type="text/csv")
    writer = csv.writer(response)
    writer.writerow(areadata)
    return response


def country_population(request, country_code):
    country = Country.find_by_code(country_code)
    if not country:
        raise Http404("No country for specified code")
    return HttpResponse(str(country.current_popcount), content_type="text/plain")


def trigger_all_recounts(request):
    status = 403
    if request.user.is_authenticated:
        countries = Country.objects.filter(popcount_ready=0)
        response = {"_triggered": len(countries)}
        for country in countries:
            logger.info(f"triggering recount for country {country}")
            response[country.country_code] = country.trigger_population_recount()
        return JsonResponse(response, content_type="application/json")
    else:
        return HttpResponse(status=status)


def country_trigger_recount(request, country_code):
    status = 403
    if request.user.is_authenticated:
        country = Country.find_by_code(country_code)
        if not country:
            raise Http404("No country for specified code")
        logger.info(f"triggering recount for country {country}")
        response = country.trigger_population_recount()
        return JsonResponse(dict(response), content_type="application/json")
    else:
        return HttpResponse(status=status)


def country_regenerate_timeline(request, country_code):
    status = 403
    if request.user.is_authenticated:
        country = Country.find_by_code(country_code)
        if not country:
            raise Http404("No country for specified code")
        country.generate_population_count()
        return HttpResponse(str(country.current_popcount), content_type="text/plain")
    else:
        return HttpResponse(status=status)


def country_population_timeline(request, country_code):
    country = Country.find_by_code(country_code)
    if not country:
        raise Http404("No country for specified code")
    response = HttpResponse(content_type="text/csv")
    writer = csv.writer(response)
    writer.writerow(
        [
            "Date",
            "Country",
            "Government",
            "Location",
            "Population",
            "Declaration Status",
            "Declared Population",
        ]
    )
    for pc in country.popcounts:
        area = pc.declaration.area
        writer.writerow(
            [
                pc.declaration.event_date,
                country.name,
                area.name,
                area.location,
                area.population,
                pc.status,
                pc.population,
            ]
        )
    return response


def country_pop_by_location(request, country_code):
    country = Country.find_by_code(country_code)
    if not country:
        raise Http404("No country for specified code")
    response = HttpResponse(content_type="text/plain")
    writer = csv.writer(response)
    writer.writerow(["Date", "Country", "Location", "Declared Population"])
    cpops = country.popcounts
    start_date = cpops[0].declaration.event_date
    logger.info(f"start date {start_date}")
    current_pop = 0
    last_date = cpops[0].declaration.event_date
    day_diff = timedelta(days=1)
    for pc in cpops:
        dec_date = pc.date
        while dec_date > last_date + day_diff:
            last_date += day_diff
            writer.writerow([last_date, country.name, "", current_pop])
        area = pc.declaration.area
        writer.writerow([pc.date, country.name, area.location, pc.population])
        current_pop = pc.population
        last_date = dec_date
    return response


def world_population_timeline(request):
    response = HttpResponse(content_type="text/plain")
    writer = csv.writer(response)
    all_popcounts = PopCount.objects.order_by("date")
    writer.writerow(["Date", "Country", "Government", "Declared Population"])
    for pc in all_popcounts:
        area = pc.declaration.area
        writer.writerow([pc.date, area.country.name, area.name, pc.population])
    return response


# unused
def country_declarations(request, country_code):
    country = Country.find_by_code(country_code)
    if not country:
        raise Http404("No country for specified code")
    response = HttpResponse(content_type="text/csv")
    writer = csv.writer(response)
    writer.writerow(
        ["Area", "Location", "Population", "Date Declared", "Declared Ancestors"]
    )
    query_args = {
        "order_by": "date",
    }

    before_date = request.GET.get("before")
    after_date = request.GET.get("after")
    if before_date:
        date_obj = None
        try:
            date_obj = datetime.datetime.strptime(before_date, DATE_FORMAT)
        except ValueError as ex:
            return HttpResponseBadRequest("Bad date format")
        query_args["before"] = before_date
    if after_date:
        date_obj = None
        try:
            date_obj = datetime.datetime.strptime(after_date, DATE_FORMAT)
        except ValueError as ex:
            return HttpResponseBadRequest("Bad date format")
        query_args["after"] = after_date

    declist = country.declarations(**query_args)
    for dec in declist:
        writer.writerow(
            [
                dec.area.name,
                dec.area.location,
                dec.area.population,
                dec.display_event_date(),
                dec.area.num_declared_ancestors(),
            ]
        )

    return response


## ADMIN METHODS ##


def structure_del(request, structure_id):
    status = 403
    if request.user.is_authenticated and request.method == POST:
        status = 200
        structure = get_object_or_404(Structure, pk=structure_id)
        structure.delete()
    return HttpResponse(status=status)


def area_del(request, area_id):
    status = 403
    if request.user.is_authenticated and request.method == POST:
        status = 200
        area = get_object_or_404(Area, pk=area_id)
        area.delete()
        if area.population > 0:
            area.country.popcount_update_needed()
    return HttpResponse(status=status)


def declaration_del(request, declaration_id):
    status = 403
    if request.user.is_authenticated and request.method == POST:
        status = 200
        declaration = get_object_or_404(Declaration, pk=declaration_id)
        declaration.delete()
        declaration.area.country.popcount_update_needed(declaration.event_date)
    return HttpResponse(status=status)


def link_del(request, link_id):
    status = 403
    if request.user.is_authenticated and request.method == POST:
        status = 200
        link = get_object_or_404(Link, pk=link_id)
        link.delete()
    return HttpResponse(status=status)


def import_declaration_del(request, import_declaration_id):
    status = 403
    if request.user.is_authenticated and request.method == POST:
        status = 200
        import_declaration = get_object_or_404(
            ImportDeclaration, pk=import_declaration_id
        )
        import_declaration.delete()
    return HttpResponse(status=status)


# Create multiple areas at once from CSV-like text
def add_multi_areas(request, parent_id, structure_id):
    if request.method == "POST" and request.user.is_authenticated:
        parent = Area.objects.get(id=parent_id)
        lines = request.POST.get("area_csv_data").split("\n")
        for line in lines:
            row = line.split("|")
            newarea_name = row.pop(0)
            try:
                newarea_pop = int(row.pop(0).replace(",", ""))
            except:
                newarea_pop = 0
            logger.info(f"Adding {newarea_name} with pop {newarea_pop}")
            form = AreaForm(
                {
                    "country": parent.country_id,
                    "location": parent.location,
                    "parent": parent_id,
                    "structure": structure_id,
                    "name": newarea_name,
                    "sort_name": newarea_name,
                    "population": newarea_pop,
                }
            )
            if form.is_valid():
                newarea = form.save()
                logger.info(
                    f"Created new area {newarea} population {newarea.population}"
                )
                for newurl in row:
                    logger.info(f"newurl {newurl}")
                    if not newurl:
                        continue
                    link_data = {
                        "content_type_id": Area.content_type_id(),
                        "object_id": newarea.id,
                        "url": newurl,
                    }
                    newlink = Link(**link_data)
                    try:
                        newlink.full_clean()
                        newlink.save()
                        logger.info("Created new link %s" % newlink)
                    except ValidationError as ex:
                        logger.error("couldn't save new link: %s" % ex)
            else:
                logger.error(f"Errors in add_multi_areas: {form.errors}")
    return redirect("area", area_id=parent_id)


# Inbox methods
def add_multi_import_declarations(request, country_id):
    if request.user.is_authenticated:
        # TODO only enter here if POST - even a GET request
        # results in popcounts being regenerated
        try:
            lines = request.POST.get("paste_data").split("\n")
            data = []

            for line in lines:
                values = line.split("|")
                date = False
                for fmt in (
                    "%d %b, %Y",
                    "%d %b %Y",
                    "%d %B %Y",
                    "%Y-%m-%d",
                    "%d %B, %Y",
                    "%d-%m-%Y",
                ):
                    try:
                        date = datetime.datetime.strptime(values[4], fmt).date()
                        break
                    except ValueError:
                        pass
                if not date:
                    raise ValueError("no valid date format found")
                data.append(
                    {
                        "name": values[0],
                        "num_govs": int("".join(values[1].split(","))),
                        "area": values[2],
                        "population": int("".join(values[3].split(","))),
                        "date": date,
                        "due": values[5],
                        "contact": values[6],
                        "link": values[7],
                        "country": Country.objects.filter(id=country_id).first(),
                    }
                )
        except (AttributeError, ValueError, IndexError) as error:
            return HttpResponse(
                f"Error: 400\nInvalid Input Data\n{error}",
                status=400,
                content_type="text/plain",
            )

        for datum in data:
            ImportDeclaration(**datum).save()

        return redirect(
            "inbox", country_id=Country.objects.filter(id=country_id).first().id
        )
    return HttpResponse(status=403)


def import_declaration_pro(request, parent_id, structure_id, import_declaration_id):
    if request.user.is_authenticated:
        importDeclaration = ImportDeclaration.objects.filter(
            id=import_declaration_id
        ).first()
        parent = Area.objects.filter(id=parent_id).first()
        structure = Structure.objects.filter(id=structure_id).first()

        area = Area(
            **{
                "name": importDeclaration.name,
                "country": importDeclaration.country,
                "location": importDeclaration.area,
                "population": importDeclaration.population,
                "structure": structure,
                "parent": parent,
            }
        )
        area.save()

        declaration = Declaration(
            **{
                "area": area,
                "status": "D",
                "event_date": importDeclaration.date,
                "key_contact": importDeclaration.contact,
            }
        )
        declaration.save()

        if declaration.affects_population_count:
            # Trigger a task to regenerate all stored population counts
            # for the country,
            # from the date of this declaration onwards
            area.country.popcount_update_needed(declaration.event_date)

        Link(
            **{
                "content_type_id": Declaration.content_type_id(),
                "object_id": declaration.id,
                "url": importDeclaration.link,
            }
        ).save()

        importDeclaration.delete()

        return redirect("area", area_id=area.id)
    return HttpResponse(status=403)


def declaration_from_import(request, area_id, import_declaration_id):
    if request.user.is_authenticated:
        importDeclaration = ImportDeclaration.objects.filter(
            id=import_declaration_id
        ).first()
        area = Area.objects.filter(id=area_id).first()

        declaration = Declaration(
            **{
                "area": area,
                "status": "D",
                "event_date": importDeclaration.date,
                "key_contact": importDeclaration.contact,
            }
        )
        declaration.save()

        if declaration.affects_population_count:
            # Regenerate all stored population counts for the country,
            # from the date of this declaration onwards
            area.country.popcount_update_needed(declaration.event_date)
            pass

        Link(
            **{
                "content_type_id": Declaration.content_type_id(),
                "object_id": declaration.id,
                "url": importDeclaration.link,
            }
        ).save()

        return redirect("area", area_id=area_id)
    return HttpResponse(status=403)


@csrf_protect
def structure_add_subtree(request, structure_id):
    logger.info(f"authenticated? {request.user.is_authenticated} method? {request.method}")
    if request.user.is_authenticated and request.method == "POST":
        logger.info(f"adding subtree to structure {structure_id}")
        struct = Structure.objects.get(pk=structure_id)
        new_struct = Structure(
            country=struct.country,
            parent=struct,
            name="Temporary holding area",
            level=(struct.level + 1),
        )
        new_struct.save()
        prev_struct = new_struct
        for l in range(1, 9):
            logger.info(f"Adding a new struct at level {l}")
            new_struct = Structure(
                country=struct.country,
                parent=prev_struct,
                name=f"Level {l}",
                level=(prev_struct.level + 1),
            )
            new_id = new_struct.save()
            logger.info(f"Added new structure id {new_struct.id}")
            prev_struct = new_struct
        return HttpResponse(status=200)

    return HttpResponse(status=403)


class AreaList(generics.ListCreateAPIView):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer


class AreaDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer


class AreaChildren(mixins.ListModelMixin, generics.GenericAPIView):
    serializer_class = AreaSerializer

    def get_queryset(self):
        return Area.objects.get(pk=self.kwargs["pk"]).children

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class StructureViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = Structure.objects.all()
    serializer_class = StructureSerializer
