import datetime
import json
import csv
import sys

countries = []
nodetypes = []
nodes = []
with open('countries.csv', newline='') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    cnum = 1
    read_title = False
    for row in csvreader:
        if not read_title:
            read_title = True
            continue
        country_code = row[0]
        population = int(float(row[1]) * 1000)
        region = row[2]
        name = row[3]
        countries.append({
            'model': 'govtrack.Country',
            'pk': cnum,
            'fields': {
                'country_code': country_code,
                'population': population,
                'region': region,
                'name': name,
            }
        })
        nodetypes.append({
            'model': 'govtrack.NodeType',
            'pk': cnum,
            'fields': {
                'name': 'National Government',
                'country': cnum,
                'level': 1,
                'parent': cnum,
            }
        })
        nodes.append({
            'model': 'govtrack.Node',
            'pk': cnum,
            'fields': {
                'name': name,
                'area': name,
                'country': cnum,
                'parent': cnum,
                'nodetype': cnum,
                'population': population
            }
        })
        cnum += 1

print(json.dumps(countries))
print()
print(json.dumps(nodetypes))
print()
print(json.dumps(nodes))
