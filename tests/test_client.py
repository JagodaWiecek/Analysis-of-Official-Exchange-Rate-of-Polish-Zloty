from datetime import date, timedelta

import pytest
from src.client import date_windows, MAX_DAYS, fetch_window, date_windows, download_raw
from unittest.mock import Mock, patch
import requests
import json
#TO REMOVE
import logging
logger = logging.getLogger(__name__)

#START, END = date(2025, 1, 1), date(2025, 12, 31)
"""
Test for the whole date window, ensuring that the start and end dates are not lost in the window generation process. 
The first window should start with the start date, and the last window should end with the end date.
"""
def test_first_and_last_window_match_range():
    start, end = date(2025, 1, 1), date(2025, 12, 31)
    windows = list(date_windows(start, end))
    assert windows[0][0] == start
    assert windows[-1][1] == end
"""
Test to ensure that there are no gaps or overlaps between the generated date windows.
"""
def test_windows_have_no_gaps_or_overlaps():
    windows = list(date_windows(date(2021, 1, 1), date(2025, 12, 31)))
    for (_, prev_end), (next_start, _) in zip(windows, windows[1:]):
        assert next_start == prev_end + timedelta(days=1)

"""
To ensure that each time period does not exceed the maximum allowed by the NBP API, 
we check that the number of days in each window is less than or equal to MAX_DAYS.  
"""
def test_no_window_exceeds_api_limit():
    for win_start, win_end in date_windows(date(2021, 1, 1), date(2025, 12, 31)):
        assert (win_end - win_start).days + 1 <= MAX_DAYS

"""
Test to verify that the function handles a short date range correctly, returning a single window that matches the start and end dates.
"""
def test_short_range_gives_single_window():
    start, end = date(2025, 1, 1), date(2025, 1, 31)
    assert list(date_windows(start, end)) == [(start, end)]

"""
To verify that the function can handle a date range that is exactly equal to one day.
"""
def test_single_day():
    day = date(2025, 1, 1)
    assert list(date_windows(day, day)) == [(day, day)]

"""
Test to verify that the function returns a single window when the date range is exactly equal to the maximum allowed by the NBP API.
"""
def test_range_of_exactly_limit_is_one_window():
    start = date(2025, 1, 1)
    end = start + timedelta(days=MAX_DAYS - 1)
    assert list(date_windows(start, end)) == [(start, end)]

"""
Test to verify that the function returns two windows when the date range is exactly equal to the maximum allowed by the NBP API plus one day.
"""
def test_range_of_limit_plus_one_day_is_two_windows():
    start = date(2025, 1, 1)
    end = start + timedelta(days=MAX_DAYS)
    assert len(list(date_windows(start, end))) == 2

"""
To verify the incorrect input handling, we check that the function returns an empty list when the start date is after the end date.
"""
def test_start_after_end_gives_no_windows():
    assert list(date_windows(date(2025, 2, 1), date(2025, 1, 1))) == []
"""
To test function handling the custom window size, we use pytest's parametrize feature to run the test with different max_days values.
We check that the generated windows do not exceed the specified max_days for each test case.
"""
@pytest.mark.parametrize("max_days", [1, 7, 30, 120, 365])
def test_custom_window_size(max_days):
    for win_start, win_end in date_windows(date(2024, 1, 1), date(2026, 1, 1), max_days):
        assert (win_end - win_start).days + 1 <= max_days

"""
The function to create a mock response object for testing the fetch_window function
"""
def make_response(status: int, payload=None) -> Mock:
    response = Mock()
    response.status_code = status
    response.json.return_value = payload
    if status >= 400 and status != 404:
        response.raise_for_status.side_effect = requests.HTTPError(f"{status}")
    return response

START, END = date(2025, 1, 1), date(2025, 1, 10)
"""
To test the fetch_window function, if it returns the expected JSON payload when the API call is successful, status code 200
"""
@patch("src.client.requests.get")
def test_returns_json_on_success(mock_get):
    payload = [{"effectiveDate": "2025-01-02", "rates": []}]
    mock_get.return_value = make_response(200, payload)
    assert fetch_window(START, END) == payload
"""
To verify if the function raises an HTTPError or returns an empty list when the API call returns a 404 status code,
indicating that the requested data is not found
"""
@patch("src.client.requests.get")
def test_404_returns_empty_list(mock_get):
    mock_get.return_value = make_response(404)
    assert fetch_window(START, END) == []
"""
To verify that the function raises an HTTPError for other error status codes (400, 500, 503), 
indicating that the API call failed for reasons other than data not being found.
"""
@pytest.mark.parametrize("status", [400, 500, 503])
@patch("src.client.requests.get")
def test_other_errors_raise(mock_get, status):
    mock_get.return_value = make_response(status)
    with pytest.raises(requests.HTTPError):
        fetch_window(START, END)

"""
Verifies that the proper amount of files are downoloaded 
and the function is called the expected number of times when downloading raw data for a given date range.
"""
@patch("src.client.fetch_window")
def test_creates_one_file_per_window(mock_fetch, tmp_path):
    mock_fetch.return_value = [{"effectiveDate": "2025-01-02"}]
    download_raw(START, END, raw_dir=tmp_path)

    expected = len(list(date_windows(START, END)))
    assert len(list(tmp_path.glob("tables_a_*.json"))) == expected
    assert mock_fetch.call_count == expected

"""
Verifies that windows without data save an empty list to the corresponding JSON file, ensuring that the function handles cases where the API returns no data for a given date range.
"""
@patch("src.client.fetch_window")
def test_window_without_data_saves_empty_list(mock_fetch, tmp_path):
    mock_fetch.return_value = []
    download_raw(date(2025, 1, 1), date(2025, 1, 2), raw_dir=tmp_path)

    files = list(tmp_path.glob("*.json"))
    assert json.loads(files[0].read_text(encoding="utf-8")) == []

"""
To verify if the function creates the target directory if it does not exist, 
ensuring that the function can handle cases where the specified raw_dir is missing
"""
@patch("src.client.fetch_window")
def test_creates_missing_directory(mock_fetch, tmp_path):
    mock_fetch.return_value = []
    target = tmp_path / "nested" / "raw"
    download_raw(date(2025, 1, 1), date(2025, 1, 2), raw_dir=target)
    assert target.is_dir()


"""
Verifies the correctness of the filenames generated by the download_raw function, 
ensuring that they contain the start and end dates of the corresponding data window.
"""
@pytest.mark.parametrize(
    "start, end",
    [
        (date(2025, 1, 1), date(2025, 1, 10)),
        (date(2025, 2, 1), date(2025, 2, 28)),
        (date(2025, 12, 20), date(2026, 1, 10)),
    ],
)
@patch("src.client.fetch_window", return_value=[])
def test_filename_contains_window_dates( tmp_path, start, end):
    download_raw(start, end, raw_dir=tmp_path)
    assert (tmp_path / f"tables_a_{start}_{end}.json").exists()
