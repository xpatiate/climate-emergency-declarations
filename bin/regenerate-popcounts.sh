#!/bin/bash

URL=http://icef.localhost:8000

COUNTRIES='data/countries.csv'

CODES=$(tail -n 217 $COUNTRIES | cut -d',' -f 1)

for C in $CODES
do
    echo curl $URL/api/country/$C/regenerate_timeline
done
