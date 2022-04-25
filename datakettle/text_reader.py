import os
from datakettle.cleantext.textcleaner import TextCleaner
from datakettle.cleantext.filereader import TextFileReader
import datakettle.cleantext.utils as utils
import logging

class TextReader (object):

    def __init__(self, source_config):
        self.source_config = source_config
        self.logger = logging.getLogger(__name__)

        self.def_special_chars = ['MINUS', 'COMMA', 'DQUOTE', 'SQUOTE', 'FSLASH', 'BSLASH', 'HASH', 'AT', 'EXCL', 'CARAT',
                          'AMP', 'PCT', 'DOLLAR', 'TILDA', 'APOS', 'COLN', 'SCOLN', 'QMARK', 'LT', 'GT', 'EQ', 'PIPE', 'CBRACE',
                          'SBRKT','BRKT', 'USCORE', 'ASTRSK', 'DOT', 'PLUS']

        self.def_white_space_chars = ["NEWLINE", 'CR', 'FF', 'TAB']

    """
    Read local text files from configured directory path
    """
    def read_local_files (self):
        tfr = TextFileReader ()
        tc = TextCleaner ()
        access = self.source_config["access"]

        file_filter = ""
        if access["file_filter"] :
            file_filter = access["file_filter"]

        # Read file names from given path
        files_list = utils.get_files_in_path(access["path"], file_filter)

        file_data_list = []
        label_value_list = []
        for file in files_list:

            # read file content and convert json string to dictionary
            file_data = tfr.read_file (file)

            # Text data that is read from the file may contain one or more text documents, separated by some character or string
            # Split them into a list of docs

            if "document_separator" in access:
                separator_code = access["document_separator"]
                multi_docs = tc.split_multi_text_by_separator(file_data, separator_code=separator_code)
            else:
                multi_docs = [file_data]

            # If a label is provided globally, read it from config.
            # Label will be the class/prediction used for training purposes.
            global_label_value = None
            if "label_value_override" in access:
                global_label_value = access["label_value_override"]

            self.logger.info("Found {} markup documents ".format(len(multi_docs)))

            # Iterate through each markup document
            for textdoc in multi_docs:
                clean_data = self.cleanup_data(textdoc)
                file_data_list.append({"content":clean_data, "label":global_label_value})

        return file_data_list

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

                replace_char = cstep["replace_char"] if cstep.get("replace_char") else ''
                clean_data = tc.remove_white_spaces(white_space_chars=white_space_chars, doc=clean_data, replace_char=replace_char)

        return clean_data

    """
    From the config, understand the file endpoint. It can be local file system or Amazon S3. 
    Call read function as necessary
        
    Clean up data as specified in the config and return to model builder
    """
    def read_text_data (self):

        access = self.source_config["access"]

        # Read data from markup files
        if (access["endpoint"] == "file") and (access["filesystem"] == "local"):
            self.logger.info ("Reading local text files from {}".format(access["path"]))
            data_list = self.read_local_files ()

        if (access["endpoint"] == "file") and (access["filesystem"] == "s3"):
            self.logger.info("Reading s3 text files from {}".format(access["path"]))
            data_list = self.read_s3_files ()

        return data_list

