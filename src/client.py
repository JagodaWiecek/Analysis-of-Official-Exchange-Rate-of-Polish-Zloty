"""
This module contains functions to download raw exchange rate data from the NBP API and save it to local files as JSON. 
It handles date ranges, API requests, and file writing. 
The main function downloads data for the last 5 years.
"""
import json
import logging
from datetime import date, timedelta
from pathlib import Path

import requests

BASE_URL = "https://api.nbp.pl/api/exchangerates/tables/a"
MAX_DAYS = 93 #the time period for which the NBP API allows fetching data in a single request is 93 days
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
HISTORY_DAYS = 365 * 5
REQUEST_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)

"""
Generates date windows of up to max_days between start and end dates
"""
def date_windows(start: date, end: date, max_days: int = MAX_DAYS):
    current = start
    while current <= end:
        window_end = min(current + timedelta(days=max_days - 1), end)
        yield current, window_end
        current = window_end + timedelta(days=1)

"""
Fetches exchange rate data from the NBP API for a given date range and returns it as a list of dictionaries.
If the API returns a 404 status code, an empty list is returned.
"""
def fetch_window(start: date, end: date) -> list[dict]:
    url = f"{BASE_URL}/{start}/{end}/"
    response = requests.get(url, params={"format": "json"}, timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code == 404:
        return []
    response.raise_for_status()
    return response.json()

"""
Function to download raw exchange rate data for a given date range and save it to local JSON files.
The data is fetched in windows of up to MAX_DAYS to comply with the NBP API limitations. 
Each window's data is saved to a separate JSON file in the RAW_DIR directory.
"""
def download_raw(start: date, end: date) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for win_start, win_end in date_windows(start, end):
        logger.info("Downloading %s - %s", win_start, win_end)
        tables = fetch_window(win_start, win_end)
        path = RAW_DIR / f"tables_a_{win_start}_{win_end}.json"
        path.write_text(json.dumps(tables), encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    today = date.today()
    download_raw(today - timedelta(days=HISTORY_DAYS), today)