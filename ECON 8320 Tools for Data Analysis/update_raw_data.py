import requests
import json
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
DATA_FILE = 'raw_data.csv'

# Same Series Mapping
SERIES_MAPPING = {
    'LNS14000000': 'Unemployment Rate',
    'CES0000000001': 'Employment Level',
    'CUUR0000SA0': 'CPI',
    'CES0500000003': 'Hourly Earnings',
    'CES0500000002': 'Hours Worked'
}

def fetch_bls_data(series_ids, start_year, end_year):
    headers = {'Content-type': 'application/json'}
    # Removed "registrationkey"
    data = json.dumps({
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year)
    })
    
    print(f"Checking for new data: {start_year}-{end_year}...")
    try:
        response = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error connecting to BLS: {e}")
        return None

def parse_and_process(json_data):
    records = []
    if not json_data or 'Results' not in json_data:
        return pd.DataFrame()

    for series in json_data['Results']['series']:
        series_id = series['seriesID']
        col_name = SERIES_MAPPING.get(series_id, series_id)
        for item in series['data']:
            if 'M' in item['period'] and item['period'] != 'M13':
                date_str = f"{item['year']}-{int(item['period'].replace('M', '')):02d}-01"
                records.append({'Date': date_str, 'Series': col_name, 'Value': item['value']})
    
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df_wide = df.pivot(index='Date', columns='Series', values='Value')
    df_wide.reset_index(inplace=True)
    return df_wide

def main():
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: {DATA_FILE} not found. Run import_raw_data.py first.")
        return

    # 1. Read existing data
    df_existing = pd.read_csv(DATA_FILE)
    df_existing['Date'] = pd.to_datetime(df_existing['Date'])
    
    # 2. Find last update date
    last_date = df_existing['Date'].max()
    start_year = last_date.year
    current_year = datetime.now().year
    
    print(f"Last data point in file: {last_date.date()}")
    
    # 3. Fetch potentially new data
    json_data = fetch_bls_data(list(SERIES_MAPPING.keys()), start_year, current_year)
    df_new = parse_and_process(json_data)
    
    if df_new.empty:
        print("No new data returned from API.")
        return

    # 4. Clean and Append
    df_new['Date'] = pd.to_datetime(df_new['Date'])
    
    # Filter: Only keep rows strictly AFTER the last known date
    df_new = df_new[df_new['Date'] > last_date]
    
    if df_new.empty:
        print("Data is already up to date.")
    else:
        # Append
        df_combined = pd.concat([df_existing, df_new])
        df_combined.sort_values('Date', inplace=True)
        
        # Save
        df_combined.to_csv(DATA_FILE, index=False)
        print(f"SUCCESS: Appended {len(df_new)} new months.")
        print(f"New latest date: {df_combined['Date'].max().date()}")

if __name__ == "__main__":
    main()