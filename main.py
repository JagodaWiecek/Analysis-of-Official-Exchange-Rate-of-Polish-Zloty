import logging
from datetime import date, timedelta

from src.client import download_raw

logging.basicConfig(level=logging.INFO)
HISTORY_DAYS = 365 * 5
today = date.today()
def main():
    download_raw(today - timedelta(days=HISTORY_DAYS), today)

if __name__ == "__main__":
    main()