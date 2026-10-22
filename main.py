import logging
from datetime import date, timedelta
import sys

from src.client import download_raw
from src.transform import build_silver

logger = logging.getLogger("pipeline")

logging.basicConfig(level=logging.INFO)
HISTORY_DAYS = 365 * 5
today = date.today()
def main() -> int:
   # logging.basicConfig(level=logging.INFO,
    #                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        download_raw(today - timedelta(days=HISTORY_DAYS), today)
        build_silver()
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return 1
    
    logger.info("Pipeline finished successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
