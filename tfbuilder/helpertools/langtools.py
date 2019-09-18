# Languages.py contains several classes with methods that
# are important to process strings, both for TEI XML and CSV.
# Any information that is specific for the TEI XML 
# conversion, can be found in config.py
import pickle
from data import attrib_errors
from helpertools.unicodetricks import splitPunc, cleanWords, plainCaps, plainLow
from helpertools.data.greek_elisions import ELISIONS
from helpertools.data.greek_crasis import CRASIS
from cltk.corpus.greek.beta_to_unicode import Replacer
import betacode.conv

from unicodedata import normalize
from greek_normalisation.normalise import Normaliser



class Generic(object):
    udnorm = 'NFD'

    @classmethod
    def replace(cls, token):
        return token
    
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
        return splitPunc(sentence, norm=cls.udnorm, clean=clean,
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
            return normalize(cls.udnorm, ''.join(token))
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
    ELISION_norm = {normalize('NFC', k): v for k, v in ELISIONS.items()}
    CRASIS_norm = {normalize('NFC', k): v for k, v in CRASIS.items()}

    @classmethod
    def replace(cls, token):
        (pre, word, post) = token
        plain_word = plainLow(word)
        # Handling elided forms
        if normalize('NFC', word) in cls.ELISION_norm:
            return (pre, normalize(cls.udnorm, cls.ELISION_norm[normalize('NFC', word)]), post)
        elif post.startswith(('᾿', '’', '᾽', "'", 'ʹ')):
            if normalize('NFC', word + '᾽') in cls.ELISION_norm:
                return (pre, normalize(cls.udnorm, cls.ELISION_norm[normalize('NFC', word + '᾽')]), post)
            else:
                return token
        elif word.endswith(('᾿', '’', '᾽', "'", 'ʹ')):
            if normalize('NFC', word[:-1] + '᾽') in cls.ELISION_norm:
                return (pre, normalize(cls.udnorm, cls.ELISION_norm[normalize('NFC', word[:-1] + '᾽')]), post)
            else:
                return token
        # Handling crasis forms
        elif normalize('NFC', word) in cls.CRASIS_norm:
            return (pre, normalize(cls.udnorm, cls.CRASIS_norm[normalize('NFC', word)]), post)
        # Deletion of movable-nu
        elif plain_word.endswith(('εν', 'σιν', 'στιν')) and len(plain_word) >= 3:
            return (pre, word[:-1], post)
        # Handling final-sigma
        elif plain_word.endswith('σ'):
            return (pre, word[:-1] + 'ς', post)
        # Handling various forms of ου
        elif plain_word in ('ουχ', 'ουκ'):
            return (pre, word[:-1], post)
        # Handling ἐξ
        elif plain_word == 'εξ':
            return (pre, word[:-1] + 'κ', post)
        else:
            return token

    
    @classmethod
    def jtNormalize(cls, token):
        """This method returns a normalized word
        according to the normalization procedure
        of James Tauber; formatted in the NFD format.
        """
        pre, word, post = token
        return normalize(cls.udnorm, Normaliser().normalise(word)[0])
        
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
            lemma = normalize(cls.udnorm, ','.join(lemmatizer[word]))
        else: 
            word = cls.jtNormalize(('', word, ''))
            if word in lemmatizer:
                lemma = normalize(cls.udnorm, ','.join(lemmatizer[word]))
            else:
                word = cls.plainWord(('', word, ''))
                if word in lemmatizer:
                    lemma = normalize(cls.udnorm, ','.join(lemmatizer[word]))
                else:
                    lemma = f'*{normalize(cls.udnorm, word)}'
        return lemma

    @staticmethod
    def checkEncoding(elem):
        try:
            elem.encode('ascii')
            return 'beta'
        except UnicodeEncodeError:
            return 'uni'
    
    @classmethod
    def beta2uni(cls, word):
        """Converts betacode to unicode"""
        beta_to_uni = Replacer()
        return normalize(cls.udnorm, beta_to_uni.beta_code(word))
    
    @classmethod
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
    @classmethod
    def normWord(cls, token, split=True):
        if split:
            return normalize(cls.udnorm, cls.jtNormalize(token))
        else:
            return normalize(cls.udnorm, cls.jtNormalize(('', token, '')))
    
    @classmethod
    def betaPlainWord(cls, token, split=True):
        if split:
            pre, word, post = token
            return cls.uni2betaPlain(word)
        else:
            return cls.uni2betaPlain(token)
    
    @classmethod
    def lemmaWord(cls, token, lemmatizer, split=True):
        if split:
            pre, word, post = token
            return cls.lemmatize(word, lemmatizer)
        else:
            return cls.lemmatize(token, lemmatizer)
                      
class Latin(Generic):
    udnorm = 'NFD'
    
#     @staticmethod
#     def tokenize(self, string):
        
#     @staticmethod
#     def normalize(self):
        
#     @staticmethod
#     def lemmatize(self, word):
    
  
