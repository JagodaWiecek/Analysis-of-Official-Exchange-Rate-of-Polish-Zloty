import pandas as pd
import pytest

from src.analysis import select_currencies, add_daily_change, find_extremes

"""
Helpers for testing the analysis functions.
The make_df function creates a sample DataFrame with exchange rate data for two currencies (EUR and USD) over a period of 4 days
"""
def make_df() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=4)
    mids = {
        "EUR": [4.0, 4.4, 4.2, 4.3],   # +10%, -4.5%, +2.4%
        "USD": [3.0, 2.7, 3.3, 3.2],   # -10%, +22.2%, -3.0%
    }
    rows = [{"date": d, "code": code, "currency": code.lower(), "mid": m}
            for code, values in mids.items() for d, m in zip(dates, values)]
    return pd.DataFrame(rows)

"""
The pick function is a helper function used in the tests to extract a specific row 
from the result DataFrame based on the currency code and event type
"""
def pick(result: pd.DataFrame, code: str, event: str) -> pd.Series:
    return result[(result["code"] == code) & (result["event"] == event)].iloc[0]

# ------ TESTS ------
"""
To verify that the function correctly filters the DataFrame to include only the specified currencies
"""
def test_select_currencies_filters():
    df = select_currencies(make_df(), ["EUR"])
    assert set(df["code"]) == {"EUR"}

"""
To verify if the function raises a ValueError when one or more specified currencies are missing from the DataFrame
"""
def test_select_currencies_raises_when_missing():
    with pytest.raises(ValueError):
        select_currencies(make_df(), ["JPY", "GBP"])

"""
To verify the function correctly computes the daily percentage change in exchange rates for each currency
"""
def test_daily_change_is_computed_per_currency():
    df = add_daily_change(make_df())
    eur = df[df["code"] == "EUR"]["pct_change"].tolist()
    assert pd.isna(eur[0])                       # first day in EUR should be NaN
    assert eur[1] == pytest.approx(10.0)

    usd_first = df[df["code"] == "USD"]["pct_change"].iloc[0] # first day in USD should also be NaN
    usd = df[df["code"] == "USD"]["pct_change"].tolist()
    assert pd.isna(usd_first) 
    assert usd[1] == pytest.approx(-10.0)

"""
The function verifies that the find_extremes function correctly identifies the lowest and highest exchange rates
"""
def test_extremes_rates():
    result = find_extremes(add_daily_change(make_df()))
    assert pick(result, "EUR", "lowest_rate")["date"] == pd.Timestamp("2025-01-01")
    assert pick(result, "EUR", "highest_rate")["date"] == pd.Timestamp("2025-01-02")
    assert pick(result, "USD", "lowest_rate")["mid"] == 2.7

"""
To verify that the find_extremes function correctly identifies the biggest daily fall and rise 
for each currency based on the percentage change in exchange rates
"""
def test_extremes_daily_changes():
    result = find_extremes(add_daily_change(make_df()))
    assert pick(result, "EUR", "biggest_daily_rise")["date"] == pd.Timestamp("2025-01-02")
    assert pick(result, "EUR", "biggest_daily_fall")["date"] == pd.Timestamp("2025-01-03")
    assert pick(result, "USD", "biggest_daily_fall")["date"] == pd.Timestamp("2025-01-02")
    assert pick(result, "USD", "biggest_daily_rise")["pct_change"] == pytest.approx(22.222, abs=0.01)

"""
To verify that function saves only 4 events per currency in the extremes DataFrame, 
ensuring that each currency has exactly one of each event type, 
lowest rate, highest rate, biggest daily fall, and biggest daily rise
"""
def test_extremes_has_four_events_per_currency():
    result = find_extremes(add_daily_change(make_df()))
    assert len(result) == 8
    assert result.groupby("code")["event"].nunique().eq(4).all()