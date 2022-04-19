import os
import numpy as np
import pandas as pd
import logging
from . import utils


class TextFileReader (object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

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