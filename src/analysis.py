import logging
from pathlib import Path
import pandas as pd
"""
The task, for each currency in comparison to PLN:
    when it had the highest depreciation
    when it had the highest appreciation
    when it had extreme fall in one day (24 hours from high to low)
    when it had extreme growth in one day (24 hours from low to high)
"""
CURRENCIES = ["EUR", "USD", "GBP", "JPY"]
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PROCESSED_FILE = PROCESSED_DIR / "rates.csv"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output"
OUTPUT_FILE = OUTPUT_DIR / "rates.csv"
EXTREMES_FILE = OUTPUT_DIR / "extremes.csv"
logger = logging.getLogger(__name__)

"""
Loads the processed data from the CSV file and returns it as a pandas DataFrame.
"""
def load_processed(path: Path = PROCESSED_FILE) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"])

"""
Removes unimportant currencies from the DataFrame, keeping only the specified currencies
"""
def select_currencies(df: pd.DataFrame, currencies: list[str] = CURRENCIES) -> pd.DataFrame:
    missing = set(currencies) - set(df["code"])
    if missing:
        raise ValueError(f"Missing currencies: {sorted(missing)}")
    return df[df["code"].isin(currencies)].copy()

"""
Provide additional column to the DataFrame, such as daily percentage change in exchange rates for each currency. 
It calculates it using the current mid value and previous day's mid value, grouped by currency code
Important to note: 
    the first date for each currency will have NaN values for pct_change since there is no previous day to compare to
"""
def add_daily_change(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["code", "date"]).reset_index(drop=True)
    df["pct_change"] = df.groupby("code")["mid"].pct_change(fill_method=None) * 100
    return df

def save_gold(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

"""
For each currency, finds 4 events: lowest rate, highest rate, biggest daily fall, and biggest daily growth. 
In case of ties, the earliest date is selected. 
The function returns a DataFrame with the results.
"""
def find_extremes(df: pd.DataFrame) -> pd.DataFrame:
    picks = {
        "lowest_rate": df.loc[df.groupby("code")["mid"].idxmin()],
        "highest_rate": df.loc[df.groupby("code")["mid"].idxmax()],
        "biggest_daily_fall": df.loc[df.groupby("code")["pct_change"].idxmin()],
        "biggest_daily_rise": df.loc[df.groupby("code")["pct_change"].idxmax()],
    }
    result = pd.concat([rows.assign(event=name) for name, rows in picks.items()])
    result = result[["code", "event", "date", "mid", "pct_change"]]
    return result.sort_values("code", kind="stable").reset_index(drop=True)

def gold_process(out_path: Path = OUTPUT_FILE,
                extreme_path: Path = EXTREMES_FILE) -> pd.DataFrame:
    df = load_processed()
    df = select_currencies(df)
    df = add_daily_change(df)
    save_gold(df, out_path)
    results = find_extremes(df)
    save_gold(results, extreme_path)
    return df

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gold_process()
    #logger.info("Results \t: %s", results)
    #logger.info("Selected currencies: %s", df["code"].unique())
    #logger.info("pct_change: %s", df["pct_change"].unique())