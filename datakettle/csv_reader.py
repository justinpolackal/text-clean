import os
from datakettle.cleantext.textcleaner import TextCleaner
from datakettle.cleantext.filereader import TextFileReader
import datakettle.cleantext.utils as utils
import logging

class CSVReader (object):

    def __init__(self, source_config):
        self.source_config = source_config
        self.logger = logging.getLogger(__name__)

        self.def_special_chars = ['MINUS', 'COMMA', 'DQUOTE', 'SQUOTE', 'FSLASH', 'BSLASH', 'HASH', 'AT', 'EXCL', 'CARAT',
                          'AMP', 'PCT', 'DOLLAR', 'TILDA', 'APOS', 'COLN', 'SCOLN', 'QMARK', 'LT', 'GT', 'EQ', 'PIPE', 'CBRACE',
                          'SBRKT','BRKT', 'USCORE', 'ASTRSK', 'DOT', 'PLUS']

        self.def_white_space_chars = ["NEWLINE", 'CR', 'FF', 'TAB']

    """
    Read local csv files from configured directory path
    """
    def read_local_files (self):
        tfr = TextFileReader ()
        tc = TextCleaner ()
        access = self.source_config["access"]

        file_filter = ""
        if access["file_filter"] :
            file_filter = access["file_filter"]

        # Read column delimiter
        delimiter = ","
        if "delimiter" in access:
            delimiter = utils.if_null(access["delimiter"], ",")

        header_row = None
        if "header_row" in access:
            header_row = utils.if_null(access["header_row"], None)

        data_column = 0
        if "data_column" in access:
            data_column = utils.if_null(access["data_column"], 0)

        label_column = None
        if "label_column" in access:
            label_column = utils.if_null(access["label_column"], None)

        usecols = []
        usecols.append(data_column)

        if label_column is not None:
            usecols.append(label_column)

        # If a label is provided globally, read it from config.
        # Label will be the class/prediction used for training purposes.
        global_label_value = None
        if "label_value_override" in access:
            global_label_value = utils.if_null(access["label_value_override"], None)

        # Read file names from given path
        files_list = utils.get_files_in_path(access["path"], file_filter)

        file_data_list = []
        label_value_list = []
        for file in files_list:

            # read csv file as a pandas dataframe
            data_df = tfr.read_csv_file (file_path=file, separator=delimiter, header_row=header_row, select_cols=usecols)

            self.logger.info("Found {} markup documents ".format(len(data_df)))

            if utils.df_size(data_df) < 1:
                continue

            # Convert data column (text rows) into a list
            text_list = list(data_df.iloc[:,0].values)

            # If label column is specified, convert label column into list
            if label_column is not None:
                label_list = list(data_df.iloc[:,1].values)

            # Iterate through each text row
            id = 0
            for textdoc in text_list:

                clean_data = self.cleanup_data(textdoc)

                if clean_data is not None and len(clean_data.strip()) > 0:
                    file_data_list.append(clean_data)

                    # if a label is provided globally, append it to labels list for each document
                    if global_label_value is not None:
                        label_value_list.append(global_label_value)
                    else:
                        if label_column is not None:
                            label_value_list.append(label_list[id])
                id += 1

        return file_data_list, label_value_list

    """
    Read json files from an S3 path
    """
    def read_s3_files (self, config):
        self.logger.error ("S3 file reader: Not yet implemented")
        return [], []

    """
    Cleanup file data list using the cleaning steps listed within the sources section of the feed config JSON
    """
    def cleanup_data (self, clean_data):
        if clean_data is None or len(clean_data) < 1:
            return ""

        tc = TextCleaner()
        clean_steps = self.source_config["clean"]

        # Iterate through each step and perform specified cleaning action
        for cstep in clean_steps:

            stepname = cstep["step"]

            #self.logger.info("Processing: {}".format(stepname))

            if stepname == "remove_all_markup":
                clean_data = tc.remove_all_markup (doc=clean_data, valid_markup=False)

            if stepname == "remove_html_encoded_chars":
                clean_data = tc.remove_html_encoded_chars(clean_data, replace_char=' ')

            if stepname == "remove_special_chars":
                if "special_chars" in cstep:
                    special_chars = cstep["special_chars"]
                else:
                    special_chars = self.def_special_chars
                clean_data = tc.remove_special_chars (special_chars, clean_data)

            if stepname == "remove_white_spaces":
                if "white_space_chars" in cstep:
                    white_space_chars = cstep["white_space_chars"]
                else:
                    white_space_chars = self.def_white_space_chars

                clean_data = tc.remove_white_spaces(white_space_chars=white_space_chars, doc=clean_data)

        return clean_data

    """
    From the config, understand the file endpoint. It can be local file system or Amazon S3. 
    Call read function as necessary
        
    Clean up data as specified in the config and return to model builder
    """
    def read_csv_data (self):

        access = self.source_config["access"]

        # Read data from markup files
        if (access["endpoint"] == "csv") and (access["filesystem"] == "local"):
            self.logger.info ("Reading local text files from {}".format(access["path"]))
            data_list, label_list = self.read_local_files ()

        if (access["endpoint"] == "csv") and (access["filesystem"] == "s3"):
            self.logger.info("Reading s3 text files from {}".format(access["path"]))
            data_list, label_list = self.read_s3_files ()

        return data_list, label_list

