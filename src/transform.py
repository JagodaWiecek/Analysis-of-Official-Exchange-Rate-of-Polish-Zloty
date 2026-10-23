"""
This code load s and transforms the raw exchange rate data downloaded from the NBP API.
It reads the JSON files from the raw data directory, extracts information, and saves it to a CSV file in the processed data directory.
"""
import json
import logging
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PROCESSED_FILE = PROCESSED_DIR / "rates.csv"

logger = logging.getLogger(__name__)
"""
Load all tables_a_*.json files and combine them into a single list.
"""
def load_raw(raw_dir: Path = RAW_DIR) -> list[dict]:
    
    files = sorted(raw_dir.glob("tables_a_*.json"))
    if not files:
        raise FileNotFoundError(f"No files found in {raw_dir}")
    tables: list[dict] = []
    for file in files:
            try:
                tables.extend(json.loads(file.read_text(encoding="utf-8")))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in file: {file.name} "
                         f"Remove it and download the data again.") from exc
    return tables

"""
Transforms the list of dictionaries (JSON data) into a pandas DataFrame
The table is saved in a format of 4 columns: date, code, currency, mid
- date: the effective date of the exchange rate
- code: the currency code (e.g., EUR, USD)
- currency: the full name of the currency (e.g., Euro, US Dollar)
- mid: the average exchange rate
"""
def to_dataframe(tables: list[dict]) -> pd.DataFrame:
    try:
        rows = [
            {
                "date": table["effectiveDate"],
                "code": rate["code"],
                "currency": rate["currency"],
                "mid": rate["mid"],
            }
            for table in tables
            for rate in table["rates"]
        ]
    except KeyError as exc:
        raise ValueError(f"Unexpected data format from API, missing field {exc}") from exc 
    df = pd.DataFrame(rows, columns=["date", "code", "currency", "mid"])
    df["date"] = pd.to_datetime(df["date"])
    df["mid"] = df["mid"].astype(float)
    df = df.drop_duplicates(subset=["date", "code"])
    df = df.dropna(subset=["mid"])
    if df.duplicated(subset=["date", "code"]).any():
        logger.warning("Found duplicate rows after dropping duplicates.")
    return df.sort_values(["code", "date"]).reset_index(drop=True)

"""
The quality checks on the DataFrame ensure that the data is valid and consistent.
1. Check if the DataFrame is empty.
2. Check if there are any missing or non-positive exchange rates in the 'mid' column.
3. Check for duplicate rows based on the combination of 'date' and 'code'.
"""
def validate(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("Table is empty")
    if df["mid"].isna().any() or (df["mid"] <= 0).any():
        raise ValueError("Empty or non-positive exchange rates found")
    if df.duplicated(subset=["date", "code"]).any():
        raise ValueError("Duplicates found")

"""
Saves the processed (silver) data to a CSV file
"""
def save_processed(df: pd.DataFrame, path: Path = PROCESSED_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

"""
The function that process the JSON files from the raw data directory, 
transforms them into a DataFrame, 
validates the data, 
and saves it to a CSV file in the processed data directory.
"""
def build_silver(raw_dir: Path = RAW_DIR, out_path: Path = PROCESSED_FILE) -> pd.DataFrame:
    df = to_dataframe(load_raw(raw_dir))
    validate(df)
    save_processed(df, out_path)
    return df

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_silver()
   

    