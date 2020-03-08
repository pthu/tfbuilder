# Author: Ernst Boogert
# Institution: Protestant Theological University
# Date: January 21th, 2020

# Remarks:
# Several functions have originally been written by Dirk Roorda.
# Most of them are modified by me later on. I am very grateful
# to Dirk for introducing me into the mechanics of unicodedata!

from unicodedata import category, normalize

# letter = {'L'}
# space = {'Z'}
# letter_space = {'L', 'Z'}
# dia = {'M'}
# punc = {'P'}
# letter_dia = {'L', 'M'}

letter = {'Lu', 'Ll', 'Lt'}
space = {'Zs', 'Zl', 'Zp'}
dia = {'Mn', 'Mc', 'Me'}
punc = {'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po'}
letter_space = letter | space
letter_dia = letter | dia

udnorm = 'NFC'


def rsplitPunc(word, norm=udnorm, clean=False):
    '''This function splits off punctuation 
    from words on the RIGHT side of the word.

    returns (word, punc)
    '''
    w = normalize(norm, word)
    afterWord = len(w)
    for i in range(len(w) - 1, -1, -1):
        if category(w[i]) not in letter_dia:
            afterWord = i
        else:
            break
    if clean:
        return (''.join(c for c in w[0:afterWord]
                        if category(c) in letter_dia), w[afterWord:])
    else:
        return (w[0:afterWord], w[afterWord:])


def lsplitPunc(word, norm=udnorm, clean=False):
    '''This function splits off punctuation 
    from words on the LEFT side of the word.

    returns (punc, word)
    '''
    w = normalize(norm, word)
    beforeWord = -1
    for i in range(len(w)):
        if category(w[i]) not in letter_dia:
            beforeWord = i
        else:
            beforeWord += 1
            break
    if clean:
        return (w[0:beforeWord], ''.join(c for c in w[beforeWord:]
                                         if category(c) in letter_dia))
    else:
        return (w[0:beforeWord], w[beforeWord:])


def splitPunc(words, norm=udnorm, clean=False,
              splitters=None, non_splitters=None):
    '''This function splits off punctuation 
    from words on both sides of the word. 
    It returns a tuple with tuples, containing
    the punctuation before, the word itself, 
    and punctuation after. It can be used for
    multiple words

    clean=False:
        if punctuation is within the word, the word
        will be split into two, except for characters
        defined in the non-splitters list.
    clean=True:
        punctuation within a word will be deleted, 
        except for characters defined in the splitters 
        list. In that case, the string will be split.


    splitters=['character', 'character', ...]
    non_splitters=['character', 'character', ...]


    returns ((pre, word, after), (pre, word, after), ...)
    '''
    if splitters is None:
        splitters = ()
    if non_splitters is None:
        non_splitters = ()
    w = normalize(norm, words)
    pP = 0
    for i in range(len(w)):
        if category(w[i]) in space and pP > 0:
            pP += 1
            preWord = w[0:pP].strip('\n')
            if preWord:
                rest = splitPunc(w[pP:], clean=clean, splitters=splitters,
                                 non_splitters=non_splitters) if pP < len(w) else ()
                return ((preWord, '', ''),) + rest
            else:
                continue
        elif category(w[i]) not in letter_dia:
            pP += 1
        else:
            break
    preWord = w[0:pP].strip('\n') if pP else ''
    pW = pP
    for i in range(pP, len(w)):
        if w[i] in non_splitters:
            break
        elif category(w[i]) in letter_dia:
            pW += 1
        else:
            break
    word = w[pP:pW]
    pA = pW
    nsplit = False
    spaceBreak = False
    sLoc = None
    for i in range(pW, len(w)):
        if clean:
            if spaceBreak:
                if not category(w[i]) in letter_dia:
                    pA += 1
                    if category(w[i]) in space:
                        sLoc = pA
                else:
                    break
            elif category(w[i]) in space:
                pA += 1
                spaceBreak = True
                sLoc = pA
            elif w[i] in splitters:
                pA += 1
                break
            elif category(w[i]) in letter_dia:
                pW = i + 1
                pA = pW
                word += w[i]
            elif category(w[i]) not in letter_dia:
                pA += 1
        else:
            if spaceBreak:
                if not category(w[i]) in letter_dia:
                    pA += 1
                    if category(w[i]) in space:
                        sLoc = pA
                else:
                    break
            elif category(w[i]) in space:
                pA += 1
                spaceBreak = True
                sLoc = pA
            elif w[i] in non_splitters:
                nsplit = True
                continue
            elif category(w[i]) not in letter_dia:
                nsplit = False
                pA += 1
            elif category(w[i]) in letter_dia and nsplit == True:
                pW = i + 1
                pA = pW
                word += w[i]
            else:
                break
    if not sLoc:
        sLoc = pA
    afterWord = w[pW:sLoc].strip('\n')
    rest = splitPunc(w[sLoc:], clean=clean, splitters=splitters,
                     non_splitters=non_splitters) if sLoc < len(w) else ()
    return ((preWord, word, afterWord),) + rest


def cleanWords(words, norm=udnorm, clean=False,
               splitters=None, non_splitters=None):
    """cleanWords splits off any punctuation and 
    non-word characters from words in a string. 
    It can be used for cleaning single words,
    or to tokenize full sentences.

    clean=False:
        letter characters that have punctuation
        inbetween but no space, are split on punctuation
        exceptions can be defined in non_splitters

    clean=True:
        words with punctuation within (without whitespace) 
        are glued together without punctuation
        exceptions can be defined in splitters

    returns: ('string', 'string', ...)
    """
    if splitters is None:
        splitters = ()
    if non_splitters is None:
        non_splitters = ()
    w = normalize(norm, words)
    pP = 0
    for i in range(len(w)):
        if category(w[i]) not in letter_dia:
            pP += 1
        else:
            break
    pW = pP
    for i in range(pP, len(w)):
        if category(w[i]) in letter_dia:
            pW += 1
        else:
            break
    realWord = w[pP:pW]
    pA = pW
    nsplit = False
    for i in range(pW, len(w)):
        if clean:
            if category(w[i]) in space:
                break
            elif w[i] in splitters:
                break
            elif category(w[i]) not in letter_dia:
                pA += 1
            elif category(w[i]) in letter_dia:
                realWord += w[i]
                pA += 1
        else:
            if w[i] in non_splitters:
                nsplit = True
                continue
            elif category(w[i]) in letter_dia and nsplit == True:
                pW = i + 1
                pA = pW
                realWord += w[i]
            elif category(w[i]) not in letter_dia:
                nsplit = False
                pA += 1
            else:
                break
    res = (realWord,) + \
          (cleanWords(w[pA:], norm=udnorm, clean=clean,
                      splitters=splitters, non_splitters=non_splitters)
           if pA < len(w) else ())
    return res if not res == ('',) else ()


def tokenizer(sentence, norm=udnorm, punc=False, clean=False,
              splitters=None, non_splitters=None, func=None):
    """tokenize feeds a sentence string
    to splitWord, while concatenating the
    resulting strings into one tuple.

    clean=False:
        split on punctuation without whitespace
    clean=True:
        delete punctuation inside words
    clean=None

    returns: ('string', 'string', ...)
    """
    if func:
        func(sentence)
    else:
        if punc:
            if clean:
                return splitPunc(sentence, norm=udnorm, clean=True,
                                 splitters=splitters, non_splitters=non_splitters)
            else:
                return splitPunc(sentence, norm=udnorm, clean=False,
                                 splitters=splitters, non_splitters=non_splitters)
        else:
            if clean:
                return cleanWords(sentence, clean=True,
                                  splitters=splitters, non_splitters=non_splitters)
            else:
                return cleanWords(sentence, clean=False,
                                  splitters=splitters, non_splitters=non_splitters)

# Text formatting
# NFD is used to split accents from letters;


def stripAccents(word):
    return ''.join(c for c in normalize('NFD', word.lower())
                   if category(c) in letter)

# Conversions of full sentences with spaces


def plainMajuscule(tokens):
    return ''.join(c.upper() for c in
                   normalize('NFD', ' '.join(tokens))
                   if category(c) not in dia)


def plainMinuscule(tokens):
    return ''.join(c.lower() for c in
                   normalize('NFD', ' '.join(tokens))
                   if category(c) not in dia)

# Conversions of single word strings


def plainCaps(word):
    return ''.join(c.upper() for c in
                   normalize('NFD', word)
                   if category(c) in letter)


def plainLow(word):
    return ''.join(c.lower() for c in
                   normalize('NFD', word)
                   if category(c) in letter)
