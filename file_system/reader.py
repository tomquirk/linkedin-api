import os
import csv
import json
import logging
import pandas as pd

DEFAULT_ENCODING = 'utf-8'
DEFAULT_VERBOSE = False
DEFAULT_EXCEL_SHEET_NAME = 'Sheet1'


def read_json(file_path: str, verbose=DEFAULT_VERBOSE, encoding=DEFAULT_ENCODING):
    data = None

    if os.path.isfile(file_path):
        with open(file_path, encoding=encoding) as jsonFile:
            data = json.load(jsonFile)

            if verbose:
                logging.info(f"Read JSON data from {file_path}")

    return data


def read_html(file_path: str, verbose=DEFAULT_VERBOSE, encoding=DEFAULT_ENCODING):
    data = None

    if os.path.isfile(file_path):
        with open(file_path, encoding=encoding) as file:
            data = ''.join(file.readlines())

        if verbose:
            logging.info(f"Read HTML data from {file_path}")

    return data


def read_text(file_path: str, verbose=DEFAULT_VERBOSE, encoding=DEFAULT_ENCODING):
    data = None

    if os.path.isfile(file_path):
        with open(file_path, encoding=encoding) as file:
            data = ''.join(file.readlines())

        if verbose:
            logging.info(f"Read TXT data from {file_path}")

    return data


def read_csv(file_path: str, verbose=DEFAULT_VERBOSE, encoding=DEFAULT_ENCODING) -> list[dict] | None:
    data = None

    if os.path.isfile(file_path):
        with open(file_path, newline='', encoding=encoding) as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            data = [row for row in spamreader]

            if verbose:
                logging.info(
                    f"Read CSV data from {file_path} with {len(data)} rows")

    return data


def read_excel(file_path: str, sheet_name: str = DEFAULT_EXCEL_SHEET_NAME, verbose=DEFAULT_VERBOSE) -> list[dict] | None:
    data = None

    if os.path.isfile(file_path):
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        data = df.to_dict(orient='records')

        if verbose:
            logging.info(
                f"Read EXCEL data from {file_path} with {len(data)} rows")

    return data
