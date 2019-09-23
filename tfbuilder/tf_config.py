from collections import OrderedDict
from helpertools import langtools
from data import attrib_errors
# from .tfbuilder.helpertools import langtools
# from .tfbuilder.data import attrib_errors

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


langsettings = {
    'generic': {
        'slot_type': 'word',
        'udnorm': 'NFD',
        'tokenizer': langtools.Generic.splitTokenize,
        'tokenizer_args': {'punc': True, 
                           'clean': False,
                           'splitter': None,
                           'non_splitter': ('-',),},
        'lemmatizer': None,
        'text_formats': {'orig': {'format': '{pre}{orig}{post} ',
                                  'function': langtools.Generic.origWord,
                                  'metadata': 'original format of the word including punctuation'},
                         'main': {'format': '{main} ',
                                  'function': langtools.Generic.mainWord,
                                  'metadata': 'normalized format of the word excluding punctuation'},
                         'plain': {'format': '{plain} ',
                                   'function': langtools.Generic.plainWord,
                                   'metadata': 'plain format in lowercase'},
                        },
        'dir_struct': [['author', 'editor'], ['title', 'book', 'work'], ['editor']],
        
        'metadata': {'titleStmt': {'concat': False},
                     'publicationStmt': {'concat': True, 'delimit': ', ', 'end': '.'},
                     'sourceDesc': {'concat': True, 'delimit': ', ', 'end': '.'},
                     'license': {'concat': True, 'delimit': ', ', 'end': '.'},
                     'availability': {'concat': True, 'delimit': ', ', 'end': '.'},
                    },
        'section_tags': {'div',},
        'ignore_attrib_keys': set(),
        'ignore_attrib_values': set(),
        'ignore_section_elems': set(),
        'non_text_elems': {'head', 'note', 'title', 'bibl', 'del'},
        'sentence_delimit': {'.', '?', '!',},
        'phrase_delimit': {',', ';', ':',},
        'langtool': langtools.Generic,
    },
    
    'greek': {
        'slot_type': 'word',
        'udnorm': 'NFD',
        'tokenizer': langtools.Greek.splitTokenize,
        'tokenizer_args': {'punc': True, 
                           'clean': False,
                           'splitters': None,
                           'non_splitters': ('-',),},
        'token_out': {'pre': {'desc': 'interpunction before word'},
                      'word': {'desc': 'the word without interpunction'},
                      'post': {'desc': 'interpunction after word'},
                     },
        'replace_func': langtools.Greek.replace,
        'lemmatizer': langtools.Greek.startLemmatizer,
        'text_formats': {'fmt:text-orig-full': {'name': 'orig',
                                                'format': '{pre}{orig}{post} ',
                                                'function': langtools.Greek.origWord,
                                                'metadata': 'original format of the word including punctuation'},
                         'fmt:text-orig-main': {'name': 'main',
                                                'format': '{main} ',
                                                'function': langtools.Greek.mainWord,
                                                'metadata': 'normalized format of the word excluding punctuation'},
                         'fmt:text-orig-norm': {'name': 'norm', 
                                                'format': '{norm} ',
                                                'function': langtools.Greek.normWord,
                                                'metadata': 'normalized format (James Tauber) of the word excluding punctuation'},
                         'fmt:text-orig-plain': {'name': 'plain',
                                                'format': '{plain} ',
                                                'function': langtools.Greek.plainWord,
                                                'metadata': 'plain format in lowercase'},
                         'fmt:text-orig-beta-plain': {'name': 'beta_plain',
                                                'format': '{beta_plain} ',
                                                'function': langtools.Greek.betaPlainWord,
                                                'metadata': 'plain format in lowercase betacode (=Greek in Roman characters)'},
                         'fmt:text-orig-lemma': {'name': 'lemma',
                                                'format': '{lemma} ',
                                                'function': langtools.Greek.lemmaWord,
                                                'metadata': 'possible lemmata of the original words'},
                        },
        
        'dir_struct': [['author', 'editor'], ['title', 'book', 'work'], ['editor']],
        
        'metadata': {'titleStmt': {'concat': False},
                     'publicationStmt': {'concat': True, 'delimit': ', ', 'end': '.'},
                     'sourceDesc': {'concat': True, 'delimit': ', ', 'end': '.'},
                     'license': {'concat': True, 'delimit': ', ', 'end': '.'},
                     'availability': {'concat': True, 'delimit': ', ', 'end': '.'},
                    },
        'section_tags': {'div', 'milestone'},
        'ignore_attrib_keys': {'corresp', 'merge', 'resp'},
        'non_section_keys': {'altpage', 'altpage1', 'altnumbering', 'altref', 'mspage', 'xml:lang', 'type', 'corresp',},
        'non_section_values': {'altpage', 'altpage1', 'altnumbering', 'altref', 'mspage', 'xml:lang', 'edition', 'mignepage', 'stephnumbering', 'vignumbering', 'altnumbering', 'ms', 'textpart', 'altedition',},
        'non_text_tags': {'head': {'behaviour': 'next slots'},
                          'note': {'behaviour': 'previous slots'},
                          'title': {'behaviour': 'next slots'},
                          'bibl': {'behaviour': ''},
                          'del': {'behaviour': ''},
                          'foreign': {'behaviour': ''},
                         },
        'feature_attribs': {'corresp',},
        'sentence_delimit': {'.', ';',},
        'phrase_delimit': {',', '·', '·', ':',},
        'langtool': langtools.Greek,
    },
    'latin': {
        'slot_type': 'word',
        'udnorm': 'NFD',
        'dir_struct': ['author', 'book', 'editor'],
        'sentence_delimit': ['.', '?', '!'],
        'phrase_delimit': [',', ';', ':'],
        'langtool': langtools.Latin,
    },
    'custom': {
        'slot_type': '',
        'udnorm': 'NFD',
        'dir_struct': [],
        'sentence_delimit': [],
        'phrase_delimit': [],
        'langtool': Custom,
    },
}

