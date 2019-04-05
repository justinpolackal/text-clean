import logging
from bs4 import BeautifulSoup
import re
import json
import os
import nltk
from nltk.tokenize import word_tokenize

"""
Class intended to be used to clean up text data. 
Data can be in plain text or markup format (HTML etc.)
"""

class TextCleaner (object):
    def __init__(self, input_type="file", content_type="markup"):
        self.input_type = input_type
        self.content_type = content_type
        self.logger = logging.getLogger(__name__)

    """
    Read a text file in read mode as a single document and return 
    """
    def read_file (self, file_path):
        fh = None
        file_data = None

        try:
            fh = open(file_path, mode='r')

            file_data = fh.read()

            self.logger.info("Read: {} chars from {}.".format(len(file_data), file_path))

        except IOError as ioerror:
            self.logger.error ("Error Occurred while reading: ", exc_info=True)

        finally:
            if (fh):
                fh.close()

        return file_data

    """
    Read stopwords for a given language from the stopwords file. 
    The file is assumed to be named as "stopwords_[languagecode].txt, where language code should be the two character iso code.
    E.g: "stopwords_en.txt" for English
     
    Returns a list of stopwords
    """
    def read_stopwords_file(self, lang="en"):
        file_name = "stopwords_{}.txt".format(lang)
        fh = None
        stopwords = []

        file_path = os.path.dirname(os.path.realpath(__file__))
        file_name = os.path.join(file_path, file_name)

        self.logger.info ("Reading stopwords list for [{}] from {}".format(lang, file_name))

        try:
            fh = open(file_name, mode='r')

            # Each line is a stop word in the file. Reads them into a list
            lines = fh.readlines()

            # Remove trailing newline, carriage return from each word
            for word in lines:
                sword = self.remove_white_spaces(white_space_chars=['NEWLINE', 'CR', 'FF', 'TAB'], replace_char='', doc=word)
                stopwords.append(sword)

        except IOError as ioerror:
            self.logger.error ("Error Occurred while reading: {}".format(file_name), exc_info=True)

        finally:
            if fh:
                fh.close()
        return stopwords

    """
    If the file data contains multiple documents (markup content), separated
    by @separator_markup, then split the whole file data into a list of separate
    documents. 
    For example, in one case, a file contains multiple documents enclosed within <REUTERS>..</REUTERS> tag
    Function splits them into a list of separate documents. Tags are included. 
    """
    def split_multi_content_by_end_tag (self, data_str, separator_markup="html"):
        """
        :param data_str: String data (whole document)
        :param separator_markup: markup tag that separates documents within the file
        :return: List of documents
        """
        doc_list = []
        if (data_str is None or len(data_str) < 1):
            return doc_list

        start_tag = "<{}>".format(separator_markup.lower())
        end_tag   = "</{}>".format(separator_markup.lower())

        self.logger.info ("Start-End tags: {} {}".format(start_tag, end_tag))

        split_list = data_str.lower().split(end_tag)

        for doc in split_list:
            doc_list.append("{} {}".format(doc, end_tag))

        return doc_list

    """
    If the text file data contains multiple documents, separated
    by @separator_code, then split the whole file data into a list of separate
    documents. 
    separator_code value = "NEWLINE" will be treated as newline. Each line will be split into a separate document
    Any other value will be treated as a delimiter as it is and documents will be split accordingly. 
    """
    def split_multi_text_by_separator (self, data_str, separator_code=""):
        """
        :param data_str: String data (whole document)
        :param separator_code: document delimiter - character sequence that separates documents within the file
        :return: List of documents
        """
        doc_list = []
        if data_str is None or len(data_str) < 1:
            return doc_list

        if separator_code == "":
            doc_list.append (data_str.lower())
        else:
            if separator_code.lower() == 'newline':
                separator_code ='\n'

            doc_list = data_str.lower().split(separator_code.lower())
        return doc_list

    """
    Get content enclosed in a specific tag, within a document having markups
    For example, retrieve only the content enclosed inside <body></body> tag 
    """
    def get_text_within_tags(self, doc, container_tag="body"):
        """
        :param doc: Document String
        :param container_tag: The markup tag within which the text of interest is packed. E.g: Text between <body> and </body>
        :return: List of strings
        """
        start_tag = "<{}>".format(container_tag.lower())
        end_tag   = "</{}>".format(container_tag.lower())

        if (doc is None):
            return None

        tag_doc = None

        regex_pattern = r"{0}(.*?){1}".format(start_tag, end_tag)
        tag_doc = re.findall(regex_pattern, doc, re.MULTILINE|re.DOTALL)

        return tag_doc

    """
    Remove all markup tags from a document.Any tag having <>, </> will be removed
    CAUTION: Use @valid_markup=True only when the document is a proper markup document
    """
    def remove_all_markup(self, doc, valid_markup=False):
        """
        :param doc: Document string
        :param valid_markup: When True, function assumes that the document contains a valid html/xml markup document. If not sure, choose False
        :return: String with all tags (<> and </>) removed
        """
        if (doc is None):
            return None

        if (valid_markup):
            # Use beautifulsoup to replace all tags with spaces
            cleantext = ""
            soup = BeautifulSoup(doc, "lxml")
            cleantext = soup.get_text(separator=' ')
        else:
            # Use regular expression to get rid of any tags
            #pattern = re.compile(r'<.*?>')
            cleantext = re.sub('<[^<]+?>', '', doc)

        return cleantext

    """
    Removes specified white space characters from a given text document (@doc)
    @white_space_chars is a list that can contain one or more of:
        - SPACE
        - NEWLINE
        - CR
        - FF
        - TAB
    """
    def remove_white_spaces(self, doc, white_space_chars, replace_char=' '):
        """
        :param white_space_chars: A list of white space characters. Specify human readable codes for characters as mentioned above.
        :param doc: Document string
        :return: cleaned document string
        """
        if doc is None:
            return None

        for wchar in white_space_chars:
            if (wchar == 'NEWLINE'):
                remove = '\n'
            elif (wchar == 'CR'):
                remove = '\r'
            elif (wchar == 'FF'):
                remove = '\f'
            elif (wchar == 'TAB'):
                remove = '\t'

            doc = doc.replace (remove, replace_char)

            if (wchar == 'SPACE'):
                doc = " ".join(doc.split())

        return doc

    """
    Removes HTML encoded characters such as &nbsp;, &lt; etc. as well as 
    their ASCII number equivalents e.g: &#32, &#33 etc. 
    """
    def remove_html_encoded_chars (self, doc, replace_char=' '):
        """
        :param doc: Document string
        :param replace_char: The character to be used to replace a matching encoded character. Default is white space
        """
        pat_html_name = r"[&]\w+[;]"
        pat_html_num  = r"[&][#]\w+[;]"

        if (doc is None):
            return None

        clean_doc = re.sub(pat_html_name, replace_char, doc, flags=re.MULTILINE)

        clean_doc = re.sub(pat_html_num, replace_char, clean_doc, flags=re.MULTILINE)

        return clean_doc

    """
    Split a given text document by newline. 
    if @trim_spaces is True, consecutive whitespaces (/r, /t, /f...) are removed
    if @ remove_empty_lines is True, a cleaned sentence is added to the document only if it is non empty 
    """
    def split_by_newline (self, doc, trim_spaces=True, remove_empty_lines=True):
        if doc is None:
            return None

        raw_sentences = doc.split("\n")

        if (trim_spaces):
            sentences = []

            for sentence in raw_sentences:
                clean_sentence = " ".join(sentence.split())

                if (remove_empty_lines):

                    if (len(clean_sentence) > 0):
                        sentences.append(clean_sentence)
                else:
                    sentences.append(clean_sentence)

        return sentences

    """
    Split a document into sentences using specific character sequences @char_sequence
    if @trim_spaces is True, consecutive whitespaces (/r, /t, /f...) are removed
    if @ remove_empty_lines is True, a cleaned sentence is added to the document only if it is non empty
    """
    def split_by_char_sequence (self, doc, char_sequence=". ", trim_spaces=True, remove_empty_lines=True):
        if doc is None:
            return None

        raw_sentences = doc.split(char_sequence)

        if (not trim_spaces):
            sentences = raw_sentences
        else:
            sentences = []

            for sentence in raw_sentences:
                clean_sentence = " ".join(sentence.split())

                if (remove_empty_lines):

                    if (len(clean_sentence) > 0):
                        sentences.append(clean_sentence)
                else:
                    sentences.append(clean_sentence)

        return sentences

    """
    Splits a document into sentences using nltk.punkt module. Available only for English
    nltk Punkt Sentence Tokenizer divides a text into a list of sentences by using an unsupervised algorithm.
    The NLTK data package includes a pre-trained Punkt tokenizer for English, which is being used here.
    """
    def split_by_punkt (self, doc, trim_spaces=True, remove_empty_lines=True):
        sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

        raw_sentences = sent_detector.tokenize(doc.strip())

        if (not trim_spaces):
            sentences = raw_sentences
        else:
            sentences = []

            for sentence in raw_sentences:
                clean_sentence = " ".join(sentence.split())

                if (remove_empty_lines):

                    if (len(clean_sentence) > 0):
                        sentences.append(clean_sentence)
                else:
                    sentences.append(clean_sentence)
        return sentences

    """
    Takes in a json string and converts it to a python object.
    If the input json is an array, the returned object will be a list of dictionaries.
    Otherwise, the return object will be a dictionary.
    NOTE: The input string must be a valid json 
    """
    def string_to_json_object (self, json_str):
        """
        :param json_str: JSON String
        """
        json_obj = None

        if (json_str is None or len(json_str) < 1):
            return None

        try:

            json_obj = json.loads(json_str)

        except Exception as e:
            self.logger.error("Failed to convert string to JSON object", exc_info=True)

        return json_obj

    """
    Removes special characters specified in :special_chars list
    """
    def remove_special_chars (self, special_chars, doc, replace_char=' '):
        """
        :param special_chars: List of special characters, denoted by pnemonic codes. E.g: COMMA, DQUOTE, SQUOTE, FSLASH, BSLASH, HASH, etc.
        :param replace_char: character to be replaced with. Default is white space
        :param doc: String or text document to clean
        """
        # Pnemonic map
        #-------------
        # COMMA : ,
        # DQUOTE: "
        # SQUOTE: '
        # FSLASH: /
        # BSLASH: \
        # HASH  : #
        # AT    : @
        # EXCL  : !
        # CARAT : ^
        # AMP   : &
        # PCT   : %
        # DOLLAR: $
        # TILDA : ~
        # APOS  : `
        # COLN  : :
        # SCOLN : ;
        # QMARK : ?
        # LT    : <
        # GT    : >
        # EQ    : =
        # PIPE  : |
        # CBRACE: {, }
        # SBRKT : [,]
        # BRKT  : (,)
        # USCORE: _
        # ASTRSK: *
        # DOT   : .
        # MINUS : -
        # PLUS  : +

        pnemonics = {
            "COMMA" : ",",
            "DQUOTE": '\"',
            "SQUOTE": "\'",
            "FSLASH": "/",
            "BSLASH": "\\\\",
            "HASH"  : "#",
            "AT"    : "@",
            "EXCL"  : "!",
            "CARAT" : "^",
            "AMP"   : "&",
            "PCT"   : "%",
            "DOLLAR": "$",
            "TILDA" : "~",
            "APOS"  : "`",
            "COLN"  : ":",
            "SCOLN" : ";",
            "QMARK" : "?",
            "LT"    : "<",
            "GT"    : ">",
            "EQ"    : "=",
            "PIPE"  : "|",
            "CBRACE": "{}",
            "SBRKT" : "\[\]",
            "BRKT"  : "()",
            "USCORE": "_",
            "ASTRSK": "*",
            "DOT"   : ".",
            "MINUS" : "-",
            "PLUS"  : "+"
        }

        pattern = ""
        for spec_char in special_chars:
            pattern = "{}{}".format(pattern, pnemonics[spec_char])

        pattern = "[{}]".format(pattern)
        #print (pattern)

        clean_doc = re.sub(pattern, replace_char, doc, flags=re.MULTILINE)
        return clean_doc

    """
    Convert a given sentence or document into word tokens. 
    Uses nltk word_tokenize()
    
    Returns empty list if the doc is empty
    """
    def get_word_tokens (self, doc, language='english'):
        """
        :param doc: Source document to be tokenized
        :param language: Language input for nltk. Default is 'english'
        :return: List of word tokens. Empty list when the document is empty
        """
        if doc is None or len(doc) < 1:
            return []

        return nltk.word_tokenize(doc, language=language)

    """
    Given a list of word tokens, remove all stopwords. 
    If a list of stopwords is supplied, the list will be used. Otherwise, list of stopwords will be read from stopwords_<ll>.txt
    
    Returns a list of filtered word tokens. None if the supplied word_tokens is None.
    """
    def remove_stopwords (self, word_tokens, stopwords=None, lang="en" ):
        """
        :param word_tokens: List of words (word tokens)
        :param stopwords: List of stopwords (optional)
        :param lang: (language code. E.g: en, optional)
        :return: List of filtered word tokens. Otherwise None
        """
        if stopwords is None or len(stopwords) < 1:
            stopwords = self.read_stopwords_file(lang=lang)

        if word_tokens is None:
            return None

        filtered_tokens = [w for w in word_tokens if w not in stopwords]

        return filtered_tokens

