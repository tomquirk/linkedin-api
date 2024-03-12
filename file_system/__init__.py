
import gzip
from os import makedirs
from os.path import isfile, exists
from file_system.downloader import download_file as static_download_file
from .finder import IGNORED_FILE_SET, get_file_paths, get_folder_paths, refine_path as static_refine_path
from .reader import DEFAULT_ENCODING, DEFAULT_EXCEL_SHEET_NAME, DEFAULT_VERBOSE, read_text, read_csv, read_excel, read_html, read_json
from .writer import DEFAULT_OVERWRITE, write_csv, write_excel, write_html, write_json, write_text


class FileSystem:
    def __init__(self, path=None, verbose=DEFAULT_VERBOSE, encoding=DEFAULT_ENCODING):
        self.path = path
        self.verbose = verbose
        self.encoding = encoding

    def __get_path(self, path):
        path = path if path is not None else self.path

        if not path:
            raise Exception('Path must be specified')

        return path

    def __prepare_folder(self, path):
        # Auto create folder if it doesn't exist
        folder_path = '/'.join(path.split('/')[:-1])
        if not exists(folder_path):
            makedirs(folder_path)

    def read(self, path=None, verbose=None, encoding=None, excel_sheet_name=DEFAULT_EXCEL_SHEET_NAME):
        path = self.__get_path(path)
        verbose = verbose if verbose is not None else self.verbose
        encoding = encoding if encoding is not None else self.encoding

        if isfile(path):
            if path[-5:] == '.json':
                return read_json(file_path=path, verbose=verbose, encoding=encoding)
            elif path[-5:] == '.html':
                return read_html(file_path=path, verbose=verbose, encoding=encoding)
            elif path[-4:] == '.txt' or path[-4:] == '.log':
                return read_text(file_path=path, verbose=verbose, encoding=encoding)
            elif path[-4:] == '.csv':
                return read_csv(file_path=path, verbose=verbose, encoding=encoding)
            elif path[-5:] == '.xlsx':
                return read_excel(file_path=path, sheet_name=excel_sheet_name, verbose=verbose)
            else:
                raise Exception(f"Unsupported file type for {path}")

    def write(self, data, path=None, verbose=None, csv_and_excel_overwrite=DEFAULT_OVERWRITE, encoding=None, csv_fieldnames=None, excel_sheet_name=DEFAULT_EXCEL_SHEET_NAME, excel_enable_str_conversion=False):
        path = self.__get_path(path)
        verbose = verbose if verbose is not None else self.verbose
        encoding = encoding if encoding is not None else self.encoding

        self.__prepare_folder(path)

        if path[-5:] == '.json':
            return write_json(file_path=path, data=data, verbose=verbose, encoding=encoding)
        elif path[-5:] == '.html':
            return write_html(file_path=path, data=data, verbose=verbose, encoding=encoding)
        elif path[-4:] == '.txt' or path[-4:] == '.log':
            return write_text(file_path=path, data=data, verbose=verbose, encoding=encoding)
        elif path[-4:] == '.csv':
            return write_csv(file_path=path, data=data, fieldnames=csv_fieldnames, verbose=verbose, overwrite=csv_and_excel_overwrite, encoding=encoding)
        elif path[-5:] == '.xlsx':
            return write_excel(file_path=path, data=data, sheet_name=excel_sheet_name, verbose=verbose, overwrite=csv_and_excel_overwrite, enable_str_conversion=excel_enable_str_conversion)
        else:
            raise Exception(f"Unsupported file type for {path}")

    def unzip(self, path=None, output_path=None, verbose=None):
        path = self.__get_path(path)
        verbose = verbose if verbose is not None else self.verbose

        self.__prepare_folder(path)

        if path[-3:] == '.gz':
            with gzip.open(path, 'rb') as gz_file:
                data = gz_file.read()

                if output_path:
                    with open(output_path, 'wb') as out_file:
                        out_file.write(data)

                    if verbose:
                        print(
                            f"Unzipped data from {path} and wrote data to {output_path}")
                else:
                    if verbose:
                        print(f"Unzipped data from {path} ")

                return data
        else:
            raise Exception(f"Unsupported file type for {path}")

    def download(self, url, file_path_without_extension=None, verbose=None):
        path = self.__get_path(file_path_without_extension)
        verbose = verbose if verbose is not None else self.verbose

        self.__prepare_folder(path)

        return static_download_file(url=url, file_path_without_extension=path, verbose=verbose)

    def find_files(self, path=None, ignored_file_set=IGNORED_FILE_SET, file_suffix=None, recursive=False):
        path = path if path is not None else self.path
        file_paths = get_file_paths(path, ignored_file_set, recursive)
        if file_suffix:
            if file_suffix[0] != '.':
                file_suffix = '.' + file_suffix

            return [file_path for file_path in file_paths if file_path[-len(file_suffix):] == file_suffix]

        return file_paths

    def find_folders(self, path=None, ignored_folder_set=set(), recursive=False):
        path = path if path is not None else self.path
        return get_folder_paths(path, ignored_folder_set, recursive)

    def refine_path(self, path=None):
        path = path if path is not None else self.path
        return static_refine_path(path)


def read_file(path=None, verbose=None, encoding=None, excel_sheet_name=DEFAULT_EXCEL_SHEET_NAME):
    return FileSystem().read(path=path, verbose=verbose, encoding=encoding, excel_sheet_name=excel_sheet_name)


def write_file(data, path=None, verbose=None, csv_and_excel_overwrite=DEFAULT_OVERWRITE, encoding=None, csv_fieldnames=None, excel_sheet_name=DEFAULT_EXCEL_SHEET_NAME, excel_enable_str_conversion=False):
    return FileSystem().write(data=data, path=path, verbose=verbose, csv_and_excel_overwrite=csv_and_excel_overwrite, encoding=encoding, csv_fieldnames=csv_fieldnames, excel_sheet_name=excel_sheet_name, excel_enable_str_conversion=excel_enable_str_conversion)


def download_file(url, file_path_without_extension=None, verbose=None):
    return FileSystem().download(url=url, file_path_without_extension=file_path_without_extension, verbose=verbose)


def unzip_file(path=None, output_path=None, verbose=None):
    return FileSystem().unzip(path=path, output_path=output_path, verbose=verbose)


def find_files(path=None, ignored_file_set=IGNORED_FILE_SET, file_suffix=None, recursive=False):
    return FileSystem().find_files(path=path, ignored_file_set=ignored_file_set, file_suffix=file_suffix, recursive=recursive)


def find_folders(path=None, ignored_folder_set=set(), recursive=False):
    return FileSystem().find_folders(path=path, ignored_folder_set=ignored_folder_set, recursive=recursive)
