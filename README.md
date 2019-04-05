# Text Data Preparation
## The Problem
Any text analysis/machine learning project requires lots of text data. Source of the data could be in various file formats:
CSV, Html or custom markup, plain text files, Json etc.

Once the data is read, they will require cleansing - remove special characters, separate lines, separate documents from within the same input file etc.

## The Solution
This project aims to provide a framework to read, cleanse and deliver data for analytics and ML tasks. It can already read from CSV, JSON, markups and plain text files.
Most cleaning tasks are also available. 
All these tasks can be configured using a JSON file. So instead of writing code, one can define a pipeline and the framework will do all specified activities.

No rocket science. Everyone does this in their projects to get data in shape. All I did was to put them together, in a re-usable form. 

The dummymodel.py in the project root demonstrates how to read text data through configured pipeline. 
feedconfig.json contains sample pipline definitions for multiple source formats.

module structure:
   |
   +-datakettle
     |
     +-cleantext

datakettle: Contains packages for reading text data from various file types - viz. JSON, markups(html, etc.), plain text files, csv
            serve_data.DataServer class serves the data to our requirements

            HOW TO USE:

            from datakettle.cleantext.filereader import TextFileReader
            from datakettle.serve_data import DataServer

            # Read feedconfig.json

            fr = TextFileReader()
            configdata = json.loads(fr.read_file(full_path))
            ...
            ...

            # Fetch text data and labels from individual channels. Specify ALL to fetch from all enabled channels
            ds = DataServer (configdata)
            data_list, label_list = ds.fetch_data(channel='negative_news')
            ...
            ...

            It provides text documents as a list in data_list. label_list contains sentiment labels for each document in the data_list.
            Labels can be read from input files or can be configured globally.

feedconfig.json: This is a configuration file in JSON format. We can configure various channels. Each channel can be configured to
            read from one among csv, plain text, JSON or markup files. "disable" flag when set to True, the channel will not be read

            The "access" section:
            =====================
            The access section for each channel defines from where the data will be read. As of now, the code can read only from local files.
            The path can be specified and a file filter tells the module to read all files having that extension.

            "reader" values can be:
              - json_file_reader - for JSON files
              - markup_file_reader - for markups like html
              - text_file_reader - for plain text files
              - csv_file_reader  - for csv files

            "datatype" tells whether the channel is for training or testing data

            "data_element" for JSON, and markups tells which element within the document contains the text data to be read

            "document_element" for markup tells the element that separates documents within the file. A file can have multiple documents, wrapped in "document element"
                               A JSON file can be a single object or an array of objects. Hence no separate document separator needs to be specified.

            "document_separator"  for text files does the same function as "document_element". It separates documents within a text file. This can be NEWLINE as well.
                                If specified as NEWLINE, every linebreak will be treated as a separate document.

            "label_element" element that contains the sentiment label, if available within the file. (Optional)
            "label_value_override" If a sentiment label has to be assigned globally to every document read from a channel, we can set the value here. Otherwise leave it as ""
                                   This is useful when positive documents are placed in one directory and negative ones in another.

            Specific for CSV:
            "delimiter": column separator - default is ","
            "header_row": row number where column headers are present (if present). otherwise leave it as ""
            "data_column": column index (integer) or column name (if header available) where text data can be found
            "label_column": column index (integer) or  column name (if header available) where sentiment class label is present (optional)

            clean section
            =============
            This is an array specifying what kind of text cleaning has to be performed on each document that is read.
            Available functions :
            - remove_all_markup - All markup tags will be removed. E.g: <p></p>
            - remove_html_encoded_chars - Removes all encoded characters like &nbsp;  &#32; etc.
            - remove_special_chars - Removes special characters as specified in the special_chars array. This takes in pnemonic codes for each special character. We can selectively remove each.
            - remove_white_spaces - Removes white space characters. Specify white space characters as white_space_chars array. Again, pick and choose pnemonic codes for each
