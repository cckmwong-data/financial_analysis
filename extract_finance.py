import yfinance as yf
import pandas as pd
from google.colab import auth
import gspread
from google.auth import default

# 1. Authenticate with Google
auth.authenticate_user()
creds, _ = default()
gc = gspread.authorize(creds)

# 2. Define your Spreadsheet ID (Paste yours here)
spreadsheet_id = '1IJh9E22UNFZ8soiNZrhilQfiimO7nVIzLiVLNZLRz6M'
sh = gc.open_by_key(spreadsheet_id)

tickers = ["TSLA", "NVDA", "META", "GOOGL"]

def get_financials(ticker_list):
    inc_list, bal_list, cf_list = [], [], []
    for ticker in ticker_list:
        t = yf.Ticker(ticker)

        # Helper to process and melt data
        def process(df, name):
            if not df.empty:
                df = df.reset_index().melt(id_vars="index", var_name="Period", value_name="Value").rename(columns={"index": "Account"})
                df["Ticker"] = ticker
                return df
            return pd.DataFrame()

        inc_list.append(process(t.financials, "Income"))
        bal_list.append(process(t.balance_sheet, "Balance"))
        cf_list.append(process(t.cashflow, "CashFlow"))

    return pd.concat(inc_list), pd.concat(bal_list), pd.concat(cf_list)

# 3. Fetch Data
income_df, balance_df, cashflow_df = get_financials(tickers)

# 4. Write to Google Sheets
def update_sheet(df, sheet_name):
    worksheet = sh.worksheet(sheet_name)
    worksheet.clear()
    # Adding header and values
    worksheet.update([df.columns.values.tolist()] + df.astype(str).values.tolist())

update_sheet(income_df, "Income Statement")
update_sheet(balance_df, "Balance Sheet")
update_sheet(cashflow_df, "Cash Flow")

print("Success! Google Sheet Updated.")
