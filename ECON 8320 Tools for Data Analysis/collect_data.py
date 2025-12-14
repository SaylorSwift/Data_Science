import requests
import json
import pandas as pd
from datetime import datetime
import os

#setup
output = 'data.csv'

default_start_year = 2008
default_end_year = datetime.now().year

series_keys = {
    'LNS14000000': 'Unemployment Rate',
    'CES0000000001': 'Employment Level',
    'CUUR0000SA0': 'CPI',
    'CES0500000003': 'Hourly Earnings',
    'CES0500000002': 'Hours Worked'
}

bls_api = 'https://api.bls.gov/publicAPI/v1/timeseries/data/'

#request json from BLS
def request_json(series_ids, start_year, end_year):

    headers = {'Content-type': 'application/json'}

    data = json.dumps({
    "seriesid": series_ids,
    "startyear": str(start_year),
    "endyear": str(end_year)
    })

    p = requests.post(bls_api, data=data, headers=headers)

    json_data = json.loads(p.text)

    return json_data

#convert json to data frame. add calculated column estimated weekly income
def convert_json(json_data):

    records = []

    for series in json_data['Results']['series']:
        series_id = series['seriesID']
        col_names = series_keys.get(series_id, series_id)
        
        for item in series['data']:
            year = item['year']
            period = item['period']
            value = item['value']
            month = int(period.replace('M', ''))
            date_str = f"{year}-{month:02d}-01"
            records.append({'Date': date_str, 'Series': col_names, 'Value': value})

    #change to wide form to make visuals easier
    table = pd.DataFrame(records).pivot(index = 'Date', columns = 'Series', values = 'Value')
    table = table.reset_index()


    table['Date'] = pd.to_datetime(table['Date'])
    #convert to numbers so multiply works
    table['Hourly Earnings'] = pd.to_numeric(table['Hourly Earnings'], errors = 'coerce')
    table['Hours Worked'] = pd.to_numeric(table['Hours Worked'], errors = 'coerce')

    table['Weekly Income'] = round(table['Hourly Earnings'] * table['Hours Worked'],2)


    return table

#first time running script with no data
def initial_data():

    df = pd.DataFrame()
    
    start_year = default_start_year
    series_id = list(series_keys.keys())

    #request data, append data in 10 year periods
    while start_year <= default_end_year:
        end_year = min(start_year + 9, default_end_year)
        new_json_data = request_json(series_id, start_year, end_year)
        new_df = convert_json(new_json_data)
        df = pd.concat([df,new_df], ignore_index = True)
        start_year += 10

    #save as .csv
    df.sort_values('Date')
    df.to_csv(output, index = False)

    print(f"create data.csv ({default_start_year} - {default_end_year})")

#update data to most current if already exist
def update_data():

    #check most recent data date
    df = pd.read_csv(output)
    df['Date'] = pd.to_datetime(df['Date'])

    start_year = max(df["Date"]).year
    end_year = datetime.now().year
    series_id = list(series_keys.keys())

    #collect new data
    new_json_data = request_json(series_id, start_year, end_year)
    new_df = convert_json(new_json_data)

    #append new data
    if not new_df.empty:
        df = pd.concat([df,new_df], ignore_index = True)
        df = df.drop_duplicates(subset=["Date"], keep = "last")
        df.sort_values('Date')
        df.to_csv(output, index = False)
        print(f"data.csv found. update data ({start_year} - {end_year})")

    else:
        print('no new data available.')

#check to if first time running code
def collect_data():
    #check if data.csv already exist
    if os.path.isfile(output):
        df = pd.read_csv(output)
        df['Date'] = pd.to_datetime(df['Date'])

        #calculate date difference between current date and data date
        current_date = datetime.now() - pd.DateOffset(months=1)
        data_date = max(df['Date'])

        month_diff = (current_date.year - data_date.year) * 12 + (current_date.month - data_date.month)

        #if lags less than one month, don't update
        if month_diff < 1:
            print("data.csv found. data is up to date")

        #found existing data, lag more than 1 month, update data
        else:
            update_data()

    #no exisiting data, collect data first time
    else:
        initial_data()


if __name__ == "__main__":
    collect_data()
