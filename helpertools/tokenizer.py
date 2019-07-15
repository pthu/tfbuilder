import operator
from functools import reduce
from unicodedata import category, normalize, decomposition, lookup

# Definition of unicodedata categories
letter = {'L'}
dia = {'M'}
punc = {'P'}
letter_dia = {'L', 'M'}


def cleanWord(w): 
    """splitWord splits off punctuation and 
    non-word characters from a string, while 
    glueing together words that have one or 
    more non-letter characters inbetween.
    
    returns: ('string',)
    """
    pP = 0
    for i in range(len(w)):
        if category(w[i])[0] not in letter:
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
        if category(w[i])[0] not in letter:
            pA += 1
        else:
            break
    res = (realWord,) + (cleanWord(w[pA:]) if pA < len(w) else ())
    return res if not res == ('',) else ()


def tokenize(sentence):
    """tokenize feeds a sentence string
    to splitWord, while concatenating the
    resulting strings into one tuple.
    
    returns: ('string', 'string', ...)
    """
    return reduce(
        operator.add,
        (cleanWord(word) for word in sentence.strip().split()),
        (),
    )


def splitPunc():
    


def stripAccents(word):
    return ''.join(c for c in normalize('NFD', word.lower())
                  if category(c)[0] in letter)


