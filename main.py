import logging
from datetime import date, timedelta
import sys
import argparse
from pathlib import Path
import requests

from src.client import download_raw
from src.transform import build_silver
from src.analysis import gold_process
from src.plots import plot_all

logger = logging.getLogger("pipeline")

logging.basicConfig(level=logging.INFO)
HISTORY_DAYS = 365 * 5
today = date.today()
OUTPUT_DIR = Path(__file__).resolve().parent /"data"/ "output"

def run(skip_download: bool) -> None:
    """
    Run the entire data processing pipeline:
    1. Download raw data for the last HISTORY_DAYS days.
    2. Transform the raw data into a processed format.
    3. Analyze the processed data and save results.
    4. Generate plots based on the analyzed data.
    """
    if not skip_download:
        today = date.today()
        download_raw(today - timedelta(days=HISTORY_DAYS), today)
    
    build_silver()
    gold, extremes = gold_process()
    plot_all(gold, extremes, OUTPUT_DIR/"plots")

def main() -> int:
    parser = argparse.ArgumentParser(description="Analysis of PLN rates from API NBP")
    parser.add_argument("--skip-download", action="store_true",
                        help="skip download, use files from data/raw")
    args = parser.parse_args()
    try:
        run(args.skip_download)
    except requests.RequestException as exc:
        logger.error("Download failed: %s", exc)
        return 1
    except ValueError as exc:
        logger.error("Data problem: %s", exc)
        return 2
    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
        return 3
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        return 4
    return 0

if __name__ == "__main__":
    sys.exit(main())
