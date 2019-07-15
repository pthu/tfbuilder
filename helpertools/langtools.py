# Languages.py contains any important information that
# is important to process a language string,
# both for TEI XML and CSV.
# Any information that is specific for the TEI XML 
# conversion, can be found in config.py

from tfbuilder import tf_config
from tfbuilder.data import attrib_errors
from tfbuilder.helpertools import tokenizer

from unicodedata import normalize

class Generic:
    config = tf_config.generic
    udnorm = config['udnorm']
#     udnorm = tf_config.generic['udnorm']
    
    @classmethod
    def tokenize(cls, string):
    """Basic tokenization on spaces.
    
    This basic tokenization method splits a STRING 
    on SPACES, without returning empty strings.
    Any white space before and after is stripped off.
    It outputs string parts in a normalized way,
    according to the norm given in tf_config.py.
    
    returns ['normalized_string', 'normalized_string', ...]
    """
    return list(filter(None, 
      normalize(cls.udnorm, string.strip().split(' '))))
    
    @classmethod
    def stripTokenize(cls, string):
        """Advanced tokenization on non-letter characters.
        
        This advanced tokenization method splits a STRING 
        on NON-LETTER characters (as defined by the unicode
        data category definitions), without returning empty 
        strings. Before the splitting process, strings are
        converted to the NFC norm (combining accents with
        letters), to prevent splitting on accents.
        
        Any white space before and after is stripped off.
        It outputs string parts in a normalized way,
        according to the norm given in tf_config.py.
        
        NB: non-letter characters get lost during tokenization!

        returns ['normalized_string', 'normalized_string', ...]
        """
        tokens = tokenizer.tokenize(string)
        return tuple(normalize(norm=cls.udnorm, word) for word in tokens)
    
    @classmethod
    def origWord(cls, word):
        """returns the original word according to the
        preferred unicode normalization as defined
        in tf_config.py
        
        returns 'normalized_string'
        """
        return normalize(cls.udnorm, word)
    
    @classmethod
    def mainWord(cls, word):
        """returns the original word,
        but stripped of punctuation
        before, inbetween and after with
        normalized accentuation
        """
        
    
    @classmethod
    def plainWord(self, word):
        return stripAccents

    
    
class Greek(Generic):
    config = tf_config.greek
    
    @staticmethod
    def tokenize(self, string):
    
    @staticmethod
    def normalize(self):
        
    
    @staticmethod
    def jt_normalize(self, word):
        
    @staticmethod
    def lemmatize(self, word):
    

  
    
class Latin(Generic):
    config = tf_config.latin
    
    @staticmethod
    def tokenize(self, string):
    
    @staticmethod
    def normalize(self):
        
    @staticmethod
    def lemmatize(self, word):
    

  
