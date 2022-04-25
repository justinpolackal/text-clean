import os
from datakettle.cleantext.textcleaner import TextCleaner
from datakettle.cleantext.filereader import TextFileReader
import datakettle.cleantext.utils as utils
import logging
from bs4 import BeautifulSoup

class HTMLReader(object):

    def __init__(self, source_config):
        self.source_config = source_config
        self.logger = logging.getLogger(__name__)

        self.def_special_chars = ['MINUS', 'COMMA', 'DQUOTE', 'SQUOTE', 'FSLASH', 'BSLASH', 'HASH', 'AT', 'EXCL',
                                  'CARAT',
                                  'AMP', 'PCT', 'DOLLAR', 'TILDA', 'APOS', 'COLN', 'SCOLN', 'QMARK', 'LT', 'GT', 'EQ',
                                  'PIPE', 'CBRACE',
                                  'SBRKT', 'BRKT', 'USCORE', 'ASTRSK', 'DOT', 'PLUS']

        self.def_white_space_chars = ["NEWLINE", 'CR', 'FF', 'TAB']


    """
    Read web pages from a list of URLs provided in a text file
    """
    def read_url_list(self):
        tfr = TextFileReader()
        tc = TextCleaner()
        access = self.source_config["access"]
        url_data_list = []

        # Read the list of URLs from the local text file defined by the config JSON.
        # Each line in the text file is assumed to be a valid URL
        urls_list_file = access["url_list_file"]
        urls_list = tfr.read_file_by_line(urls_list_file)

        for url in urls_list:
            # Fetch html content
            html_data = tfr.read_web_page(url.strip())

            if html_data is None:
                self.logger.info(f"Reading URL: {url}: Error")
                url_data_list.append({"url": url.strip(), "title": None, "content": None})
                continue

            self.logger.info(f"Reading URL: {url}: {len(html_data)} chars")

            soup = BeautifulSoup(html_data, 'html.parser')
            html_title = soup.head.title.get_text()
            tag_data = html_data  # By default, use the entire html string as the target data

            # Filter for a given tag with specific attributes, if specified in the config JSON
            content_within_tag = access.get("get_content_within_tag")
            if content_within_tag:
                tag_data = self.get_html_content_within_tag(soup, content_within_tag)
            #
            # TBD: Run other extraction methods, as defined in the config file
            #

            clean_data = self.cleanup_data(tag_data) if tag_data else None
            clean_title = self.cleanup_data(html_title) if html_title else None
            url_data_list.append({"url": url.strip(), "title": clean_title, "content": clean_data})

        return url_data_list

    def get_html_content_within_tag(self, soup, tag_def):
        find_tag = tag_def.get("tag")
        attribs = tag_def.get("attribs")
        find_what = tag_def.get("find")

        tag_snippets = soup.find_all(find_tag, attrs=attribs)
        print(f"Number of snipets: {len(tag_snippets)}")

        # If the filter didn't yield anything, skip this html altogether.
        if not tag_snippets:
            return None

        if find_what == "all" and tag_snippets:
            tag_data = ' '.join([snippet.get_text() for snippet in tag_snippets])
        if find_what == "first":
            tag_data = tag_snippets[0].get_text()
        if find_what == "last":
            tag_data = tag_snippets[-1].get_text()
        return tag_data

    """
    Cleanup file data list using the cleaning steps listed within the sources section of the feed config JSON
    """

    def cleanup_data(self, clean_data):
        if clean_data is None or len(clean_data) < 1:
            return ""

        tc = TextCleaner()
        clean_steps = self.source_config["clean"]

        # Iterate through each step and perform specified cleaning action
        for cstep in clean_steps:
            stepname = cstep["step"]

            if stepname == "remove_all_markup":
                clean_data = tc.remove_all_markup(doc=clean_data, valid_markup=False)

            if stepname == "remove_html_encoded_chars":
                clean_data = tc.remove_html_encoded_chars(clean_data, replace_char=' ')

            if stepname == "remove_special_chars":
                if "special_chars" in cstep:
                    special_chars = cstep["special_chars"]
                else:
                    special_chars = self.def_special_chars

                replace_char = cstep["replace_char"] if cstep.get("replace_char") else ''
                clean_data = tc.remove_special_chars(special_chars, clean_data, replace_char=replace_char)

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

    def read_html_data(self):
        access = self.source_config["access"]

        # Scrape from list of URLs, placed in a text file
        if access["endpoint"] == "http":
            self.logger.info("Reading web pages for URLs in {}".format(access["url_list_file"]))
            url_data_list = self.read_url_list()

        return url_data_list

