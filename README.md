# Analysis-of-Official-Exchange-Rate-of-Polish-Zloty
The project aims to analyse the exchange rates of the Polish zloty against the euro, US dollar, pound sterling and Japanese yen.

 ## Quick start
 python -m venv .venv

.venv\Scripts\activate.bat

pip install -r requirements.txt

python -m pytest

python main.py

python main.py --skip-download #this commend ignores the downloading process, better to use if JSON files are downloaded



## Architecture
data/raw       | bronze | raw JSON files downloaded from https://api.nbp.pl/en.html , each file contains 93 days of the exchange rates
data/processed | silver | cleared data with all currencies, saved to CSV file in column format : date, code, currency, mid
data/output | gold | two CSV files: one containing the selected currencies and the other containing the minimum, maximum and extreme analysis and plots.

## Project structure
```text
project/
├── data/
│   ├── raw/                # Raw JSON responses from the NBP API
│   ├── processed/          # Cleaned exchange rates in CSV format
│   └── output/             # Cleaned data with extreme calculations and currency analysis in CVS format and plots
│       └── plots/          # Generated plots based on cleaned data from output 
├── src/
│   ├── __init__.py
│   ├── client.py            # Downloading data from the API
│   ├── transform.py         # Loading, transforming and validating data
│   ├── analysis.py          # Extracting the information and the currencies  
│   └── plots.py 
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_transform.py
│   └── test_analysis.py
├── requirements.txt
├── main.py
└── README.md
```
## Design decisions
### Dataset structure
I considered two dataset layouts: a wide format with one row per date and a separate column for each currency, and a long format with one row per date and currency. I chose the long format, using the columns `date`, `code`, `currency`, and `mid`. Dates repeat across rows, with each row containing the exchange rate for a different currency. This keeps the schema consistent when currencies are added or removed and makes filtering, grouping, and validation straightforward.
### Processing tool
I chose pandas rather than PySpark because the dataset is small enough to process in memory on a single machine. At this scale, PySpark would add setup and execution overhead without a meaningful benefit. Due to the scale, I saved the data as a .csv file; for a larger scale, I would use a .parquet file