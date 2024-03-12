
import pathlib
import platform
from os import listdir, path
from posixpath import join

IGNORED_FILE_SET = set(['.DS_Store'])


def refine_path(path: str):
    return str(pathlib.WindowsPath(path) if platform.system() == 'Windows' else pathlib.PurePath(path))


def get_file_paths(folder_path: str, ignored_file_set=IGNORED_FILE_SET, recursive=False):
    if not path.exists(folder_path):
        return []

    if not recursive:
        return [join(folder_path, file_name) for file_name in listdir(folder_path) if path.isfile(join(folder_path, file_name)) and file_name not in ignored_file_set]
    else:
        def internal_get_file_paths(folder_path: str, ignored_file_set=set()):
            file_paths = []
            for item in listdir(folder_path):
                full_path = path.join(folder_path, item)
                if path.isfile(full_path) and item not in ignored_file_set:
                    # Add the file path if it's a file and not ignored
                    file_paths.append(full_path)
                elif path.isdir(full_path):
                    # Recursively search in subdirectories for files
                    file_paths.extend(internal_get_file_paths(
                        full_path, ignored_file_set))
            return file_paths

        return internal_get_file_paths(folder_path, ignored_file_set)


def get_folder_paths(folder_path: str, ignored_folder_set=set(), recursive=False):
    if not path.exists(folder_path):
        return []

    if not recursive:
        return [join(folder_path, folder_name) for folder_name in listdir(folder_path) if path.isdir(join(folder_path, folder_name)) and folder_name not in ignored_folder_set]
    else:
        def internal_get_folder_paths(folder_path: str, ignored_folder_set=set()):
            folder_paths = []
            for folder_name in listdir(folder_path):
                full_path = path.join(folder_path, folder_name)
                if path.isdir(full_path) and folder_name not in ignored_folder_set:
                    # Add the current folder path
                    folder_paths.append(full_path)
                    # Recursively add paths from subfolders
                    folder_paths.extend(internal_get_folder_paths(
                        full_path, ignored_folder_set))
            return folder_paths

        return internal_get_folder_paths(folder_path, ignored_folder_set)
