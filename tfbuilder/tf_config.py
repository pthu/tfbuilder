from collections import OrderedDict
from helpertools import langtools
from data import attrib_errors
# from .tfbuilder.helpertools import langtools
# from .tfbuilder.data import attrib_errors

class Custom(langtools.Generic):
    def __init__(self, lang='custom'):
        self.lang = lang
    
    @staticmethod
    def tokenize(text):
        return text
        
    # NB for every defined text_format,
    # you need to enter a separate method
    # corresponding to the name of the 
    # value in lang['text_formats'][key]
    @staticmethod
    def normalize(word):
        return word
        
    @staticmethod
    def lemmatize(word):
        return word

generic_metadata = {
    'convertor execution': 'Ernst Boogert', # Please replace this by your own name!
    'convertor_author': 'Ernst Boogert',
    'convertor_date': 'February, 2020',
    'convertor_institution': 'Protestant Theological University (PThU), Amsterdam/Groningen, The Netherlands',
    'convertor_version': '1.0.0',
}
    

langsettings = {
    'generic': {
        #OUTPUT DIR STRUCTURE
        #Output dir struct; NB these variable names need to be defined in the metadata!
        #Multiple items in the list define multiple options that will be checked from left to right
        #Output author/title/editor (or one of the other options if they are not provided
        'dir_struct': [['author', 'editor'], 
                       ['title', 'book', 'work'], 
                       ['editor']],
        
        #TF variables!
        'slot_type': 'word',
        'intFeatures': set(),
        'nonIntFeatures': {'otype', 'oslots',},
        'struct_counter': dict(_sentence=1, _phrase=1),
        'generic': {}, # = Metadata used by TF
        
        #LANGUAGE VARIABLES
        #Unicode norm
        'udnorm': 'NFD',
        #Package of langtools
        'langtool': langtools.Generic,
        'replace_func': langtools.Generic.replace,
        #Tokenizer
        'tokenizer': langtools.Generic.splitTokenize,
        'tokenizer_args': {'punc': True, 
                           'clean': False,
                           'splitters': None,
                           'non_splitters': ('-', '<'),},
        'token_out': OrderedDict([('pre', {'text': False, 'metadata': 'interpunction before word'}),
                                 ('orig', {'text': True, 'metadata': 'the original format of the word without interpunction'}),
                                 ('post', {'text': False, 'metadata': 'interpunction after word'}),
                                 ]),
        #Lemmatizer
        'lemmatizer': None,
        #Text formats
        'text_formats': {'fmt:text-orig-orig': {'format': '{pre}{orig}{post} ',
                                  'function': langtools.Generic.origWord,
                                  'metadata': 'original format of the word including punctuation'},
                         'fmt:text-orig-main': {'format': '{main} ',
                                  'function': langtools.Generic.mainWord,
                                  'metadata': 'normalized format of the word excluding punctuation'},
                         'fmt:text-orig-plain': {'format': '{plain} ',
                                   'function': langtools.Generic.plainWord,
                                   'metadata': 'plain format in lowercase'},
                        },

        #XML VARIABLES
        #Define the fields from xml metadata that need to be preserved
        # concat = True means that subfields are concatenated
        # concat = False means that subfields get their own metadata entry
        'xmlmetadata': {'titleStmt': {'concat': False, 'delimit': ', ', 'end': ''},
                     'publicationStmt': {'concat': True, 'delimit': ', ', 'end': '.'},
                     'sourceDesc': {'concat': True, 'delimit': ', ', 'end': '.'},
                     'license': {'concat': True, 'delimit': ', ', 'end': '.'},
                     'availability': {'concat': True, 'delimit': ', ', 'end': '.'},
                    },
        
        #Define the tag in which sectioning can be found
        'section_tags': {'div',},
        #Define in which key the section name can be found
        'section_keys': {'subtype'},
        #Define attribute keys that are superfluous and need to be ignored
        'ignore_attrib_keys': set(),
        #Define attribute keys that do not contain a section name
        'non_section_keys': set(),
        #Define values that are no sections, although they are in the right key
        'non_section_values': set(),
        ##Define attribute values that are superfluous and need to be ignored
        ##'ignore_attrib_values': set(),
        #Define tags that contain text elements that need not to be processed as regular text 
        #but as features
        'non_text_tags': set(),
        #Define attributes that have values that are feature names (values will be calculated automatically)
        'feature_attribs': {'corresp', 'source'},
        #Define sentence delimiters to be counted by struct_counter
        'sentence_delimit': {'.', '?', '!',},
        #Define phrase delimiters to be counted by struct_counter
        'phrase_delimit': {',', ';', ':',},
    },
    
    'greek': {**langsettings['generic'], #Inherit all key-value pairs of 'generic'
        # Replacement and additional settings compared to 'generic'
        'langtool': langtools.Greek,
        'replace_func': langtools.Greek.replace,
        'lemmatizer': langtools.Greek.startLemmatizer,
        'text_formats': {'fmt:text-orig-full': {'name': 'orig',
                                                'format': '{pre}{orig}{post}',
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
                         'fmt:text-orig-beta_plain': {'name': 'beta_plain',
                                                'format': '{beta_plain} ',
                                                'function': langtools.Greek.betaPlainWord,
                                                'metadata': 'plain format in lowercase betacode (=Greek in Roman characters)'},
                         'fmt:text-orig-lemma': {'name': 'lemma',
                                                'format': '{lemma} ',
                                                'function': langtools.Greek.lemmaWord,
                                                'metadata': 'possible lemmata of the original words'},
                        },
        #XML settings
        'section_tags': {'div', 'milestone', 'state',},
        'section_keys': {'subtype',},
        'ignore_attrib_keys': {'corresp', 'merge', 'resp', 'id', 'xml:id', 'source'},
              
        'non_section_keys': {'altpage', 'altpage1', 'altnumbering', 'altref', 'mspage', 'xml:lang', 'corresp', 'xml:id', 'ed', 'id', 'source',},
              
        'non_section_values': {'altpage', 'altpage1', 'altnumbering', 'altref', 'mspage', 'xml:lang', 'edition', 'mignepage', 'stephnumbering', 'vignumbering', 'altnumbering', 'ms', 'textpart', 'altedition', 'page', 'line', 'Line', 'bekker page', 'tlnum', 'stephpage', 'olpage', 'altchapter', 'pat2', 'oleariuspage', 'pagew', 'pagep', 'MSS', 'NarrProof', 'blancard', 'hudson', 'borheck', 'lnum', 'reiskpage', 'bekker line', 'altsection', 'section2', 'casaubonpage', 'Whiston chapter', 'Whiston section', 'cam2page', 'orgpage', 'Para', 'Jebb page', 'ed1page', 'ed2page', 'ms1folio', 'lineno', 'altline', 'altpagecont', 'alt',},
              
        'non_text_tags': {'head': {'behaviour': 'next'},
                          'note': {'behaviour': 'previous'},
                          'title': {'behaviour': 'next'},
                          'bibl': {'behaviour': ''},
                          'del': {'behaviour': 'previous'},
                          'foreign': {'behaviour': ''},
                         },
        'feature_attribs': {'corresp', 'source'},
        'sentence_delimit': {'.', ';',},
        'phrase_delimit': {',', '·', '·', ':',},
    },
    
    
    
    'latin': {**langsettings['generic'],
        'langtool': langtools.Latin,
    },
    
    
    
    'custom': {**langsettings['generic'],
        'dir_struct': [[],],
        
        #TF variables!
        'slot_type': '',
        'intFeatures': set(),
        'nonIntFeatures': {'otype', 'oslots',},
        'struct_counter': dict(),
        'generic': {},
        
        #LANGUAGE VARIABLES
        #Unicode norm
        'udnorm': '',
        #Package of langtools
        'langtool': Custom,
        'replace_func': Custom.replace,
        #Tokenizer
        'tokenizer': Custom.tokenize,
        'tokenizer_args': {},
        'token_out': OrderedDict([]),
        
        #Lemmatizer
        'lemmatizer': Custom.lemmatize,
        #Text formats
        'text_formats': {'fmt:text-orig-orig': {'format': '{orig}',
                                  'function': Custom.origWord,
                                  'metadata': 'original word'},
                        },

        #XML VARIABLES
        #Define the fields from xml metadata that need to be preserved
        # concat = True means that subfields are concatenated
        # concat = False means that subfields get their own metadata entry
        'xmlmetadata': {},
        
        #Define the tag in which sectioning can be found
        'section_tags': set(),
        #Define in which key the section name can be found
        'section_keys': set(),
        #Define attribute keys that are superfluous and need to be ignored
        'ignore_attrib_keys': set(),
        #Define attribute keys that do not contain a section name
        'non_section_keys': set(),
        #Define values that are no sections, although they are in the right key
        'non_section_values': set(),
        ##Define attribute values that are superfluous and need to be ignored
        ##'ignore_attrib_values': set(),
        #Define tags that contain text elements that need not to be processed as regular text 
        #but as features
        'non_text_tags': set(),
        #Define attributes that have values that are feature names (values will be calculated automatically)
        'feature_attribs': set(),
        #Define sentence delimiters to be counted by struct_counter
        'sentence_delimit': set(),
        #Define phrase delimiters to be counted by struct_counter
        'phrase_delimit': set(),
    },
}

