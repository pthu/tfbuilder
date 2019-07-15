# Languages.py contains any important information that
# is important to process a language string,
# both for TEI XML and CSV.
# Any information that is specific for the TEI XML 
# conversion, can be found in config.py

import tf_config
from data import attrib_errors
from helpertools import tokenizer

class Generic:
    config = tf_config.generic
    
    @staticmethod
    def tokenize(string):
    '''This basic tokenize method splits a string 
    on spaces, without returning any empty strings.
    '''
    return list(filter(None, string.strip().split(' ')))
    
    @classmethod
    def stripTokenize(cls, string):
        return tokenizer.tokenize(string, norm=cls.config['udnorm'])
    
    @staticmethod
    def origWord(word):
        '''returns the original word'''
        return word
    
    @staticmethod
    def mainWord(self, word):
        '''returns the original word,
        but stripped of punctuation
        before and after and with
        normalized accentuation'''
    
    @staticmethod
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
    

  
