import os
import json
import logging
from datakettle.cleantext.filereader import TextFileReader
from datakettle.serve_data import DataServer

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

conf_file_path = "D:\\git_repos\\text-clean"
conf_file_name = "feedconfig.json"

full_path = os.path.join(conf_file_path, conf_file_name)

fr = TextFileReader()
configdata = json.loads(fr.read_file(full_path))

ds = DataServer (configdata)
data_list, label_list = ds.fetch_data(channel='negative_news')

# Split Train, Test Data sets

# Vectorize documents

# fit transform model

# test

# calculate f1 score


