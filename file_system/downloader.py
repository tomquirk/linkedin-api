import mimetypes
import logging
import os
import requests

from file_system.utils import get_or_create_folder_path

DEFAULT_VERBOSE = False


def download_file(url, file_path_without_extension, verbose=DEFAULT_VERBOSE):
    # Send a GET request
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Ensure the request was successful

    # Try to extract the file extension from the Content-Type header
    content_type = response.headers.get('Content-Type')
    extension = mimetypes.guess_extension(
        content_type) if content_type else None

    # If we couldn't find an extension, default to '.bin'
    if not extension:
        extension = '.bin'

    if verbose:
        logging.info(f"Guessed the file extension as {extension}")

    get_or_create_folder_path(file_path_without_extension)

    file_path = f"{file_path_without_extension}{extension}"

    if verbose:
        logging.info(f"Downloading file from {url}")

    # Write the response content to a file
    with open(file_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

        if verbose:
            logging.info(f"Downloaded file to {file_path}")

    return file_path
