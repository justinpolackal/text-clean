import os
from datakettle.cleantext.textcleaner import TextCleaner
from datakettle.cleantext.filereader import TextFileReader
import datakettle.cleantext.utils as utils
import logging

class JsonReader (object):

    def __init__(self, source_config):
        self.source_config = source_config
        self.logger = logging.getLogger(__name__)

        self.def_special_chars = ['MINUS', 'COMMA', 'DQUOTE', 'SQUOTE', 'FSLASH', 'BSLASH', 'HASH', 'AT', 'EXCL', 'CARAT',
                          'AMP', 'PCT', 'DOLLAR', 'TILDA', 'APOS', 'COLN', 'SCOLN', 'QMARK', 'LT', 'GT', 'EQ', 'PIPE', 'CBRACE',
                          'SBRKT','BRKT', 'USCORE', 'ASTRSK', 'DOT', 'PLUS']

        self.def_white_space_chars = ["NEWLINE", 'CR', 'FF', 'TAB']

    """
    Read local json files from configured directory path
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

        # Which data element is to be read from the JSON object for text data
        data_element = access["data_element"]

        # If a label is provided globally, read it from config.
        # Label will be the class/prediction used for training purposes.
        global_label_value = None
        if "label_value_override" in access:
            global_label_value = access["label_value_override"]

        file_data_list = []
        label_value_list = []
        for file in files_list:

            # read file content and convert json string to dictionary
            data = tc.string_to_json_object(tfr.read_file (file) )

            # JSON read from the file can be a single object or an array of objects.
            # Check if this is a single JSON object
            if isinstance(data, dict):

                # Label value to be used for training purposes.
                label_value = None
                if "label_element" in data:
                    label_value = utils.if_null(data["label_element"], None)

                if (data_element in data):
                    text_data = data[data_element]
                    clean_data = self.cleanup_data(text_data)

                    # After cleanup, if there is valid text, then append to the list of documents
                    if clean_data is not None and len(clean_data.strip()) > 0:
                        file_data_list.append(clean_data)

                        # Append the label value as well. Take care of global override, if provided
                        if global_label_value is not None:
                            label_value_list.append(global_label_value)
                        else:
                            label_value_list.append(label_value)

            # Check if this is an array of JSON objects. Then iterate through each object
            if isinstance(data, list):
                for jsonobj in data:

                    # Label value to be used for training purposes.
                    label_value = None
                    if "label_element" in jsonobj:
                        label_value = utils.if_null(jsonobj["label_element"], None)

                    if data_element in jsonobj:

                        text_data = jsonobj[data_element]
                        clean_data = self.cleanup_data(text_data)

                        # After cleanup, if there is valid text, then append to the list of documents
                        if clean_data is not None and len(clean_data.strip()) > 0:
                            file_data_list.append(clean_data)

                            # Append the label value as well. Take care of global override, if provided
                            if global_label_value is not None:
                                label_value_list.append(global_label_value)
                            else:
                                label_value_list.append(label_value)

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
        tc = TextCleaner()
        clean_steps = self.source_config["clean"]

        # Iterate through each step and perform specified cleaning action
        for cstep in clean_steps:

            stepname = cstep["step"]

            if stepname == "remove_all_markup":
                clean_data = tc.remove_all_markup (clean_data, valid_markup=False)

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
    def read_json_data (self):

        access = self.source_config["access"]

        # Read data from JSON files
        if (access["endpoint"] == "file") and (access["filesystem"] == "local"):
            self.logger.info ("Reading local json files from {}".format(access["path"]))
            data_list, label_list = self.read_local_files ()

        if (access["endpoint"] == "file") and (access["filesystem"] == "s3"):
            self.logger.info("Reading s3 json files from {}".format(access["path"]))
            data_list, label_list = self.read_s3_files ()

        return data_list, label_list

