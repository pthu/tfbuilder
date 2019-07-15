# Several functions have originally been written by Dirk Roorda. 
# Some of them are modified later on by me. I am very grateful
# to Dirk for introducing me into the mechanics of unicodedata!

import pickle
from unicodedata import category, normalize
from pprint import pprint

letter = {'L'}
letter_space = {'L', 'Z'}
dia = {'M'}
punc = {'P'}
letter_dia = {'L', 'M'}
udnorm = 'NFC'

# Handling of punctuation connected to words
# NB: stripping of punctuation works best on 
#     NFC(!) formatted text!
# Be aware that any function returns text in NFC!

def rsplitPunc(word, norm=udnorm):
    '''This function splits off punctuation 
    from words on the RIGHT side of the word.
    
    returns (word, punc)
    '''
    w = normalize(norm, word)
    afterWord = len(w)
    for i in range(len(w) - 1, -1, -1):
        if category(w[i])[0] not in letter:
            afterWord = i
        else:
            break
    return (w[0:afterWord], w[afterWord:])

def lsplitPunc(word, norm=udnorm):
    '''This function splits off punctuation 
    from words on the LEFT side of the word.
    
    returns (punc, word)
    '''
    w = normalize(norm, word)
    beforeWord = 0
    for i in range(len(w) - 1):
        if category(w[i])[0] not in letter:
            beforeWord = i
        else:
            beforeWord +=1
            break
    return (w[0:beforeWord], w[beforeWord:])


def splitPunc(word, norm=udnorm):
    '''This function splits off punctuation 
    from words on both sides of the word.
    '''
    w = normalize(norm, word)
    pP = 0
    for i in range(len(w)):
        if category(w[i])[0] not in letter:
            pP += 1
        else:
            break
    preWord = w[0:pP] if pP else ''
    pW = pP
    for i in range(pP, len(w)):
        if category(w[i])[0] in letter:
            pW += 1
        else:
            break
    word = w[pP:pW]
    pA = pW
    for i in range(pW, len(w)):
        if category(w[i])[0] not in letter:
            pA += 1
        else:
            break
    afterWord = w[pW:pA]
    if pA == len(w):
        afterWord += ' '
    
    rest = splitPunc(w[pA:]) if pA < len(w) else ()
    return ((preWord, word, afterWord),) + rest


# Tokenization

def splitWord(word, norm=udnorm):
    '''splitWord is an advanced tokenizer, that
    splits text on the basis of non-letter characters,
    like space and punctuation.
    '''
    w = normalize(norm, word)
    tokens = ()
    pP = 0
    for i in range(len(w)):
        if category(w[i])[0] not in letter:
            pP += 1
        else:
            break
    pW = pP
    for i in range(pP, len(w)):
        if category(w[i])[0] in letter:
            pW += 1
        else:
            break
    realWord = w[pP:pW]
    pA = pW
    for i in range(pW, len(w)):
        if category(w[i])[0] not in letter:
            pA += 1
        else:
            break
    return (realWord,) + (splitWord(w[pA:]) if pA < len(w) else ())

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
                   normalize('NFD', wword) \
                   if category(c)[0] in letter)
