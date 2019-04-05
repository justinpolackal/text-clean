import os
import sys
import json
import logging
from .json_reader import JsonReader
from .markup_reader import MarkupReader
from .text_reader import TextReader
from .csv_reader import CSVReader

class DataServer (object):
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    """
    Iterate through the sources in the config JSON and fetch data from each channel, or, 
    as specified in the input
    """
    def fetch_data (self, channel='ALL'):
        sources = ""

        if ("sources" in self.config):
            sources = self.config["sources"]

        self.logger.info("Channel: {0}".format(channel))

        data_list = []
        label_list = []
        for source in sources:
            if (source["disabled"]):
                continue

            if (source["channel"] == channel ) or (channel == 'ALL'):
                access = source["access"]
                self.logger.info ("Fetching data from {0} Reader {1}".format(source["channel"], access["reader"]))

                if access["reader"] == "json_file_reader":
                    jsreader = JsonReader(source_config=source)
                    data, label = jsreader.read_json_data()
                    data_list.extend (data)
                    label_list.extend(label)
                    self.logger.info("Fetched data {} items ".format(len(data)))

                if access["reader"] == "markup_file_reader":
                    mkreader = MarkupReader(source_config=source)
                    data, label = mkreader.read_markup_data()
                    data_list.extend(data)
                    label_list.extend(label)
                    self.logger.info("Fetched data {} items ".format(len(data)))

                if access["reader"] == "text_file_reader":
                    txtreader = TextReader(source_config=source)
                    data, label = txtreader.read_text_data()
                    data_list.extend(data)
                    label_list.extend(label)
                    self.logger.info("Fetched data {} items ".format(len(data)))

                if access["reader"] == "csv_file_reader":
                    csvreader = CSVReader(source_config=source)
                    data, label = csvreader.read_csv_data()
                    data_list.extend(data)
                    label_list.extend(label)
                    self.logger.info("Fetched data {} items ".format(len(data)))

                if access["reader"] == "benzinga_reader":
                    self.logger.error("Not implemented yet")
                    pass


        return data_list, label_list