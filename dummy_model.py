import os
import json
import logging
from datakettle.cleantext.filereader import TextFileReader
from datakettle.serve_data import DataServer
import pandas as pd

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

conf_file_path = "/Users/justinjose/Work/personal/text-clean"
conf_file_name = "feedconfig.json"

full_path = os.path.join(conf_file_path, conf_file_name)

fr = TextFileReader()
configdata = json.loads(fr.read_file(full_path))

ds = DataServer (configdata)
#data_list = ds.fetch_data(channel='financial1')
data_list = ds.fetch_data(channel='cnbc_news_delta1')
#data_list, label_list, title_list = ds.fetch_data(channel='positive_news')
#data_list = ds.fetch_data(channel='101articles')

url = []
title = []
content = []
for item in data_list:
    url.append(item.get("url"))
    title.append(item.get("title"))
    content.append(item.get("content"))
data_list_df = pd.DataFrame({"URL":url, "TITLE":title, "CONTENT":content})
#df = pd.DataFrame({"title":title_list, "content": data_list})
#df.to_csv("C:\\Users\\justin.jose\\projects\\glorifi\\textcleaner\\cnbc_data_delta1.csv", sep="|",header=True,index=True)
