import operator
from functools import reduce
from unicodedata import category, normalize, decomposition, lookup

# Definition of unicodedata categories
letter = {'L'}
dia = {'M'}
punc = {'P'}
letter_dia = {'L', 'M'}


def splitWord(word, norm='NFD'): 
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
    return (realWord,) + (splitWord(w[pA:]) if pA < len(w) else ())


def tokenize(sentence, norm='NFD'):
    return reduce(
        operator.add,
        (splitWord(word) for word in sentence.strip().split()),
        (),
    )


def stripAccents(word):
    return ''.join(c for c in normalize('NFD', word.lower())
                  if category(c)[0] in letter)

