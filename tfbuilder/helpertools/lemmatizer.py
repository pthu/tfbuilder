
# coding: utf-8

# 
# # Lemmatizer of Greek text
# 
# This file provides a function (createLemmatizer) that creates (pickles) a dictionary that contains Greek wordforms as its keys and its possible lemmata as values (set). It also provides a function (lemmatize) that takes two arguments: a wordstring and the just created dictionary of lemmata. It returns a string with the possible lemmata in comma-separated format.
# 
# If you like to use these functions, be aware to load the lemmatizer (=lemma dictionary) only once...
# 


import pickle
from unicodedata import normalize, category
from os import path
# from pprint import pprint
import xml.etree.ElementTree as etree
from tf.fabric import Timestamp
# import nbimporter

udnorm = 'NFD'

REPO = '~/github/pthu/tei_to_tf/'
SRC_DIR = path.expanduser(f'{REPO}helpertools/data')
SOURCE1 = SRC_DIR + '/forms-normalised-20180208_001.txt'
SOURCE2 = SRC_DIR + '/MorpheusUnicode.xml'

letter = {'L'}


MANUAL_FORMS = {
    'θεὸς': 'θεός',
    'ἰδοὺ': 'ἰδοὺ',
    'ἐμὲ': 'ἐμός',
    'τάυτην': 'οὗτος',
    'εὐλογημένος': 'εὐλογέω',
    'δαβίδ': 'δαβίδ',
    'ὡσαννά': 'ὡσαννά',
    'ἐγὼ': 'ἐγώ',
    'μωσέως': 'μωσέως',
    'ἱερουσαλήμ': 'ἱερουσαλήμ',
    'ἔρχεταί': 'ἔρχομαι',
    'ἡσαΐου': 'ἡσαΐου',
    'ἰσαὰκ': 'ἰσαὰκ'
}
    

def strip_accents(word):
    return ''.join(c for c in normalize(udnorm, word.lower())
                   if category(c)[0] in letter)

def createLemmatizer(sourcepath1, sourcepath2):
    lemma_dict = {}
    with open(sourcepath1) as source1:
        for line in source1:
            form, alternative, morphology, lemma = line.strip().split("\t")
            form1 = normalize(udnorm, form.lower())
            form2 = strip_accents(form1)
            alternative1 = normalize(udnorm, alternative.lower())
            alternative2 = strip_accents(alternative1)
            lemma = normalize(udnorm, lemma.lower())
            if form1 in lemma_dict:
                lemma_dict[form1].add(lemma)
            else:
                lemma_dict[form1] = {lemma}
            if form2 in lemma_dict:
                lemma_dict[form2].add(lemma)
            else:
                lemma_dict[form2] = {lemma}
                
            if alternative1 in lemma_dict:
                lemma_dict[alternative1].add(lemma)
            else:
                lemma_dict[alternative1] = {lemma}
            if alternative2 in lemma_dict:
                lemma_dict[alternative2].add(lemma)
            else:
                lemma_dict[alternative2] = {lemma}
                
    with open(sourcepath2) as source2:
        tree = etree.parse(source2)
        for elem in tree.iter('t'):
            form1a = normalize(udnorm, elem.findtext('f').lower())
            form2a = normalize(udnorm, elem.findtext('b').lower())
            form1b = strip_accents(elem.findtext('f').lower())
            form2b = strip_accents(elem.findtext('b').lower())
            lemma = normalize(udnorm, elem.findtext('l').lower())
            if form1a in lemma_dict:
                lemma_dict[form1a].add(lemma)
            else:
                lemma_dict[form1a] = {lemma}
            if form2a in lemma_dict:
                lemma_dict[form2a].add(lemma)
            else:
                lemma_dict[form2a] = {lemma}
                
            if form1b in lemma_dict:
                lemma_dict[form1b].add(lemma)
            else:
                lemma_dict[form1b] = {lemma}
            if form2b in lemma_dict:
                lemma_dict[form2b].add(lemma)
            else:
                lemma_dict[form2b] = {lemma}
        tree = None
        
    from data.greek_lemmata_cltk import LEMMATA
        
    for key, value in LEMMATA.items():
        formA = normalize(udnorm, key.lower())
        formB = strip_accents(key.lower())
        lemma = normalize(udnorm, value.lower())
        if formA in lemma_dict:
            lemma_dict[formA].add(lemma)
        else:
            lemma_dict[formA] = {lemma}
        if formB in lemma_dict:
            lemma_dict[formB].add(lemma)
        else:
            lemma_dict[formB] = {lemma}
            
    for key, value in MANUAL_FORMS.items():
        formA = normalize(udnorm, key.lower())
        formB = strip_accents(key.lower())
        lemma = normalize(udnorm, value.lower())
        if formA in lemma_dict:
            lemma_dict[formA].add(lemma)
        else:
            lemma_dict[formA] = {lemma}
        if formB in lemma_dict:
            lemma_dict[formB].add(lemma)
        else:
            lemma_dict[formB] = {lemma}
    
    # Handle movable-nu and final-sigma
    lemma_dict_add = {}
    for wordform in lemma_dict:
        if strip_accents(wordform).endswith(('εν', 'σιν', 'στιν')) and len(strip_accents(wordform)) > 2:
            if wordform[:-1] in lemma_dict:
                pass
            else:
                lemma_dict_add[wordform[:-1]] = lemma_dict[wordform]
        elif wordform.endswith('σ'):
            if wordform[:-1] + 'ς' in lemma_dict:
                pass
            else:
                lemma_dict_add[wordform[:-1] + 'ς'] = lemma_dict[wordform]
    lemma_dict.update(lemma_dict_add)
    
    with open(SRC_DIR + '/lemmatizer.pickle', 'wb') as lemmatizer:
        pickle.dump(lemma_dict, lemmatizer, protocol=pickle.HIGHEST_PROTOCOL)
    
# Run the creation process    
#createLemmatizer(SOURCE1, SOURCE2)


def lemmatize(word, lemmatizer):
    word = normalize('NFD', word.lower())
    if word in lemmatizer:
        word = ','.join(lemmatizer[word])
    else:
        word = f'*{word}'
    return word
        

# Small test setup

# lemmatizer_open = open(SRC_DIR + '/lemmatizer.pickle', 'rb')
# lemmatizer = pickle.load(lemmatizer_open)

# selection = {k: v for k, v in sorted(lemmatizer.items())[:100]}
# pprint(selection)
# pprint(f'The total number of available wordforms = {len(lemmatizer)}')

# lemmatize('ἐΠράχθη', lemmatizer)
# lemmatizer_open.close()



