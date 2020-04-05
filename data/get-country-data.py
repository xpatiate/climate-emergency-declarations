#!/usr/bin/env python3

import argparse
from iso3166 import countries
import sys
import json
import pandas as pd
import requests


UN_POPDATA = "https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/CSV_FILES/WPP2019_TotalPopulationBySex.csv"
WB_API = "http://api.worldbank.org/v2/country?format=json&per_page=400"

parser = argparse.ArgumentParser(description="Create a countries.csv file")
parser.add_argument("datafile", type=str, help="Path to already downloaded file")
args = parser.parse_args()
datafile = args.datafile

if datafile:
    # check if it's a real file
    try:
        with open(datafile) as df:
            pass
    except IOError as io:
        print("Could not read file: %s" % io)
        sys.exit()
else:
    # TODO go and download data file
    pass

undata = pd.read_csv(datafile)

get_recent = undata[(undata.Time == 2018) & (undata.Variant == "Medium")]
recent = get_recent.loc[:, ["LocID", "Location", "PopTotal"]].set_index("LocID")

# The WorldBank API lists over 300 items as "countries"
# including many that are aggregates which we need to exclude
# It gives the 3-char country code but not the numeric one used by "ISO 3166-1 numeric"

response = requests.get(WB_API)
jsondata = json.loads(response.text)

meta = jsondata[0]
nations = jsondata[1]

nationlist = []
for c in nations:
    # skip the entries that are collections of countries
    if c["region"]["value"] == "Aggregates":
        continue
    try:
        country = countries.get(c["id"])
        nationlist.append(
            {
                "charcode": c["id"],
                "numcode": int(country.numeric),
                "region": c["region"]["value"],
                "name": c["name"],
            }
        )
    except KeyError as ex:
        # print("No record for country code %s" % c['id'])
        pass

print(
    '"%s","%s","%s","%s"'
    % ("Country Code", "Population (Thousands)", "Region", "Country")
)
for c in nationlist:
    try:
        population = recent.loc[c["numcode"], "PopTotal"]
        cname = recent.loc[c["numcode"], "Location"]
    except Exception as ex:
        # print("problem: %s" % ex)
        population = 0
        cname = c["name"]
    print('%s,%s,"%s","%s"' % (c["charcode"], population, c["region"], cname))
