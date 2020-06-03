# General imports
import re
import pickle
import csv
import betacode.conv
from os import path
from glob import glob
from pprint import pprint
from itertools import takewhile
from ordered_set import OrderedSet
from unicodedata import category, normalize
from collections import OrderedDict, namedtuple
from multiprocessing import Pool

# Text Fabric imports
from tf.fabric import Fabric, Timestamp
from tf.convert.walker import CV

# Local imports
from helpertools.unicodetricks import *
from helpertools.lemmatizer import lemmatize
from helpertools.xmlparser import xmlSplitter, dataParser, metadataReader, attribsAnalysis
from data.tlge_metadata import tlge_metadata
from data.attrib_errors import error_dict
from tf_config import langsettings, generic_metadata


class Conversion:
    def __init__(self, data, **kwargs):
        self.data = data                                # Data in preprocessed XML or CSV
        for setting, value in kwargs.items():                  # Set langsettings in tf_config as class attributes
            # NB 'lang' defines the part of langsettings
            setattr(self, setting, value)
        # Define indexes of features in token output tokenizer
        self.featuresInd = self.token_features(self.token_out)

        # Collect feature restricted metadata from tf_config
        self.featureMeta = {
            **{k: {'description': v['description']} for k, v in self.text_formats.items()},
            **{k: {'description': v['description']} for k, v in self.token_out.items()},
            **{k: {'description': v} for k, v in self.struct_counter_metadata.items()}}
        self.nonIntFeatures = kwargs['nonIntFeatures'].copy() | \
            {k for k in self.token_out} | \
            {k for k in self.text_formats}

        # Variables used in processing
        self.res_text = None    # Handle text that ends with non_splitter

    def token_features(self, token_out):
        featuresInd = []
        for i, (part, value) in enumerate(token_out.items()):
            if value['text'] == False:
                featuresInd.append((i, part))
            # Add to nonIntFeatures, because all stringparts are expected to be non-ints
            self.nonIntFeatures.add(part)
        return tuple(featuresInd)

    def process_text(self, text):
        # Normalise text according to the defined udnorm
        text = normalize(self.udnorm, text)
        text_output = []

        # Handle wordbreaks
        if self.res_text != None:
            text, self.res_text = self.res_text + text, None
        if text.endswith(self.tokenizer_args['non_splitters']):
            if ' ' in text.strip():
                text, self.res_text = text.rstrip(
                    ''.join(self.tokenizer_args['non_splitters'])).rsplit(' ', 1)
                text += ' '  # Add space deleted by split(' ')
            else:
                text, self.res_text = '', text.strip()

        # Handle punctuation that still does not belong to a word
        punc = ''

        # Process text
        for t in self.tokenizer(text, **self.tokenizer_args):
            # Check whether t contains text
            (pre, word, post) = t
            if plainLow(word) == '':
                punc += pre
                continue

            # Check whether there is any punctuation left
            if not punc == '':
                pre = punc + pre
                punc = ''

            # Check formats that need to be processed BEFORE the replacement function runs
            beforeReplaceAssigned = False
            form_dict = {}
            for form, sett in self.text_formats.items():
                if sett['before_replace'] == True:
                    form_dict[form] = normalize(
                        self.udnorm, sett['function'](t))

            # NB The replace_func might return multiple tokens if words are split like greek crasis forms
            for token in self.replace_func(t):
                token_processed = {}

                # Assign pre-replace formats
                if not beforeReplaceAssigned:
                    for form in form_dict:
                        token_processed[form] = form_dict[form]
                    beforeReplaceAssigned = True
                else:
                    for form in form_dict:
                        token_processed[form] = ''

                # Process text data
                for form, sett in self.text_formats.items():
                    if form not in token_processed:  # Prevent the replacement of pre-replace formats
                        # Special treatment of the lemma format, since it requires a lemmatizer argument
                        if not form == 'lemma':
                            token_processed[form] = normalize(
                                self.udnorm, sett['function'](token))
                        else:
                            token_processed[form] = normalize(
                                self.udnorm, sett['function'](token, self.lemmatizer))

                # Process feature data
                for i, part in self.featuresInd:
                    token_processed[part] = token[i]

                # Append dict to output list
                text_output.append(token_processed)

        # Output list of dicts with text and feature data to be assigned to slot nodes
        return text_output


class Csv2tf(Conversion):
    def __init__(self, data, first_line=None, **kwargs):
        super().__init__(data, **kwargs)
        self.first_line = first_line
        self.head = self.get_header(self.header)
        self.sections = self.head[:-1] if self.header == True \
            else (list(filter(None, self.generic['citation_scheme'].lower().split('/')))
                  if 'citation_scheme' in self.generic
                  else list(filter(None, input("No header data could be found; "
                                               "please enter an appropriate header: ").lower().split())))
        self.structs = tuple(
            ('_book',) + tuple(self.head[:-1]) + tuple(self.struct_counter))
        self.otext = {
            **{v['otext_name']: v['format'] for k, v in self.text_formats.items()},
            **{'sectionTypes': f'{",".join(self.sections[:2] + [self.sections[-1]] if len(self.sections) > 2 else self.sections)}'},
            **{'sectionFeatures': f'{",".join(self.sections[:2] + [self.sections[-1]] if len(self.sections) > 2 else self.sections)}'},
            **{'structureTypes': f'{",".join(self.structs)}'},
            **{'structureFeatures': f'{",".join(self.structs)}'}
        }

        # Calculate metadata for struct levels
        for num, struct in enumerate(self.structs[1:], 1):
            self.featureMeta[struct] = {
                'description': f'structure feature of the {num}{"st" if num == 1 else ""}{"nd" if num == 2 else ""}{"rd" if num == 3 else ""}{"th" if num > 3 else ""} level', }

        # Handle tlg head text marked by {head}
        self.head_signs = {'start': {'{', },
                           'stop': {'}', }, }

    def get_header(self, head):

        def check_header(measure, typed_input):
            if len(typed_input) == measure:
                return [h.lower() for h in typed_input]
            else:
                print(
                    f'The inputed number of header titles is {len(typed_input)}, while it should be {measure}')
                typed_input = list(filter(None, input(
                    "No header data could be found; please enter an appropriate header split by spaces:").split()))
                # Recursive loop till the length of the header is correct...
                check_header(measure, typed_input)

        # levels = len(self.data[0].split('\t'))
        first_line = self.first_line
        levels = len(first_line)

        if head == False:
            header = check_header(levels, list(filter(None, input(
                f"No header data could be found; please enter an appropriate header...\nThe first line is: '{first_line}'\n").split())))
        else:
            if isinstance(head, (list, tuple)):
                header = check_header(levels, head)
            elif self.header == True:
                header = next(self.data)
                # levels = len(self.data[0].split('\t'))
                # header = check_header(levels, header)
            else:
                print("something is wrong with the header...!")
        return [h.lower() for h in header]

    def director(self, cv):
        # keep track of features that are not ints
        nonIntFeatures = self.nonIntFeatures.copy()
        # keep track of calculated struct features defined in tf_config
        counter = self.struct_counter.copy()
        udnorm = self.udnorm                   # define the Unicode norm used
        # keep track of wordforms converted successfully to lemmata
        lemma_counter = [0, 0]
        cur = {}                            # keep track of node number assignments

        # VARIABLES TO PROCESS PREPROCESSED TLG-E OUTPUT
        # if true text will be processed as head-feature
        tlg_head = False
        tlg_head_cont = ''                            # variable to store head text elements

        # Define bookname and start first node assignment to cur
        cur['_book'] = cv.node('_book')
        book_title = self.generic['title'] if 'title' in self.generic else 'no title found in metadata'
        book_title_full = self.generic['title_full'] if 'title_full' in self.generic else book_title
        cv.feature(cur['_book'], _book=book_title)
        cv.meta('_book', description=book_title_full)
        nonIntFeatures.add('_book')

        # Initiate counters
        for count in counter:
            cur[count] = cv.node(count)
            cv.feature(cur[count], **{count: counter[count]})

        w = False

        # PROCESS CSV-DATA LINE BY LINE
        # TODO! To be updated to the csv library
        for row in self.data:
            #             refAssigned = False
            # Split reference and text; NB text is always the last element!
            ref = row[:-1]
            text = row[-1].strip()
            if not text.endswith(self.tokenizer_args['non_splitters']):
                text += ' '

            # PROCESS TEXT
            # NB token_out is a dictionary with all the text/feature formats
            for token_out in self.process_text(text):

                # ------------------------------------------------
                # Handle TLG head titles (words enclosed in {...})
                if self.typ == 'tlge':
                    if tlg_head == True:
                        # In case 'pre' or 'post' has the head end sign
                        if self.head_signs['stop'] & (set(token_out['pre']) | set(token_out['post'])):
                            tlg_head = False
                            if 'head' in cur:
                                cv.terminate(cur['head'])
                            cur['head'] = cv.node('head')
                            cv.meta('head', description="head title",)
                            nonIntFeatures.add('head')
                            if self.head_signs['stop'] & set(token_out['pre']):
                                content = tlg_head_cont
                            if self.head_signs['stop'] & set(token_out['post']):
                                content = tlg_head_cont + \
                                    f"{token_out['orig']}"
                            cv.feature(cur['head'], **{'head': content})
                            tlg_head_cont = ''
                            if self.head_signs['stop'] & set(token_out['post']):
                                continue
                        # In case the token is fully part of the tlg head
                        else:
                            tlg_head_cont += f"{token_out['orig']}"
                            continue
                    if tlg_head == False:
                        if self.head_signs['start'] & set(token_out['pre']):
                            # if the whole head is in one token_out
                            if self.head_signs['stop'] & (set(token_out['pre']) | set(token_out['post'])):
                                if 'head' in cur:
                                    cv.terminate(cur['head'])
                                content = f"{token_out['orig']}"
                                cur['head'] = cv.node('head')
                                cv.feature(cur['head'], **{'head': content})
                                cv.meta('head', description="head title",)
                                nonIntFeatures.add('head')
                                continue
                            else:
                                tlg_head = True
                                tlg_head_cont += f"{token_out['orig']}"
                                continue
                        else:
                            if self.head_signs['start'] & set(token_out['post']):
                                tlg_head = True
                                token_out['post'], tlg_head_cont = token_out['post'].split(
                                    ''.join(self.head_signs['start']), 1)
                                tlg_head_cont = ''.join(
                                    self.head_signs['start']) + tlg_head_cont
                # End tlg heads
                # ----------------------------------------------

                # Handle empty tokens that still have a pre feature, by adding them to the previous post and orig
                if 'plain' in token_out and token_out['plain'] == '':
                    if 'pre' in token_out and 'post' in token_out:
                        try:  # if there is already an existing slot number
                            cv.resume(w)
                            pre = token_out['pre']
                            orig = cv.get('orig', w) + pre
                            cv.feature(w, orig=orig)
                            post = cv.get('post', w) + pre
                            cv.feature(w, post=post)
                            # Check phrase and sentence counters
                            if set(pre) & self.phrase_delimit:
                                if cv.linked(cur['_phrase']):
                                    cv.terminate(cur['_phrase'])
                                    counter['_phrase'] += 1
                                    cur['_phrase'] = cv.node('_phrase')
                                    cv.feature(
                                        cur['_phrase'], **{'_phrase': counter['_phrase']})
                            if set(pre) & self.sentence_delimit:
                                for count in ('_phrase', '_sentence'):
                                    if cv.linked(cur[count]):
                                        cv.terminate(cur[count])
                                        counter[count] += 1
                                        cur[count] = cv.node(count)
                                        cv.feature(
                                            cur[count], **{count: counter[count]})
                            cv.terminate(w)
                        except:
                            pass
                    continue

                # HANDLE SECTIONING
#                 if refAssigned == False:
                for ind, sec in enumerate(self.sections):
                    # Check whether section level is active
                    if sec in cur and cv.active(cur[sec]):
                        # Get the current section value
                        cur_sec = cv.get(sec, cur[sec])
                        # Get the section value in the present line
                        new_sec = ref[ind]
                        if not cur_sec == new_sec:                  # Check whether the old and the new value are equal
                            # If not, terminate all lower section levels
                            for s in self.sections[:ind:-1]:
                                cv.terminate(cur[s])
                            # Terminate the current section level
                            cv.terminate(cur[sec])
                            # Create new section node
                            cur[sec] = cv.node(sec)
                            # Add new value to the new section node
                            cv.feature(cur[sec], **{sec: ref[ind]})
                    else:                                           # In case the section is not present in cur OR not active
                        # Create new section node
                        cur[sec] = cv.node(sec)
                        # Add new value to section node
                        cv.feature(cur[sec], **{sec: ref[ind]})
                    # Check whether the value is not an int
                    if not ref[ind].isdigit():
                        # In case the value is no int, add the FEATURE to the set of nonIntFeatures
                        nonIntFeatures.add(sec)
#                     refAssigned = True

                # SLOT ASSIGNMENT!
                # ================
                w = cv.slot()
                # Handle the data dictionary with text formats and features
                for name, value in token_out.items():
                    cv.feature(w, **{name: value})

                # ================

                # Check phrase and sentence counters
                if 'post' in token_out:
                    if set(token_out['post']) & self.phrase_delimit:
                        if cv.linked(cur['_phrase']):
                            cv.terminate(cur['_phrase'])
                            counter['_phrase'] += 1
                            cur['_phrase'] = cv.node('_phrase')
                            cv.feature(cur['_phrase'], **
                                       {'_phrase': counter['_phrase']})
                    if set(token_out['post']) & self.sentence_delimit:
                        for count in ('_phrase', '_sentence'):
                            if cv.linked(cur[count]):
                                cv.terminate(cur[count])
                                counter[count] += 1
                                cur[count] = cv.node(count)
                                cv.feature(cur[count], **
                                           {count: counter[count]})

                # Run lemma counter
                if 'lemma' in token_out:
                    if token_out['lemma'].startswith('*'):
                        lemma_counter[1] += 1
                    else:
                        lemma_counter[0] += 1

        # In case the csv-file has a header, but is empty:
        # assign one empty slot in case of ignore_empty == False
        if not w:
            if self.ignore_empty == False:
                for struct in self.structs:
                    if not struct in cv.activeTypes():
                        cur[struct] = cv.node(struct)
                        cv.feature(cur[struct], **{struct: 0})
                w = cv.slot()
                for name, __ in token_out.items():
                    cv.feature(w, **{name: ''})
            else:
                cv.stop(
                    'it looks like no slot numbers could be produced from the source-file; the file will be ignored.')

        # Terminate structs (includes sections!)
        for ntp in self.structs[::-1]:
            if ntp in cur:
                cv.terminate(cur[ntp])
        # Terminate any remaining active nodes in cur
        for ntp in cur:
            if ntp in cur:
                cv.terminate(cur[ntp])

        # Calculate lemmatizer coverage of lemmata
        if not lemma_counter == [0, 0]:
            cv.meta(
                'lemma', **{'coverage_ratio': f'{round(lemma_counter[0] / ((lemma_counter[0] + lemma_counter[1]) / 100 ), 2)}%'})

        # Assign the correct valueType to features
        for feature in cv.metaData:
            if feature in nonIntFeatures:
                cv.meta(feature, valueType='str')
            else:
                if feature == "":
                    pass
                else:
                    cv.meta(feature, valueType='int')


class Xml2tf(Conversion):
    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)
        self.analyzed_dict,         self.sections = attribsAnalysis(
            self.data, **kwargs)
        self.structs = tuple(
            ('_book',) + tuple(self.sections) + tuple(self.struct_counter))

        self.otext = {
            **{v['otext_name']: v['format'] for k, v in self.text_formats.items()},
            **{'sectionTypes': f'{",".join(self.sections[:2] + [self.sections[-1]] if len(self.sections) > 2 else self.sections)}'},
            **{'sectionFeatures': f'{",".join(self.sections[:2] + [self.sections[-1]] if len(self.sections) > 2 else self.sections)}'},
            **{'structureTypes': f'{",".join(self.structs)}'},
            **{'structureFeatures': f'{",".join(self.structs)}'}
        }

        for num, struct in enumerate(self.structs[1:], 1):
            self.featureMeta[struct] = {
                'description': f'structure feature of the {num}{"st" if num == 1 else ""}{"nd" if num == 2 else ""}{"rd" if num == 3 else ""}{"th" if num > 3 else ""} level', }

    def director(self, cv):
        # keep track of features that are not ints
        nonIntFeatures = self.nonIntFeatures.copy()
        # keep track of calculated struct features defined in tf_config
        counter = self.struct_counter.copy()
        udnorm = self.udnorm                   # define the Unicode norm used
        # keep track of wordforms converted successfully to lemmata
        lemma_counter = [0, 0]
        cur = {}                            # keep track of node number assignments
        tagList = []			     # keep track of the XML tags
        # keep track of features that are linked together
        linked_features_dict = {}

        # Define bookname and start first node assignment to cur
        tagList.append('_book')
        cur['_book'] = cv.node('_book')
        book_title = self.generic['title'] if 'title' in self.generic else 'no title found in metadata'
        book_title_full = self.generic['title_full'] if 'title_full' in self.generic else book_title
        cv.feature(cur['_book'], _book=book_title)
        cv.meta('_book', description=book_title_full)
        nonIntFeatures.add('_book')

        w = False

        # PROCESS XML-DATA
        for code, content in self.data:
            if code == 'text':
                # Check whether the text is part of non-text data like head- or note-features
                # TODO: position footnotes
#                 print(tagList)
                if tagList[-1] in self.non_text_tags:
                    tag = tagList[-1]
                    content = normalize(udnorm, content)
                    if tag in cur and not cv.linked(cur[tag]):
                        content = f'{cv.get(tag, cur[tag])} {content}'
                        cv.feature(cur[tag], **{tag: content})
                    else:
                        cv.feature(cur[tag], **{tag: content})
                        cv.meta(
                            tag, description="open tag without further specification. See the name of the .tf-file for it's meaning",)
                    nonIntFeatures.add(tag)
                    continue

                # Activate non-active structs
                if not set(self.structs) <= cv.activeTypes():
                    for struct in self.structs:
                        if struct not in cv.activeTypes():
                            if struct in {'_phrase', '_sentence'}:
                                if struct in cur:
                                    cv.resume(cur[struct])
                                else:
                                    cur[struct] = cv.node(struct)
                                    cv.feature(cur[struct], **
                                               {struct: counter[struct]})
                            else:
                                cur[struct] = cv.node(struct)
                                cv.feature(cur[struct], **{struct: 0})

                # PROCESS TEXT
                for token_out in self.process_text(content):

                    # Handle empty tokens that still have a pre feature, by adding them to the previous post and orig
                    if 'plain' in token_out and token_out['plain'] == '':
                        if 'pre' in token_out and 'post' in token_out:
                            try:  # Check if there is already an existing slot number
                                cv.resume(w)
                                pre = token_out['pre']
                                orig = cv.get('orig', w) + pre
                                cv.feature(w, orig=orig)
                                post = cv.get('post', w) + pre
                                cv.feature(w, post=post)
                                # Check phrase and sentence counters
                                if set(pre) & self.phrase_delimit:
                                    if cv.linked(cur['_phrase']):
                                        cv.terminate(cur['_phrase'])
                                        counter['_phrase'] += 1
                                        cur['_phrase'] = cv.node('_phrase')
                                        cv.feature(
                                            cur['_phrase'], **{'_phrase': counter['_phrase']})
                                if set(pre) & self.sentence_delimit:
                                    for count in ('_phrase', '_sentence'):
                                        if cv.linked(cur[count]):
                                            cv.terminate(cur[count])
                                            counter[count] += 1
                                            cur[count] = cv.node(count)
                                            cv.feature(
                                                cur[count], **{count: counter[count]})
                                cv.terminate(w)
                            except:
                                pass
                        continue

                    # SLOT ASSIGNMENT!
                    # ================

                    w = cv.slot()

                    # Handle the data dictionary with text formats and features
                    for name, value in token_out.items():
                        cv.feature(w, **{name: value})

                    # ================

                    # Check phrase and sentence counters
                    if 'post' in token_out:
                        if set(token_out['post']) & self.phrase_delimit:
                            if cv.linked(cur['_phrase']):
                                cv.terminate(cur['_phrase'])
                                counter['_phrase'] += 1
                                cur['_phrase'] = cv.node('_phrase')
                                cv.feature(cur['_phrase'], **
                                           {'_phrase': counter['_phrase']})
                        if set(token_out['post']) & self.sentence_delimit:
                            for count in ('_phrase', '_sentence'):
                                if cv.linked(cur[count]):
                                    cv.terminate(cur[count])
                                    counter[count] += 1
                                    cur[count] = cv.node(count)
                                    cv.feature(cur[count], **
                                               {count: counter[count]})

                    # Run lemma counter
                    if 'lemma' in token_out:
                        if token_out['lemma'].startswith('*'):
                            lemma_counter[1] += 1
                        else:
                            lemma_counter[0] += 1

            elif code == 'closeTag':
                if tagList[-1] in self.sections:
                    index = self.sections.index(tagList[-1])
                    for ntp in self.sections[:index:-1]:
                        if ntp in cur:
                            if not cv.linked(cur[ntp]):
                                cv.slot()
                            cv.terminate(cur[ntp])
                    if not cv.linked(cur[tagList[-1]]):
                        cv.slot()
                elif tagList[-1] in self.non_text_tags:
                    del tagList[-1]
                    continue
                if tagList[-1] in linked_features_dict:
                    for i in linked_features_dict[tagList[-1]]:
                        cv.terminate(cur[i])
                    del linked_features_dict[tagList[-1]]
                cv.terminate(cur[tagList[-1]])
                del tagList[-1]
                continue

            elif code in {'openAttrTag', 'closedAttrTag'}:
                tag_name, attribs = content
                value_key, name_keys = self.analyzed_dict[tag_name]
                value = attribs[value_key]
                if name_keys == 'tag':
                    name = tag_name[0]
                else:
                    name = '-'.join([attribs[key] for key in name_keys])
                if not value.isdigit():
                    nonIntFeatures.add(name)
                if code == 'openAttrTag':
                    tagList.append(name)
                if name in self.structs:
                    if name in cur and cv.get(name, cur[name]) == 0 and value.isdigit():
                        cv.feature(cur[name], **{name: str(int(value) - 1)})
                    ind = self.structs.index(name)
                    for struct in self.structs[:ind:-1]:
                        if struct in cur:
                            if not cv.linked(cur[struct]) and code == 'closedAttrTag':
                                cv.slot()
                            cv.terminate(cur[struct])
                    if name in cur:
                        if not cv.linked(cur[name]) and code == 'closedAttrTag':
                            cv.slot()
                        cv.terminate(cur[name])
                    for struct in self.structs[:ind]:
                        if not struct in cv.activeTypes():
                            cur[struct] = cv.node(struct)
                            cv.feature(cur[struct], **{struct: 0})
                    cur[name] = cv.node(name)
                    cv.feature(cur[name], **{name: value})
                else:
                    if name in cur and cv.linked(cur[name]):
                        cv.terminate(cur[name])
                        cur[name] = cv.node(name)
                        cv.feature(cur[name], **{name: value})
                    elif name in cur and not cv.linked(cur[name]):
                        pass
                    else:
                        cur[name] = cv.node(name)
                        cv.feature(cur[name], **{name: value})
                        cv.meta(
                            name, description='no feature metadata have been provided; look at the name of the feature and at the data itself to get some clues')
                if set(attribs) & self.feature_attribs:
                    features = tuple(set(attribs) & self.feature_attribs)
                    for f in features:
                        if f in cur:
                            cv.terminate(cur[f])
                        cur[f] = cv.node(f)
                        cv.feature(cur[f], **{f: attribs[f]})
                        cv.meta(
                            f, description='no feature metadata have been provided; look at the name of the feature and at the data itself to get some clues')
                        if not attribs[f].isdigit():
                            nonIntFeatures.add(f)
                        if name in linked_features_dict:
                            linked_features_dict[name].append(f)
                        else:
                            linked_features_dict[name] = [f]
                continue

            elif code == 'openTag':
                tag_name = content
                tagList.append(tag_name)
                if tag_name in self.non_text_tags:
                    nonIntFeatures.add(tag_name)
                    if not tag_name in cur:
                        cur[tag_name] = cv.node(tag_name)
                        cv.feature(cur[tag_name], **{tag_name: ''})
                        cv.meta(
                            tag_name, description="open tag without further specification. See the name of the .tf-file for it's meaning",)
                        continue
                    elif tag_name in cur and cv.linked(cur[tag_name]):
                        cv.terminate(cur[tag_name])
                        cur[tag_name] = cv.node(tag_name)
                        cv.feature(cur[tag_name], **{tag_name: ''})
                        cv.meta(
                            tag_name, description="open tag without further specification. See the name of the .tf-file for it's meaning",)
                        continue
                    else:
                        continue
                else:
                    if tag_name in cur:
                        cv.terminate(cur[tag_name])
                    if tag_name in counter:
                        counter[tag_name] += 1
                    else:
                        counter[tag_name] = 1
                cur[tag_name] = cv.node(tag_name)
                cv.feature(cur[tag_name], **{tag_name: counter[tag_name]})
                cv.meta(
                    tag_name, description="open tag without further specification. See the name of the .tf-file for it's meaning",)
                continue

            elif code == 'openCloseTag':
                #                 tag_name = content[1:-2]
                tag_name = content
                counter[tag_name] = 1 if tag_name not in counter else counter[tag_name] + 1
                if tag_name in cur:
                    cv.terminate(cur[tag_name])
                cur[tag_name] = cv.node(tag_name)
                cv.feature(cur[tag_name], **{tag_name: counter[tag_name]})
                cv.meta(
                    tag_name, description="open-close-tag without further specification. See the name of the .tf-file for it's meaning",)
                continue

            elif code == 'comment':
                continue

            elif code == 'bodyStop':
                for ntp in cur:
                    if not ntp in self.sections and not ntp == '_book':
                        cv.terminate(cur[ntp])
                for ntp in self.sections[::-1]:
                    if not cv.linked(cur[ntp]):
                        cv.slot()
                    cv.terminate(cur[ntp])
                cv.terminate(cur['_book'])
                if tagList:
                    del tagList[-1]
                break

        if not lemma_counter == [0, 0]:
            cv.meta(
                'lemma', **{'coverage_ratio': f'{round(lemma_counter[0] / ((lemma_counter[0] + lemma_counter[1]) / 100 ), 2)}%'})
        cv.meta(
            '_sentence', description=f"sentences defined by the following delimiters: {self.sentence_delimit}",)
        cv.meta(
            '_phrase', description=f"phrases defined by the following delimiters: {self.phrase_delimit}",)
        for feature in cv.metaData:
            if feature in nonIntFeatures:
                cv.meta(feature, valueType='str')
            else:
                if feature == "":
                    pass
                else:
                    cv.meta(feature, valueType='int')

# Final check of tags
#         tm.indent(level=1)
#         if len(tagList) == 0:
#             tm.info('No tag mistake(s) found...')
#         else:
#             tm.info(str(len(tagList)) + ' tag error(s) found.')


# MAIN CONVERT FUNCTION THAT INVOKES ALL THE MACHINERY ABOVE
def convert(
        input_path,
        output_path,
        file_elem='',
        csv_delimiter=',',
        tlg_out=False,
        supply_accents=False,           # Supply accents if absent
        ignore_empty=True,              # Ignore files that don't produce slots
        generic=generic_metadata,       # Generic metadata from tf_config
        lang='generic',                 # Chosen language as available in langsettings in tf_config
        # Used to introduce subclases of a language; e.g. 'tlge' in addition to 'greek'
        typ=False,
        # If True: first line of csv would be taken as header. Also tuple and list are allowed
        header=False,
        version='1.0',                  # Version number to be added in the metadata of every tf-file
        langsettings=langsettings,      # Reference to langsettings
        multiprocessing=False,          # Can be used if many files need to be converted. If 'True', the program checks number of available cores authomatically; if int, it will try to use that number of cores
        # Defines the number of files to be send to each core in multiprocessing mode
        chunksize=1,
        silent=False,                   # Keeps TF messages silent
):
    '''The convert function is the core of the tei2tf module

    It takes the following arguments:
    in_path:  the path that contains the TEI formatted texts
    out_path: the path to which the tf-files would be written
    **kwargs: a dictionary that is usually derived from the
              config.py file, that contains all important
              parameters for the conversion (see documentation)
    '''
    tm = Timestamp()
    kwargs = langsettings[lang]
    dir_struct = kwargs['dir_struct']
#    sLemmatizer  = kwargs['lemmatizer']()
    count1 = 0     # counts the number input files
    count2 = 0     # counts the number of successfully processed files

    # Add parameters to kwargs
    kwargs['ignore_empty'] = ignore_empty
    kwargs['generic'] = generic
    kwargs['lang'] = lang
    kwargs['typ'] = typ
    kwargs['header'] = header
    kwargs['version'] = version

    if kwargs['lang'] == 'greek':
        kwargs['lemmatizer'] = langsettings['greek']['slemmatizer']()

    # input-output file management
    if input_path.startswith('~'):
        inpath = path.expanduser(input_path)
    else:
        inpath = input_path
    if output_path.startswith('~'):
        outpath = path.expanduser(output_path)
    else:
        outpath = output_path

    # Necessary to make process_file picklable for multiprocessing
    global process_file

    def process_file(file):
        nonlocal count1
        nonlocal count2
        nonlocal header
#         nonlocal silent
        if file.endswith('.csv') or file.endswith('.tsv'):
            count1 += 1
            tm.info(f'parsing {file}')
            filename = path.splitext(file)[0].split('/')[-1]

            # Create csv-object that tests for header and dialect
            sniffer = csv.Sniffer()
            with open(file, newline='') as csvfile:
                test_piece = csvfile.read(1024)
                # Reset the cursor at starting position after read()
                csvfile.seek(0)
                # Define dialect
                dialect = sniffer.sniff(test_piece)
                # Automatically define the presence of a header, if header == None
                if header == None:
                    header = sniffer.has_header(test_piece)
                data = csv.reader(csvfile, dialect, delimiter=csv_delimiter)
                first_line = next(data)
                csvfile.seek(0)

                # Inject metadata
                metadata = tlge_metadata[filename]
                kwargs['generic'].update(tlge_metadata[filename])
                
                # Add original filename to metadata
                kwargs['generic']['filename'] = filename
                if not 'title' in kwargs['generic']:
                    kwargs['generic']['title'] = filename.rsplit('.', 1)[0]

                if tlg_out == True:
                    dirs = kwargs['generic']['key'].split(' ')
                # definition of output dir structure on the basis of metadata
                else:
                    dirs = []
                    for i in dir_struct:
                        assigned = False
                        for j in i:
                            if j in metadata:
                                dirs.append(metadata[j])
                                assigned = True
                                break
                        if assigned == False:
                            dirs.append(f'unknown {"-".join(i)}')

                # dirs is a list of lists of which the tagnames used are defined in config.py
                # they usually correspond to something like (author, work, editor/edition)
                # in case of multiple editions of the same work, a number will be prefixed
                C = 1
                if path.isdir(f'{outpath}/{"/".join(dirs)}/{C}/tf/{version}'):
                    # Pass if dir already exists --> temporary solution!!!
                    return False

                    while path.isdir(f'{outpath}/{"/".join(dirs)}/{C}/tf/{version}'):
                        C += 1
                    else:
                        TF_PATH = f'{outpath}/{"/".join(dirs)}/{C}/tf/{version}'
                else:
                    TF_PATH = f'{outpath}/{"/".join(dirs)}/{C}/tf/{version}'

                # setting up the text-fabric engine
                TF = Fabric(locations=TF_PATH, silent=silent)
                cv = CV(TF, silent=silent)
                # initiating the Conversion class that provides all
                # necessary data and methods for cv.walk()
                x = Csv2tf(data, first_line=first_line, **kwargs)
                # running cv.walk() to generate the tf-files
                good = cv.walk(
                    x.director,
                    slotType=x.slot_type,
                    otext=x.otext,
                    generic=x.generic,
                    intFeatures=x.intFeatures,
                    featureMeta=x.featureMeta,
                    warn=True,
                )
                # Count number of successfully converted files
                if good:
                    count2 += 1
                    tm.info('   |    Conversion was successful...\n')
                else:
                    tm.info(
                        '   |    Unfortunately, conversion was not successful...')
                    if ignore_empty == True:
                        tm.info(
                            '   |    The most probable reason is that no slot numbers could be assigned...\n')

        elif file.endswith('.xml'):
            count1 += 1
#             if count1 > 1: print('\n')
            tm.info(f'parsing {file}')

            # creation of data to extract metadata
            # and to inject later into the Conversion object
            data = dataParser(xmlSplitter(file), lang=lang)
            body_index, metadata = metadataReader(
                data, **kwargs['xmlmetadata'])
            if not body_index:
                return False
            kwargs['generic'].update(metadata)
            # Add filename
            filename = path.splitext(file)[0].split('/')[-1]
            kwargs['generic']['filename'] = filename

            # definition of output dir structure on the basis of metadata or tlg-out
            if tlg_out == True:
                dirs = file.split('/')[-1].split('.')[:3]
            else:
                dirs = []
                for i in dir_struct:
                    assigned = False
                    for j in i:
                        if j in metadata:
                            dirs.append(metadata[j])
                            assigned = True
                            break
                    if assigned == False:
                        dirs.append(f'unknown {"-".join(i)}')

            # dirs is a list of lists of which the tagnames used are defined in config.py
            # they usually correspond to something like (author, work, editor/edition)
            # in case of multiple editions of the same work, a number will be prefixed
            C = 1
            if path.isdir(f'{outpath}/{"/".join(dirs)}/{C}/tf/{version}'):
                while path.isdir(f'{outpath}/{"/".join(dirs)}/{C}/tf/{version}'):
                    C += 1
                else:
                    TF_PATH = f'{outpath}/{"/".join(dirs)}/{C}/tf/{version}'
            else:
                TF_PATH = f'{outpath}/{"/".join(dirs)}/{C}/tf/{version}'

            # setting up the text-fabric engine
            TF = Fabric(locations=TF_PATH, silent=silent)
            cv = CV(TF, silent=silent)
            # initiating the Conversion class that provides all
            # necessary data and methods for cv.walk()
            x = Xml2tf(data[body_index:], **kwargs)
            # running cv.walk() to generate the tf-files
            good = cv.walk(
                x.director,
                slotType=x.slot_type,
                otext=x.otext,
                generic=x.generic,
                intFeatures=x.intFeatures,
                featureMeta=x.featureMeta,
                warn=True,
            )
            # Count number of successfully converted files
            if good:
                count2 += 1
                tm.info(
                    f'   |    Conversion of {file.split("/")[-1]} was successful...!\n')
            else:
                tm.info(
                    f'   |    Unfortunately, conversion of {file.split("/")[-1]} was not successful...\n')

    # Define list of files to be processed
    file_list = glob(f'{inpath}/**/*{file_elem}*.*', recursive=True)
    # print(file_list)

    if multiprocessing:
        if not type(multiprocessing) == bool:
            # Manual assignment of cores
            pool = Pool(processes=multiprocessing)
        else:
            pool = Pool()
        # Manual assignment of chunksize if many files need to be consumed
        # Manual assignment might improve performance
        pool.imap_unordered(process_file, file_list, chunksize=chunksize)
    #     pool.imap_unordered(process_file, file_list)
        pool.close()
        pool.join()

    else:
        for file in file_list:
            process_file(file)

    tm.info(f'{count2} of {count1} works have successfully been converted!')
