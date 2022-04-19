import os
import numpy as np
import pandas as pd
import logging
from . import utils
import urllib3

class TextFileReader (object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.http_pool_manager = urllib3.PoolManager()

    def read_file (self, file_path):
        fh = None
        file_data = None

        try:
            fh = open(file_path, mode='r', encoding="utf8")

            file_data = fh.read()

            self.logger.info("Read: {} chars from {}.".format(len(file_data), file_path))

        except IOError as ioerror:
            self.logger.error ("Error Occurred while reading: ", exc_info=True)

        finally:
            if (fh):
                fh.close()

        return file_data

    """
    Read a csv file into a pandas dataframe.
    """
    def read_csv_file (self, file_path, separator=",", header_row=None, select_cols=None):
        """
        :param file_path: CSV file path and file name
        :param separator: Column delimiter. Defaults to ,
        :param header_row: Integer row position of the header row. Defaults to None indicating no header row
        :param select_cols: List of columns to read. If None, selects all columns from the file
        :return: Pandas dataframe
        """
        df = None

        separator = utils.if_null(separator, ",")
        header = utils.if_null(header_row, None)

        try:
            if select_cols is not None:
                df = pd.read_csv(file_path, sep=separator, header=header, usecols=select_cols)
            else:
                df = pd.read_csv(file_path, sep=separator, header=header)

        except Exception as ex:
            self.logger.error("Error Occurred while reading: ", exc_info=True)

        return df

    """
    Read contents of a text file line by line
    """
    def read_file_by_line(self, file_path):
        fh = None
        file_data = None

        try:
            fh = open(file_path, mode='r', encoding="utf8")

            file_data = fh.readlines()

            self.logger.info("Read: {} lines from {}.".format(len(file_data), file_path))

        except IOError as ioerror:
            self.logger.error ("Error Occurred while reading: ", exc_info=True)

        finally:
            if (fh):
                fh.close()

        return file_data
    """
    Read contents of a web page using the given http url
    """
    def read_web_page(self, url):
        file_data = None

        try:
            resp = self.http_pool_manager.request('GET', url)
            assert resp.status == 200, f"Error reading from {url}"

            file_data = str(resp.data, 'utf-8')

        except AssertionError as msg:
            self.logger.error(msg)
        except Exception as e:
            self.logger.error(e)

        return file_data