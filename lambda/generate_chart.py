from io import StringIO
import os
import sys

# look for modules in current dir + /lib
CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(CWD, "lib"))

import pandas as pd
import matplotlib.pyplot as plt
import requests

API_HOST=os.environ.get('API_HOST')

def make_chart(event, context):
    chart_type = event.get('type')
    country = event.get('country_code')

    if chart_type == 'country' and country:
        make_country_chart(country)
    elif chart_type == 'world':
        make_world_chart()
    else:
        print(f"Unknown chart type {chart_type}")

def make_country_chart(code):
    api_url = f"{API_HOST}/api/country/{code}/pop_by_location"
    print(api_url)

    resp = requests.get(api_url)
    print(resp.text)

    df = pd.read_csv(StringIO(resp.text),index_col='Date', parse_dates=True)
    country_name = df['Country'][2]
    ax = df.plot.area(title=country_name, legend=None)
    fig_path = f"/tmp/{code}.png"
    plt.savefig(fig_path)


def make_world_chart():
    api_url = f"{API_HOST}/api/world/population_timeline"
    print(api_url)

    resp = requests.get(api_url)
    print(resp.text)

    world_df = pd.read_csv(StringIO(resp.text),
            index_col=['Date'],
            parse_dates=True)
    world_df = world_df[~world_df['Country'].str.contains('zzz')]

    pivoted = world_df.pivot_table(
        index=['Date'],
        columns='Country',
        values='Declared Population')
    pfilled = pivoted.fillna(method="ffill")
    byday = pfilled.resample('D').fillna("ffill")
    
    ax = byday.plot.area(figsize=(16,8))
    fig_path = f"/tmp/world.png"
    plt.savefig(fig_path)

if __name__ == '__main__':
    #make_chart({'type': 'country', 'country_code': 'NLD'}, {})
    make_chart({'type': 'world'}, {})
