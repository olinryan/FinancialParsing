import pandas as pd

from edgar import *

# Tell the SEC who you are
# set_identity("Olin Ryan olinmryan@yahoo.com")     # Python 
# export EDGAR_IDENTITY="Olin Ryan olinmryan@yahoo.com"    # Linux



if __name__ == "__main__":

    # Most recent financial staement:
    boeing = Company("BA").get_filings(form='10-K',date='2024-01-31')

    BAfins = Financials.extract(boeing[0])

    # Statement of Operations:
    print(BAfins.get_income_statement())
    # Statement of Financial Position:
    print(BAfins.get_balance_sheet())
    # Statement of Cash Flows:
    print(BAfins.get_cash_flow_statement())
    # Statement of Stockholders' Equity:
    print(BAfins.get_statement_of_changes_in_equity())
    # Income Statement:
    print(BAfins.get_statement_of_comprehensive_income())

    # Convert to dataframe:
    BA_balSheet = BAfins.get_balance_sheet().get_dataframe()
    print(BA_balSheet)