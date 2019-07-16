# Author: Ernst Boogert
# Institution: Protestant Theological University
# Date: July 16th, 2019

# Remarks:
# Several functions have originally been written by Dirk Roorda. 
# Most of them are modified by me later on. I am very grateful
# to Dirk for introducing me into the mechanics of unicodedata!

from unicodedata import category, normalize

letter = {'L'}
space = {'Z'}
letter_space = {'L', 'Z'}
dia = {'M'}
punc = {'P'}
letter_dia = {'L', 'M'}
udnorm = 'NFC'

def rsplitPunc(word, norm=udnorm, clean=False):
    '''This function splits off punctuation 
    from words on the RIGHT side of the word.
    
    returns (word, punc)
    '''
    w = normalize(norm, word)
    afterWord = len(w)
    for i in range(len(w) - 1, -1, -1):
        if category(w[i])[0] not in letter_dia:
            afterWord = i
        else:
            break
    if clean:
        return (''.join(c for c in w[0:afterWord] \
                          if category(c)[0] in letter_dia), w[afterWord:])
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
        if category(w[i])[0] not in letter_dia:
            beforeWord = i
        else:
            beforeWord +=1
            break
    if clean:
        return (w[0:beforeWord], ''.join(c for c in w[beforeWord:] \
                                           if category(c)[0] in letter_dia))
    else:
        return (w[0:beforeWord], w[beforeWord:])
    

def splitPunc(word, norm=udnorm, clean=False):
    '''This function splits off punctuation 
    from words on both sides of the word. 
    It returns a tuple with tuples, containing
    the punctuation before, the word itself, 
    and punctuation after.
    
    clean=False:
        if punctuation is within the word, the word
        will be split into two!
    clean=True:
        punctuation within a word will be deleted
    
    returns ((pre, word, after), (pre, word, after), ...)
    '''
    w = normalize(norm, word)
    pP = 0
    for i in range(len(w)):
        if category(w[i])[0] not in letter_dia:
            pP += 1
        else:
            break
    preWord = w[0:pP].strip() if pP else ''
    pW = pP
    for i in range(pP, len(w)):
        if category(w[i])[0] in letter_dia:
            pW += 1
        else:
            break
    word = w[pP:pW]
    pA = pW
    for i in range(pW, len(w)):
        if clean:
            if category(w[i])[0] in space:
                pA += 1
                break
            elif category(w[i])[0] in letter_dia:
                pW = i + 1
                pA = pW
                word += w[i]
            elif category(w[i])[0] not in letter_dia:
                pA += 1
        else:
            if category(w[i])[0] in space:
                pA += 1
                break
            elif category(w[i])[0] not in letter_dia:
                pA += 1
            else:
                break
    afterWord = w[pW:pA].strip()
    rest = splitPunc(w[pA:], clean=clean) if pA < len(w) else ()
    return ((preWord, word, afterWord),) + rest


def cleanWords(words, norm=udnorm, clean=False): 
    """cleanWords splits off any punctuation and 
    non-word characters from words in a string. 
    It can be used for cleaning single words,
    or to tokenize full sentences.
    
    clean=False:
        letter characters that have punctuation
        inbetween but no space, are split on punctuation
    
    clean=True:
        words with punctuation within (without whitespace) 
        are glued together without punctuation
    
    returns: ('string', 'string', ...)
    """
    w = normalize(norm, words)
    pP = 0
    for i in range(len(w)):
        if category(w[i])[0] not in letter_dia:
            pP += 1
        else:
            break
    pW = pP
    for i in range(pP, len(w)):
        if category(w[i])[0] in letter_dia:
            pW += 1
        else:
            break
    realWord = w[pP:pW]
    pA = pW
    for i in range(pW, len(w)):
        if clean:
            if category(w[i])[0] in space:
                break
            elif category(w[i])[0] not in letter_dia:
                pA += 1
            elif category(w[i])[0] in letter_dia:
                realWord += w[i]
                pA += 1
        else:
            if category(w[i])[0] not in letter_dia:
                pA += 1
            else:
                break
    if clean:
        res = (realWord,) + (cleanWords(w[pA:], clean=clean) if pA < len(w) else ())
        return res if not res == ('',) else ()
    else:
        res = (realWord,) + (cleanWords(w[pA:], clean=clean) if pA < len(w) else ())
        return res if not res == ('',) else ()

    
def tokenizer(sentence, norm=udnorm, punc=False, clean=False): #TODO add function input
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
    if punc:
        if clean:
            return tuple(f'{pre}{word}{post}' \
                for pre, word, post in splitPunc(sentence, norm=udnorm, clean=True))
        else:
            return tuple(f'{pre}{word}{post}' \
                for pre, word, post in splitPunc(sentence, norm=udnorm, clean=False))
            
    else:
        if clean:
            return cleanWords(sentence, clean=True)
        else:
            return cleanWords(sentence, clean=False)

# Text formatting
# NFD is used to split accents from letters;

# Conversions of full sentences with spaces
def plainMajuscule(tokens):
    return ''.join(c.upper() for c in \
                   normalize('NFD', ' '.join(tokens)) \
                   if category(c)[0] not in dia)

def plainMinuscule(tokens):
    return ''.join(c.lower() for c in \
                   normalize('NFD', ' '.join(tokens)) \
                   if category(c)[0] not in dia)

# Conversions of single word strings
def plainCaps(word):
    return ''.join(c.upper() for c in \
                   normalize('NFD', word) \
                   if category(c)[0] in letter)

def plainLow(word):
    return ''.join(c.lower() for c in \
                   normalize('NFD', word) \
                   if category(c)[0] in letter)
