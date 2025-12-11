import requests
import json
import pandas as pd
from datetime import datetime

# Fist time import data
OUTPUT_FILE = 'raw_data.csv'
START_YEAR = 2008
END_YEAR = 2024

# Series IDs 
SERIES_MAPPING = {
    'LNS14000000': 'Unemployment Rate',
    'CES0000000001': 'Employment Level',
    'CUUR0000SA0': 'CPI',
    'CES0500000003': 'Hourly Earnings',
    'CES0500000002': 'Hours Worked'
}

def fetch_bls_chunk(series_ids, start_year, end_year):
    headers = {'Content-type': 'application/json'}
    data = json.dumps({
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year)
    })
    
    print(f"   > Requesting BLS data: {start_year}-{end_year}...")
    try:
        response = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
        json_data = response.json()
        
        if json_data.get('status') != 'REQUEST_SUCCEEDED':
            print(f"   ! Warning: {json_data.get('message')}")
            
        return json_data
    except Exception as e:
        print(f"   ! Error: {e}")
        return None

def parse_bls_response(json_data):
    records = []
    if not json_data or 'Results' not in json_data:
        return records

    for series in json_data['Results']['series']:
        series_id = series['seriesID']
        col_name = SERIES_MAPPING.get(series_id, series_id)
        
        for item in series['data']:
            year = item['year']
            period = item['period']
            value = item['value']
            
            # Filter for Monthly data only (M01-M12)
            if 'M' in period and period != 'M13':
                month = int(period.replace('M', ''))
                date_str = f"{year}-{month:02d}-01"
                records.append({'Date': date_str, 'Series': col_name, 'Value': value})
    return records

def main():
    print(f"--- Starting Full Data Import ({START_YEAR} - {END_YEAR}) ---")
    
    series_list = list(SERIES_MAPPING.keys())
    all_records = []

    # Loop in 10-year chunks to respect BLS limits
    for y in range(START_YEAR, END_YEAR + 1, 10):
        chunk_end = min(y + 9, END_YEAR)
        json_data = fetch_bls_chunk(series_list, y, chunk_end)
        records = parse_bls_response(json_data)
        all_records.extend(records)

    # Create DataFrame
    if all_records:
        df = pd.DataFrame(all_records)
        
        # Pivot to Wide Format
        df_wide = df.pivot(index='Date', columns='Series', values='Value')
        df_wide.reset_index(inplace=True)
        
        # Clean types and sort
        df_wide['Date'] = pd.to_datetime(df_wide['Date'])
        df_wide = df_wide.sort_values('Date')
        
        # Save
        df_wide.to_csv(OUTPUT_FILE, index=False)
        print("-" * 30)
        print(f"SUCCESS: Created {OUTPUT_FILE}")
        print(f"Rows: {len(df_wide)}")
        print(f"Range: {df_wide['Date'].min().date()} to {df_wide['Date'].max().date()}")
    else:
        print("FAILURE: No data found.")

if __name__ == "__main__":
    main()