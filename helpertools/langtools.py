# Languages.py contains several classes with methods that
# are important to process strings, both for TEI XML and CSV.
# Any information that is specific for the TEI XML 
# conversion, can be found in config.py

from tfbuilder import tf_config
from tfbuilder.data import attrib_errors
from tfbuilder.helpertools.unicodetricks import tokenizer, splitPunc, cleanWords, plainCaps, plainLow

from unicodedata import normalize

class Generic:
    config = tf_config.generic
    udnorm = config['udnorm']
#     udnorm = tf_config.generic['udnorm']

    @classmethod
    def ltNormalize(cls, string):
        """langtools normalize usually uses the unicodedata
        normalize() function; however, for many languages it
        will be overriden with a custom normalization function"""
        return normalize(cls.udnorm, string) 
    
    @classmethod
    def tokenize(cls, sentence, norm=udnorm, punc=False, clean=False):
    """This advanced tokenizer is based on the unicodedata
    categories. It is able to tokenize much more sophisticated
    than the python sentence.split() function.
    
    punc=False:
        All punctuation before and after a word is deleted.
    
    punc=True:
        All punctuation before and after a word is given
    
    clean=False:
        If punctuation stands in the middle of letters, 
        without surrounding spaces, the word is split 
        on punctuation.
    
    clean=True:
        If punctuation stands in the middle of a word,
        without spaces, the punctuation is deleted and the 
        two parts of the word are glued together.
    
    returns ['string', 'string', ...]
    """
    return tokenizer(sentence, norm=cls.udnorm, punc=False, clean=False):
    
    @classmethod
    def splitTokenize(cls, sentence):
        """Tokenizes a sentence, while preserving punctuation.
        
        The difference with tokenize() is that splitTokenize
        preserves splits punctuation from the word.
        
        returns: ((pre, word, post), (pre, word, post), ...)
        """
        splitPunc(sentence, norm=cls.udnorm, clean=True):
        
    
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
        return cleanWords(word, norm=udnorm, clean=True)
    
    @staticmethod
    def plainWord(word, caps=False):
        if caps:
            return plainCaps(word)
        else:
            return plainLow(word)

    
    
class Greek(Generic):
    config = tf_config.greek
    
    @staticmethod
    def jtNormalize(self, word):
        
        
    
    @staticmethod
    def startLemmatizer():
        lemmatizer_open = open(SRC_DIR + '/lemmatizer.pickle', 'rb')
        lemmatizer = pickle.load(lemmatizer_open)
        lemmatizer_open.close()
        return lemmatizer
    
    @classmethod #TODO!
    def lemmatize(word, norm=udnorm, lemmatizer):
        word = normalize('NFD', word.lower())
        if word in lemmatizer:
            word = ','.join(normalize(norm, lemmatizer[word]))
        else:
            word = f'*{word}'
        return word
    

  
    
class Latin(Generic):
    config = tf_config.latin
    
    @staticmethod
    def tokenize(self, string):
    
    @staticmethod
    def normalize(self):
        
    @staticmethod
    def lemmatize(self, word):
    

  
