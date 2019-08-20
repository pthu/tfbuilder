# Languages.py contains several classes with methods that
# are important to process strings, both for TEI XML and CSV.
# Any information that is specific for the TEI XML 
# conversion, can be found in config.py
from data import attrib_errors
from helpertools.unicodetricks import splitPunc, cleanWords, plainCaps, plainLow
from helpertools.data.greek_elisions import ELISIONS
from cltk.corpus.greek.beta_to_unicode import Replacer
import betacode.conv

from unicodedata import normalize
from greek_normalisation.normalise import Normaliser



class Generic(object):
    udnorm = 'NFD'

    @classmethod
    def ltNormalize(cls, string):
        """langtools normalize usually uses the unicodedata
        normalize() function; however, for many languages it
        will be overriden with a custom normalization function"""
        return normalize(cls.udnorm, string) 
    
    @classmethod
    def tokenize(cls, sentence, punc=False, clean=False,
                 splitters=None, non_splitters=('-',)):
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
        return cleanWords(sentence, norm=cls.udnorm, clean=clean,
                          splitters=splitters, non_splitters=non_splitters)
    
    @classmethod
    def splitTokenize(cls, sentence, punc=True, clean=False,
                      splitters=None, non_splitters=('-',)):
        """Tokenizes a sentence, while preserving punctuation.
        
        The difference with tokenize() is that splitTokenize
        preserves splits punctuation from the word.
        
        returns: ((pre, word, post), (pre, word, post), ...)
        """
        return splitPunc(sentence, norm=cls.udnorm, punc=punc, clean=clean,
                         splitters=splitters, non_splitters=non_splitters)

    # STANDARD TEXT OUTPUT FORMATS
    @classmethod
    def origWord(cls, token, split=True):
        """returns the original word according to the
        preferred unicode normalization as defined
        in tf_config.py
        
        returns 'normalized_string'
        """
        if split:
            return normalize(cls.udnorm, ''.join(word))
        else:
            return normalize(cls.udnorm, token)
    
    @classmethod
    def mainWord(cls, token, split=True, clean=True, splitters=None, non_splitters=('-',)):
        """returns the original word,
        but stripped of punctuation
        before, inbetween and after with
        normalized accentuation
        """
        if split:
            pre, word, post = token
            return normalize(cls.udnorm, word)
        else:
            return cleanWords(token, norm=cls.udnorm, clean=clean, split=split,
                              splitters=splitters, non_splitters=non_splitters)
    
    @staticmethod
    def plainWord(token, split=True, caps=False):
        if split:
            pre, word, post = token
            if caps:
                return plainCaps(word)
            else:
                return plainLow(word)
        else:
            if caps:
                return plainCaps(token)
            else:
                return plainLow(token)
                      

class Greek(Generic):
    udnorm = 'NFD'
    ELISION_norm = {normalize('NFC', k.strip('᾽')): v for k, v in ELISIONS.items()}

    @classmethod
    def replace(cls, word):
        plain_word = plainLow(word)
        if normalize('NFC', word) in ELISION_norm:
            return normalize(cls.udnormd, ELISION_norm[word])
        # Deletion of movable-nu
        elif plain_word.endswith(('εν', 'σιν', 'στιν')) and len(midWord_pl) >= 3:
            return word[:-1]
        # Handling final-sigma
        elif plain_word.endswith('σ'):
            return word[:-1] + 'ς'
        # Handling various forms of ου
        elif plain_word in ('ουχ', 'ουκ'):
            return word[:-1]
        # Handling ἐξ
        elif plain_word == 'εξ':
            return word[:-1] + 'κ'
        else:
            return word

    
    @classmethod
    def jtNormalize(cls, word):
        """This method returns a normalized word
        according to the normalization procedure
        of James Tauber; formatted in the NFD format.
        """
        return normalize(cls.udnorm, Normaliser().normalise(word))
        
    @staticmethod
    def startLemmatizer():
        """The lemmatizer contains only NFD formatted data
        """
        lemmatizer_open = open('data/lemmatizer.pickle', 'rb')
        lemmatizer = pickle.load(lemmatizer_open)
        lemmatizer_open.close()
        return lemmatizer
    
    @classmethod #TODO!
    def lemmatize(cls, word, lemmatizer):
        word = normalize('NFD', word.lower())
        if word in lemmatizer:
            lemma = ','.join(normalize(cls.udnorm, lemmatizer[word]))
        else: 
            word = cls.jtNormalize(word)
            if word in lemmatizer:
                lemma = ','.join(normalize(cls.udnorm, lemmatizer[word]))
            else:
                word = cls.plainWord(word)
                if word in lemmatizer:
                    lemma = ','.join(normalize(cls.udnorm, lemmatizer[word]))
                else:
                    lemma = f'*{word}'
        return normalize(cls.udnorm, lemma)

    @classmethod
    def beta2uni(cls, word):
        """Converts betacode to unicode"""
        beta_to_uni = Replacer()
        return normalize(cls.udnorm, beta_to_uni.beta_code(word))
    
    @staticmethod
    def uni2betaPlain(cls, word):
        """Converts unicode to unaccented betacode,
        to be used in the Morpheus morphological
        analyser
        """
        word_plain = plainLow(word)
        return betacode.conv.uni_to_beta(word_plain)
                      
    @staticmethod
    def morphology(plain_betacode_word):
        pass
    
    # ADDITIONAL TEXT OUTPUT FORMATS
    def normWord(cls, token, split=True):
        if split:
            pre, word, post = token
            w, analysis = cls.jtNormalize(word)
            return w
        else:
            w, analysis = cls.jtNormalize(token)
            return normalize(cls.udnorm, w)
                      
    def betaPlainWord(cls, token, split=True):
        if split:
            pre, word, post = token
            return cls.uni2betaPlain(word)
        else:
            return cls.uni2betaPlain(token)
                      
    def lemmaWord(cls, token, split=True):
        if split:
            pre, word, post = token
            return cls.lemmatize(word)
        else:
            return cls.lemmatize(token)
                      
class Latin(Generic):
    udnorm = 'NFD'
    
#     @staticmethod
#     def tokenize(self, string):
        
#     @staticmethod
#     def normalize(self):
        
#     @staticmethod
#     def lemmatize(self, word):
    
  
