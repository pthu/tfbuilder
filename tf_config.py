from tffabric import langtools
from tffabric.data import attrib_errors

generic = {
    'lang': 'generic',
    'slot_type': 'word',
    'udnorm': 'NFD',
    'dir_struct': ['author', 'book', 'editor'],
    'sentence_delimit': ['.', '?', '!'],
    'phrase_delimit': [',', ';', ':'],
    'langtool': langtools.Generic,
}

greek = {
    'lang': 'Greek',
    'slot_type': 'word',
    'text_formats': {'orig': langtools.Greek.,
                     'main': , 
                     'norm': ,
                     'plain': ,
                     'beta_plain': ,
                     'lemma': ,
                    },
    'udnorm': 'NFD',
    'dir_struct': ['author', 'book', 'editor'],
    'sentence_delimit': ['.', ';'],
    'phrase_delimit': [',', '', ':'],
    'langtool': langtools.Greek,
}

latin = {
    'lang': 'Latin',
    'slot_type': 'word',
    'udnorm': 'NFD',
    'dir_struct': ['author', 'book', 'editor'],
    'sentence_delimit': ['.', '?', '!'],
    'phrase_delimit': [',', ';', ':'],
    'langtool': langtools.Latin,
}

custom = {
    'lang': '',
    'slot_type': '',
    'udnorm': 'NFD',
    'dir_struct': [],
    'sentence_delimit': [],
    'phrase_delimit': [],
    'langtool': Custom,
}

class Custom(langtools.Generic):
    def __init__(self, lang='custom'):
        self.lang = lang
    
    @staticmethod
    def tokenize(string):
        pass
        
    # NB for every defined text_format,
    # you need to enter a separate method
    # corresponding to the name of the 
    # value in lang['text_formats'][key]
    @staticmethod
    def normalize(word):
        pass
        
    @staticmethod
    def lemmatize(word):
        pass
