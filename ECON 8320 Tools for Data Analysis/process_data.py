import pandas as pd

# --- CONFIGURATION ---
INPUT_FILE = 'raw_data.csv'
OUTPUT_FILE = 'processed_data.csv'

def process_macro_data():
    print("Loading raw data...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"ERROR: {INPUT_FILE} not found. Run import_raw_data.py first.")
        return

    # 1. Ensure Date is datetime
    df['Date'] = pd.to_datetime(df['Date'])
    df.sort_values('Date', inplace=True)

    print("Calculating derived metrics...")

    # 2. Calculate "Weekly Earnings" (Estimated Income)
    # Formula: Hourly Rate * Weekly Hours
    df['Weekly Earnings'] = df['Hourly Earnings'] * df['Hours Worked']

    # 3. Calculate "Real" Weekly Earnings (Adjusted for Inflation)
    # We adjust everything to "Today's Dollars" using the most recent CPI in the file.
    # Formula: (Nominal Earnings / Current CPI) * Latest CPI
    latest_cpi = df['CPI'].iloc[-1]
    df['Real Weekly Earnings'] = (df['Weekly Earnings'] / df['CPI']) * latest_cpi

    # 4. Rounding for cleaner display
    df['Weekly Earnings'] = df['Weekly Earnings'].round(2)
    df['Real Weekly Earnings'] = df['Real Weekly Earnings'].round(2)
    
    # 5. Save
    df.to_csv(OUTPUT_FILE, index=False)
    
    print("-" * 30)
    print(f"SUCCESS: Data processed and saved to {OUTPUT_FILE}")
    print(f"Columns added: Weekly Earnings, Real Weekly Earnings")
    print(df.tail())

if __name__ == "__main__":
    process_macro_data()