import pandas as pd
import pytest
import json
from src.transform import (
    build_silver, load_processed, load_raw, save_processed, to_dataframe, validate,
)
#valid table
TABLES = [
    {"effectiveDate": "2025-01-02",
     "rates": [{"currency": "euro", "code": "EUR", "mid": 4.2},
               {"currency": "korona czeska", "code": "CZK", "mid": 0.17}]},
    {"effectiveDate": "2025-01-03",
     "rates": [{"currency": "euro", "code": "EUR", "mid": 4.3},
               {"currency": "korona czeska", "code": "CZK", "mid": 0.18}]},
]
#Table with some missing exchange rates
TABLES_NA = [
    {"effectiveDate": "2025-01-04", 
     "rates": [{"currency": "euro", "code": "EUR", "mid": 4.2},
               {"currency": "korona czeska", "code": "CZK", "mid": None}]},
    {"effectiveDate": "2025-01-05",
     "rates": [{"currency": "euro", "code": "EUR", "mid": None},
               {"currency": "korona czeska", "code": "CZK", "mid": 0.18}]},
]

def write_raw(folder, name, tables):
    (folder / name).write_text(json.dumps(tables), encoding="utf-8") 

"""
verify that the to_dataframe function correctly transforms the list of dictionaries into a pandas DataFrame 
with the expected structure and data types
"""
def test_keeps_all_currencies():
    df = to_dataframe(TABLES)
    assert set(df["code"]) == {"EUR", "CZK"}
    assert len(df) == 4

"""
Verifies that the to_dataframe function raises a KeyError when the input data are in unexpected format
"""
def test_KeyError():
    bad = [{"effectiveDate": "2025-01-02", "rates": [{"currency": "euro", "code": "EUR"}]}]
    with pytest.raises(ValueError):
        to_dataframe(bad)
 
"""
Validates that the to_dataframe function correctly parses and sorts the date column, 
ensuring that the dates are in datetime format and sorted in increasing order for each currency code.
"""
def test_dates_are_parsed_and_sorted():
    df = to_dataframe(TABLES[::-1])
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    eur = df[df["code"] == "EUR"]
    assert eur["date"].is_monotonic_increasing

"""
The function verifies that the to_dataframe function correctly handles duplicate rows and missing values in the input data
"""
def test_duplicates_and_missing_values_are_removed():
    df = to_dataframe(TABLES+ TABLES_NA )
    assert len(df) == 6
"""
The function checks that the validate function raises a ValueError when the DataFrame contains negative rates, 
ensuring that the validation logic correctly identifies and handles invalid data.
"""
def test_validate_fails_on_non_positive_rate():
    bad = to_dataframe(TABLES)
    bad.loc[0, "mid"] = -1
    with pytest.raises(ValueError):
        validate(bad)
"""
The function verifies the data types of the columns in the DataFrame returned by the to_dataframe function
"""
def test_to_dataframe_has_expected_columns_and_types():
    df = to_dataframe(TABLES)
    assert list(df.columns) == ["date", "code", "currency", "mid"]
    assert df["mid"].dtype == float
"""
Verifies that the to_dataframe function correctly handles an empty input list, returning an empty DataFrame with the expected columns
"""
def test_to_dataframe_handles_empty_input():
    df = to_dataframe([])
    assert df.empty
    assert list(df.columns) == ["date", "code", "currency", "mid"]

"""
Verifies that for properly formatted data, the validate function does not raise any exceptions, 
confirming that the validation logic correctly identifies valid data.
"""
def test_validate_passes_on_good_data():
    validate(to_dataframe(TABLES))
"""
To verify that the validate function raises a ValueError when the DataFrame is empty,
"""
def test_validate_fails_on_empty_dataframe():
    with pytest.raises(ValueError):
        validate(to_dataframe([]))
"""
Function ensures that the loaded information properly merges
"""
def test_load_raw_merges_files_in_order(tmp_path):
    write_raw(tmp_path, "tables_a_2025-01-01_2025-01-02.json", [TABLES[0]])
    write_raw(tmp_path, "tables_a_2025-01-03_2025-01-04.json", [TABLES[1]])
    tables = load_raw(tmp_path)
    assert [t["effectiveDate"] for t in tables] == ["2025-01-02", "2025-01-03"]
"""
Function verifies that in case of one empty pile merged with a non-empty file, the output file contains only the non-empty data
"""
def test_load_raw_skips_empty_windows(tmp_path):
    write_raw(tmp_path, "tables_a_2025-01-01_2025-01-02.json", [])
    write_raw(tmp_path, "tables_a_2025-01-03_2025-01-04.json", [TABLES[1]])
    assert len(load_raw(tmp_path)) == 1

"""
To verify that in case of no files in the directory, the load_raw function raises a FileNotFoundError
"""
def test_load_raw_raises_when_no_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_raw(tmp_path)
"""
The test of silver data process and saves it to a CSV file, 
ensuring that the build_silver function correctly transforms and validates the data, 
and that the output file is created as expected.
"""
def test_build_silver_creates_csv(tmp_path):
    write_raw(tmp_path, "tables_a_2025-01-01_2025-01-10.json", TABLES)
    out = tmp_path / "out" / "rates.csv"
    df = build_silver(raw_dir=tmp_path, out_path=out)
    assert out.exists()
    assert len(df) == 4