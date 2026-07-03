"""Collect and download Hungarian population Excel datasets from government web pages.

This module is responsible for:
- scraping official government sources for Excel datasets
- filtering relevant population files
- downloading raw Excel files into local storage

Functions:
    get_excel_urls: Scrape Excel links from the configured government URL.
    load_workbook: Load an Excel workbook into a pandas ExcelFile object.
    download_excel_file: Download a remote Excel file to the raw data directory.
    is_population_excel: Validate whether a workbook contains population data.
    collect_population_datasets: Entry point for collecting population Excel files.
"""

from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from hpm.settings import settings

GOV_URL = "https://kormany.hu/nyilvantartasok/statisztika/lakossagi-szamadatok"


def get_excel_urls(url: str) -> list[str]:
    """Return all downloadable Excel file URLs found on a page.

    Args:
        url: The URL of the government statistics page to inspect.

    Returns:
        A list of Excel download URLs ending with .xls or .xlsx.

    Raises:
        requests.HTTPError: If the HTTP request to the page fails.
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    excel_links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if href.endswith((".xls", ".xlsx")):
            excel_links.append(href)

    return excel_links


def load_workbook(excel_url: str) -> pd.ExcelFile:
    """Load a remote Excel workbook into a pandas ExcelFile object.

    Args:
        excel_url: The direct URL to a remote Excel workbook.

    Returns:
        A pandas ExcelFile instance encapsulating the remote workbook.

    Raises:
        requests.HTTPError: If the HTTP request for the workbook fails.
    """
    response = requests.get(excel_url, timeout=30)
    response.raise_for_status()
    xls = BytesIO(response.content)

    return pd.ExcelFile(xls)


def download_excel_file(excel_url: str) -> Path:
    """Download an Excel file and save it under the raw data directory.

    If the target file already exists, the download is skipped.

    Args:
        excel_url: The direct URL to the remote Excel file.

    Returns:
        The local filesystem path to the downloaded or existing file.

    Raises:
        requests.HTTPError: If the HTTP request for the file fails.
    """
    settings.raw_population.mkdir(parents=True, exist_ok=True)

    filename = excel_url.split("/")[-1]
    filepath = settings.raw_population / filename

    if filepath.exists():
        print(f"Skipping {filename}")
        return filepath

    response = requests.get(excel_url, timeout=30)
    response.raise_for_status()

    with open(filepath, "wb") as f:
        f.write(response.content)

    print(f"Downloaded {filename}")

    return filepath


def is_population_excel(xls: pd.ExcelFile) -> bool:
    """Determine whether a workbook likely contains population data.

    The heuristic is based on the number of rows in the first sheet. Population
    datasets are expected to be substantially larger than ancillary Excel files.

    Args:
        xls: A pandas ExcelFile object to validate.

    Returns:
        True if the first sheet has more than 1,000 rows, otherwise False.
    """
    df = pd.read_excel(xls, sheet_name=0)
    return df.shape[0] > 1000


def collect_population_datasets():
    """Download all population Excel files from the government page."""
    excel_urls = get_excel_urls(GOV_URL)
    for url in excel_urls:
        xl = load_workbook(url)
        if not is_population_excel(xl):
            continue
        download_excel_file(url)


if __name__ == "__main__":
    collect_population_datasets()
