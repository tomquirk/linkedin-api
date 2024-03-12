from datetime import datetime
from os import makedirs, path


def get_date_string():
    return str(datetime.now()).replace(':', '_').replace(' ', '_')


def get_folder_path(full_path):
    return path.dirname(full_path)


def get_or_create_folder_path(full_path):
    folder_path = get_folder_path(full_path)
    if not path.exists(folder_path):
        makedirs(folder_path)
