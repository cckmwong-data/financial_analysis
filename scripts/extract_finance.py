import os
import json
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. AUTHENTICATION (Replaces Colab auth)
# This looks for the 'GOOGLE_SHEETS_CREDENTIALS' secret you set up in GitHub
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
secret_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")

if not secret_json:
    raise ValueError("GOOGLE_SHEETS_CREDENTIALS secret not found. Check your GitHub Settings!")

creds_dict = json.loads(secret_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(creds)

# 2. OPEN SPREADSHEET
# Using your specific Spreadsheet ID
spreadsheet_id = '1IJh9E22UNFZ8soiNZrhilQfiimO7nVIzLiVLNZLRz6M'
sh = gc.open_by_key(spreadsheet_id)

tickers = ["TSLA", "NVDA", "META", "GOOGL"]

def get_financials(ticker_list):
    inc_list, bal_list, cf_list = [], [], []
    for ticker in ticker_list:
        print(f"Fetching data for: {ticker}")
        try:
            t = yf.Ticker(ticker)

            # Helper to process and melt data (Your original logic)
            def process(df):
                if df is not None and not df.empty:
                    # Reset index to get the Account names as a column
                    df = df.reset_index()
                    # Melt turns dates into a single "Period" column for Power BI
                    df = df.melt(id_vars="index", var_name="Period", value_name="Value")
                    df = df.rename(columns={"index": "Account"})
                    df["Ticker"] = ticker
                    # Convert Period to string to ensure it writes to Sheets correctly
                    df["Period"] = df["Period"].astype(str)
                    return df
                return pd.DataFrame()

            inc_list.append(process(t.financials))
            bal_list.append(process(t.balance_sheet))
            cf_list.append(process(t.cashflow))
        except Exception as e:
            print(f"Error skipping {ticker}: {e}")

    return pd.concat(inc_list), pd.concat(bal_list), pd.concat(cf_list)

# 3. FETCH DATA
income_df, balance_df, cashflow_df = get_financials(tickers)

# 4. WRITE TO GOOGLE SHEETS
def update_sheet(df, sheet_name):
    try:
        worksheet = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        # If the tab doesn't exist, create it
        worksheet = sh.add_worksheet(title=sheet_name, rows="1000", cols="20")
    
    worksheet.clear()
    
    # Fill NaN with 0 and convert to list format for gspread
    # Power BI handles 0s better than empty strings in many DAX measures
    data = [df.columns.values.tolist()] + df.fillna(0).astype(str).values.tolist()
    
    worksheet.update(data)
    print(f"Successfully updated '{sheet_name}'")

# Execute updates
update_sheet(income_df, "Income Statement")
update_sheet(balance_df, "Balance Sheet")
update_sheet(cashflow_df, "Cash Flow")
