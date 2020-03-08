# Langtools.py contains several classes with methods that
# are important to process strings, both for TEI XML and CSV.
# Any information that is specific for the TEI XML
# conversion, can be found in tf_config.py

import pickle
import betacode.conv
from unicodedata import normalize

# Local imports
from data import attrib_errors
from helpertools.unicodetricks import splitPunc, cleanWords, plainCaps, plainLow
from helpertools.data.greek import MOVEABLE_NU_ENDINGS, MOVEABLE_NU, ELISION, CRASIS, NOMINASACRA, BIBLICAL_BOOKS

# Functions and classes specific for Greek
from cltk.corpus.greek.beta_to_unicode import Replacer
from greek_normalisation.normalise import Normaliser
from greek_accentuation.syllabify import syllabify
from greek_accentuation.syllabify import add_necessary_breathing
from greek_accentuation.accentuation import possible_accentuations, add_accentuation

beta_to_uni = Replacer()


class Generic:
    udnorm = 'NFD'

    @classmethod
    def replace(cls, token):
        """NB the replace method should always return a list or tuple in the original token format"""
        return (token,)

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
    def mainWord(cls, token, split=True, comma=True, clean=True, splitters=None, non_splitters=('-',)):
        """returns the lowered original word,
        but stripped of punctuation
        before, inbetween and after with
        normalized accentuation
        """
        if split:
            pre, word, post = token
            word = word.lower()
            if comma:
                res = ','.join(set(word.split(',')))
            else:
                res = word.lower()
            return normalize(cls.udnorm, res)
        else:
            if comma:
                return ','.join(set(cleanWords(token, norm=cls.udnorm, clean=clean, split=split,
                                               splitters=splitters, non_splitters=non_splitters)))
            else:
                return cleanWords(token, norm=cls.udnorm, clean=clean, split=split,
                                  splitters=splitters, non_splitters=non_splitters)

    @staticmethod
    def plainWord(token, split=True, comma=True, caps=False):
        if split:
            pre, word, post = token
        else:
            word = token

        if comma:
            word_list = word.split(',')
        else:
            word_list = [word]

        word_set = set()
        for w in word_list:
            if not caps:
                word_set.add(plainLow(w))
            else:
                word_set.add(plainCaps(w))

        return ','.join(word_set)


class Greek(Generic):
    # NB all functions in Greek work internally with the NFD norm, however, when called, it is converted to the configured Unicode norm
    udnorm = 'NFD'
    ELISION_norm = {normalize('NFD', k): normalize('NFD', v)
                    for k, v in ELISION.items()}
    CRASIS_norm = {normalize('NFD', k): normalize('NFD', v)
                   for k, v in CRASIS.items()}

    ELISION_plain = {}
    for k, v in ELISION_norm.items():
        if plainLow(k) + '᾽' not in ELISION_plain:
            ELISION_plain[plainLow(k) + '᾽'] = {v}
        else:
            # NB This might result in multiple ','-separated wordforms!
            ELISION_plain[plainLow(k) + '᾽'].add(v)
            # ELISION_plain[plainLow(k) + '᾽'] = f"{ELISION_plain[plainLow(k) + '᾽']},{v}"
    # The value sets make sure that only unique forms are saved; however, they need to be converted to string
    ELISION_plain = {k: ','.join(v) for k, v in ELISION_plain.items()}

    @classmethod
    def replace(cls, token):
        pre, word, post = token
        # Convert to Unicode anyway, because sometimes there is Latin characters in Greek words
        # We also bring the Unicode type into concord with the norm: 'NFD'
        word = normalize(cls.udnorm, beta_to_uni.beta_code(word).lower())
        plain_word = plainLow(word)
        ELISION_signs = ('᾿', '᾽', "'", 'ʼ', 'ʹ', '’')

        # In handling elided forms, we need to take into account several things:
        # 1) the abbreviation sign can be part of 'pre', 'word', or 'post' depending on which sign has been used.
        # 2) the signs need to be replaced by the one used in the matching dictionary
        # 3) we are not entirely sure that the source texts are accentuated correctly

        # First, check whether the last/first character of the word is an abbreviation sign and replace it if True
        if word[-1] in ELISION_signs:
            word = word[:-1] + '᾽'
        if word[0] in ELISION_signs:
            word = '᾽' + word[1:]
        if plain_word[-1] in ELISION_signs:
            plain_word = plain_word[:-1] + '᾽'
        if plain_word[0] in ELISION_signs:
            plain_word = '᾽' + plain_word[1:]

        # We then check whether the accented form appears in ELISION_norm
        # ONLY IF IT DOESN'T, we check whether the plain form appears in ELISION_plain

        # Check whether the word is in  ELISION_norm
        if word in cls.ELISION_norm:
            word = cls.ELISION_norm[word]
        # Check whether the abbreviation sign resides in the 'pre' or 'post' parts
        elif post.startswith(ELISION_signs):
            if pre.endswith(ELISION_signs):
                if f'᾽{word}᾽' in cls.ELISION_norm:
                    word = cls.ELISION_norm[f'᾽{word}᾽']
                    pre, post = pre[:-1], post[1:]
            else:
                if f'{word}᾽' in cls.ELISION_norm:
                    word = cls.ELISION_norm[f'{word}᾽']
                    post = post[1:]
        elif pre.endswith(ELISION_signs):
            if f'᾽{word}' in cls.ELISION_norm:
                word = cls.ELISION_norm[f'᾽{word}']
                pre = pre[:-1]

        # If everything above was unsuccessful, we try the plain forms
        # Hence, we continue the elif and do not start with another if
        # Check the plain versions of elided forms
        # Check whether the word is in  ELISION_plain
        if plain_word in cls.ELISION_plain:
            word = cls.ELISION_plain[word]
        # Check whether the abbreviation sign resides in the 'pre' or 'post' parts
        elif post.startswith(ELISION_signs):
            if pre.endswith(ELISION_signs):
                if f'᾽{plain_word}᾽' in cls.ELISION_plain:
                    word = cls.ELISION_plain[f'᾽{plain_word}᾽']
                    pre, post = pre[:-1], post[1:]
            else:
                if f'{plain_word}᾽' in cls.ELISION_plain:
                    word = cls.ELISION_plain[f'{plain_word}᾽']
                    post = post[1:]
        elif pre.endswith(ELISION_signs):
            if f'᾽{plain_word}' in cls.ELISION_plain:
                word = cls.ELISION_plain[f'᾽{plain_word}']
                pre = pre[:-1]

        # NB the result of the plain-check might by multiple ','-separated words!
        # However, they cannot be crasis forms!

        # Handling crasis forms
        # NB crasis results in 2 words separated by space!
        if word in cls.CRASIS_norm:
            word = cls.CRASIS_norm[word]

        # Because crasis results in 2 words, we continue with a FOR statement!
        # We also define a new plain form!
        # We also define a result list into which the resulting tokens will be gathered
        # and we define a preAssigned that tells whether the pre-feature has already be assigned
        result = []
        preAssigned = False
        word_list = tuple(enumerate(word.split(' '), start=1))
        for n, w in word_list:
            w_plain = plainLow(w)

            # Deletion of movable-nu
            if w_plain in MOVEABLE_NU:
                w = w[:-1]

            # Next is unreliable!
    #         elif plain_word[-3:] in MOVEABLE_NU_ENDINGS and len(plain_word) > 3:
    #             repl_word = word[:-1]

            # Handling sigma's
            if 'ϲ' in w:
                w = ''.join((c if not c == 'ϲ' else 'σ' for c in w))
            if w.endswith('σ'):
                w = w[:-1] + 'ς'

            # Handling various forms of ου
            if w_plain in ('ουχ', 'ουκ'):
                w = w[:-1]
            # Handling ἐξ
            elif w_plain == 'εξ':
                w = w[:-1] + 'κ'
            # Handling nomina sacra
            # NB the check for nomina sacra expects the form to be unaccented!
            elif w in NOMINASACRA:
                w = NOMINASACRA[w_plain]

            # The next fase is that of accentuating unaccentuated words
            # NB any possible ','-separated value is anyway accentuated
            word_set = set()
            if w == plainLow(w):
                # Try to syllabify the word, but if it gives errors: just pass it...
                try:
                    s = syllabify(w)
                    for accentuation in possible_accentuations(s):
                        word_set.add(add_accentuation(s, accentuation))
                    for accentuation in possible_accentuations(s, default_short=True):
                        word_set.add(add_accentuation(s, accentuation))
                    w = ','.join(word_set)
                except:
                    pass

            # Put the results in the result list
            if len(word_list) > 1:
                if not preAssigned:
                    result.append(tuple((pre, w, ' ')))
                    preAssigned = True
                elif n == len(word_list):
                    result.append(tuple(('', w, post)))
                else:
                    result.append(tuple(('', w, ' ')))
            else:
                result.append(tuple((pre, w, post)))

        return tuple(result)

    @classmethod
    def jtNormalize(cls, token, comma=True):
        """This method returns a normalized word
        according to the normalization procedure
        of James Tauber; formatted in the NFD format.
        """
        pre, word, post = token
        if comma:
            res = ','.join(set(
                [normalize(cls.udnorm, Normaliser().normalise(w)[0]) for w in word.split(',')]))
        else:
            res = normalize(cls.udnorm, Normaliser().normalise(word)[0])
        return res

    @staticmethod
    def startLemmatizer():
        """The lemmatizer contains NFD formatted data only
        """
#         lemmatizer = {0:0} # dummy
        print('    |  loading lemmatizer...')
        print('    |  ...')
        lemmatizer_open = open('data/lemmatizer.pickle', 'rb')
        lemmatizer = pickle.load(lemmatizer_open)
        lemmatizer_open.close()
        return lemmatizer

#     Start the lemmatizer immediately to be used in the lemmatize() method
#     lemmatizer = startLemmatizer.__func__()

    @classmethod
    def lemmatize(cls, word, lemmatizer, comma=True):
        word = normalize('NFD', word.lower())

        def worker(word):
            if word in lemmatizer:
                lemma = normalize(cls.udnorm, ','.join(lemmatizer[word]))
            else:
                word = cls.jtNormalize(('', word, ''))
                if word in lemmatizer:
                    lemma = normalize(cls.udnorm, ','.join(lemmatizer[word]))
                else:
                    word = cls.plainWord(('', word, ''))
                    if word in lemmatizer:
                        lemma = normalize(
                            cls.udnorm, ','.join(lemmatizer[word]))
                    else:
                        lemma = f'*{normalize(cls.udnorm, word)}'
            return lemma

        if comma:
            word_list = word.split(',')
            result_set = set()
            for w in word_list:
                result_set.update(worker(w).split(','))
            res = ','.join(result_set)
        else:
            res = worker(word)
        return res

#     @staticmethod
#     def checkEncoding(elem):
#         try:
#             elem.encode('ascii')
#             return 'beta'
#         except UnicodeEncodeError:
#             return 'uni'

    @classmethod
    def beta2uni(cls, word):
        """Converts betacode to unicode"""
#         beta_to_uni = Replacer()
        return normalize(cls.udnorm, beta_to_uni.beta_code(word))

    # @classmethod
    # def uni2betaPlain(cls, word):
    #     """Converts unicode to unaccented betacode,
    #     to be used in the Morpheus morphological
    #     analyser
    #     """
    #     word_plain = plainLow(word)
    #     return betacode.conv.uni_to_beta(word_plain)

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
            word_plain = cls.plainWord(
                token, split=True, comma=True, caps=False)
            return betacode.conv.uni_to_beta(word_plain)
        else:
            word_plain = cls.plainWord(
                token, split=False, comma=True, caps=False)
            return betacode.conv.uni_to_beta(word_plain)

    @classmethod
    def lemmaWord(cls, token, lemmatizer, split=True):
        if split:
            pre, word, post = token
            return cls.lemmatize(word, lemmatizer)
        else:
            return cls.lemmatize(token, lemmatizer)

    @classmethod
    def cleanPlain(cls, token, split=True):
        if split:
            pre, word, post = token
            return ''.join((c for c in cls.plainWord(word, split=False) if not c in {'ι', 'ν', 'σ', 'ς'}))
        else:
            return ''.join((c for c in cls.plainWord(token) if not c in {'ι', 'ν', 'σ', 'ς'}))


class Latin(Generic):
    udnorm = 'NFD'

#     @staticmethod
#     def tokenize(self, string):

#     @staticmethod
#     def normalize(self):

#     @staticmethod
#     def lemmatize(self, word):
