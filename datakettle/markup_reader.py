import os
from datakettle.cleantext.textcleaner import TextCleaner
from datakettle.cleantext.filereader import TextFileReader
import datakettle.cleantext.utils as utils
import logging

class MarkupReader (object):

    def __init__(self, source_config):
        self.source_config = source_config
        self.logger = logging.getLogger(__name__)

        self.def_special_chars = ['MINUS', 'COMMA', 'DQUOTE', 'SQUOTE', 'FSLASH', 'BSLASH', 'HASH', 'AT', 'EXCL', 'CARAT',
                          'AMP', 'PCT', 'DOLLAR', 'TILDA', 'APOS', 'COLN', 'SCOLN', 'QMARK', 'LT', 'GT', 'EQ', 'PIPE', 'CBRACE',
                          'SBRKT','BRKT', 'USCORE', 'ASTRSK', 'DOT', 'PLUS']

        self.def_white_space_chars = ["NEWLINE", 'CR', 'FF', 'TAB']

    """
    Read local markup files from configured directory path
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

        file_data_list = []
        label_value_list = []
        for file in files_list:

            # read file content and convert json string to dictionary
            file_data = tfr.read_file (file)

            # Marked up data that is read from the file may contain one or more markup blocks
            # Split them into a list of markup docs

            if "document_element" in access:
                separator_markup = access["document_element"]
                markup_docs = tc.split_multi_content_by_end_tag(file_data, separator_markup=separator_markup)
            else:
                markup_docs = [file_data]

            data_element = access["data_element"]

            # If a label is provided globally, read it from config.
            # Label will be the class/prediction used for training purposes.
            global_label_value = None
            if "label_value_override" in access:
                global_label_value = access["label_value_override"]

            self.logger.info("Found {} markup documents ".format(len(markup_docs)))

            # Iterate through each markup document
            for markupdoc in markup_docs:

                tagtext = tc.get_text_within_tags(markupdoc, container_tag=data_element)

                if isinstance(tagtext, list):
                    text_data = " ".join(tagtext)
                else:
                    text_data = tagtext

                clean_data = self.cleanup_data(text_data)

                if clean_data is not None and len(clean_data.strip()) > 0:
                    file_data_list.append(clean_data)

                    # if a label is provided globally, append it to labels list for each document
                    if global_label_value is not None:
                        label_value_list.append(global_label_value)

        return file_data_list, label_value_list

    """
    Read markup files from an S3 path
    """
    def read_s3_files (self, config):
        self.logger.error ("S3 file reader: Not yet implemented")
        return [], []

    """
    Read web pages from a list of URLs provided in a text file
    """
    def read_url_list(self):
        tfr = TextFileReader ()
        tc = TextCleaner ()
        access = self.source_config["access"]

        file_data_list = []
        label_value_list = []

        # Read the list of URLs from the local text file defined by the config JSON.
        # Each line in the text file is assumed to be a valid URL
        urls_list_file = access["url_list_file"]
        urls_list = tfr.read_file_by_line(urls_list_file)

        for url in urls_list:
            http_data = tfr.read_web_page(url)

            if http_data is None:
                self.logger.info(f"Reading URL: {url}: Error")
                continue

            read_status = f"{len(http_data)} chars"
            self.logger.info(f"Reading URL: {url}: {read_status}")

            # Marked up data that is read from the file may contain one or more markup blocks
            # Split them into a list of markup docs

            if "document_element" in access:
                separator_markup = access["document_element"]
                markup_docs = tc.split_multi_content_by_end_tag(http_data, separator_markup=separator_markup)
            else:
                markup_docs = [http_data]

            data_element = access["data_element"]

            # If a label is provided globally, read it from config.
            # Label will be the class/prediction used for training purposes.
            global_label_value = None
            if "label_value_override" in access:
                global_label_value = access["label_value_override"]

            self.logger.info("Found {} markup documents ".format(len(markup_docs)))

            # Iterate through each markup document
            for markupdoc in markup_docs:

                tagtext = tc.get_text_within_tags(markupdoc, container_tag=data_element)

                if isinstance(tagtext, list):
                    text_data = " ".join(tagtext)
                else:
                    text_data = tagtext

                clean_data = self.cleanup_data(text_data)

                if clean_data is not None and len(clean_data.strip()) > 0:
                    file_data_list.append(clean_data)

                    # if a label is provided globally, append it to labels list for each document
                    if global_label_value is not None:
                        label_value_list.append(global_label_value)

        return file_data_list, label_value_list

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
    def read_markup_data (self):

        access = self.source_config["access"]

        # Read data from markup files
        if (access["endpoint"] == "file") and (access["filesystem"] == "local"):
            self.logger.info ("Reading local markup files from {}".format(access["path"]))
            data_list, label_list = self.read_local_files ()

        if (access["endpoint"] == "file") and (access["filesystem"] == "s3"):
            self.logger.info("Reading s3 markup files from {}".format(access["path"]))
            data_list, label_list = self.read_s3_files ()

        # List of URLs to be scraped, placed in a text file
        if access["endpoint"] == "http":
            self.logger.info("Reading web pages for URLs in {}".format(access["url_list_file"]))
            data_list, label_list = self.read_url_list ()

        return data_list, label_list

