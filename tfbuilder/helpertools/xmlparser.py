import re
import operator
from pprint import pprint
from collections import OrderedDict
from data.attrib_errors import error_dict
from ordered_set import OrderedSet
from tf_config import langsettings

# XML RE PATTERNS
commentFullRE   = re.compile(r'^<!--.*?-->$')
commentStartRE  = re.compile(r'^<!--.*')
commentStopRE   = re.compile(r'.*-->$')
openTagRE       = re.compile(r'<[^/=]+?>')
closeTagRE      = re.compile(r'</.+?>')
opencloseTagRE  = re.compile(r'<[^/=]+?/ *?>')
openAttrTagRE   = re.compile(r'<.+?=.+?[^/] *?>')
closedAttrTagRE = re.compile(r'<.+?=.+?/ *?>')
bodyStartRE     = re.compile(r'<body *.*?>')
bodyStopRE      = re.compile(r'</body *.*?>')


def xmlSplitter(xmlfile):
    '''The xmlReader reads a XML file completely into memory,
    while splitting the text on "<" and ">" into a list.
    '''
    def clean(elem):
        """Deletes empty list elements"""
        if elem.strip() == '':
            return False
        else:
            return True
        
    with open(xmlfile) as xml:
        # the filter function ensures that no empty strings are returned
        data = list(filter(clean, 
                  ' '.join([line.strip() for line in xml.readlines()])\
                  .replace('- ', '-')\
                  .replace('<', '#!#<')\
                  .replace('>', '>#!#')\
                  .split('#!#')))
    return data


def attribClean(elem, errors, lang='generic', **kwargs):
    '''attribClean reads an XML tag and processes a 
    thorough normalization on it, consisting of:
    - strip() of whitespace
    - normalization of elements with attributes into:
        <name attrib1="attribname1" attrib2="attribname2">
    - correction of mistakes defined in kwargs['attrib_errors']
      kwargs is usually defined in config.py.
      
    The function returns a tuple with tag and attribs dict:
    (tag, {keys: values})
    '''
    elem = elem.strip('<>\/ ')
    elem = re.sub(r'\s*=\s*"\s*', '="', elem)
    tag = elem[:elem.find(' ')]
    attribs = {k.strip(): v.strip('" ') for k, v in [elem.split('="') \
                      for elem in elem[elem.find(' '):].split('" ')]}
    if lang in errors:
        attribs = {k: (errors[lang][v] \
                       if v in errors[lang] else v) \
                       for k, v in attribs.items()}
#     attribs = {k: v for k, v in attribs.items() \
#                     if not k in kwargs[lang]['ignore_attrib_keys']}
    tag_name = (tag, tuple(key for key in attribs.keys() if not key in kwargs[lang]['ignore_attrib_keys']))
    return tag_name, attribs


def elemParser(elem, lang='generic'):
    '''The xmlParser is able to parse the elements
    created by xmlSplitter(xmlfile). It returns a tuple
    containing the type and normalized element: (type, elem)
    
    Normalization of element involves:
    - strip() of whitespace
    - normalization of elements with attributes into:
        <name attrib1="attribname1" attrib2="attribname2 etc="etc">
    - correction of mistakes in attributes defined in kwargs[lang]
      (see attribClean)
    ''' 
    comment = False
    if comment:
        if commentStopRE.fullmatch(elem):
            comment = False
        code, content = 'comment', ''
    else:
        if commentFullRE.fullmatch(elem):
            code, content = 'comment', ''
        elif commentStartRE.fullmatch(elem):
            comment = True
            code, content = 'comment', ''
        elif bodyStartRE.fullmatch(elem):
            code, content = 'bodyStart', ''
        elif bodyStopRE.fullmatch(elem):
            code, content = 'bodyStop', ''
        elif openTagRE.fullmatch(elem):
            code, content = 'openTag', elem.strip('<> ')
        elif closeTagRE.fullmatch(elem):
            code, content = 'closeTag', elem.strip('<>/ ')
        elif opencloseTagRE.fullmatch(elem):
            code, content = 'openCloseTag', elem.strip('<>/ ')
        elif openAttrTagRE.fullmatch(elem):
            code = 'openAttrTag'
            content = attribClean(elem, error_dict, lang=lang, **langsettings)
        elif closedAttrTagRE.fullmatch(elem):
            code = 'closedAttrTag'
            content = attribClean(elem, error_dict, lang=lang, **langsettings)
        else:
            code, content = 'text', elem
    return code, content


def dataParser(data, lang='generic'):
    return [elemParser(elem, lang=lang) for elem in data]
        
    
def metadataReader(data, lang='generic', **kwargs):
    """The **kwargs are the 'metadata' field in tf_config.py
    the **kwargs passed should be langsettings[lang]['metadata'] from tf_config.py
    
    data should be produced by dataParser
    """
    metadata = {}
    READ = False
    CONC = None
    CUR  = None
    tagList = []
    for code, content in data:
        if code == 'bodyStart':
            body_index = data.index((code, content)) + 1
            break
        elif code == 'text':
            if READ:
                if CONC:
                    if CUR in metadata:
                        metadata[CUR] += kwargs[CUR]['delimit'] + content
                    else:
                        metadata[CUR] = content
                else:
                    metadata[tagList[-1]] = content
        elif code in ('openTag', 'openAttrTag'):
            if code == 'openAttrTag':
                content = content[0][0]
            if CUR:
                if not CONC:
                    tagList.append(content)
            if content in kwargs:
                READ = True
                CONC = kwargs[content]['concat']
                CUR = content
                if CONC == False:
                    tagList.append(content)
        elif code == 'closeTag':
            if tagList and content == tagList[-1]:
                del tagList[-1]
            if content in kwargs:
                READ = False
                CONC = None
                CUR = None 
        else:
            continue
    for i in kwargs:
        if 'end' in kwargs[i] and i in metadata:
            if not metadata[i][-1] == kwargs[i]['end']:
                metadata[i] += kwargs[i]['end']
    return body_index, metadata
            

def attribsAnalysis(data, lang='generic', **kwargs):
    attribs_dict = {}
    analyzed_dict = {}
    sections = []
    for code, content in ((c, _) for (c, _) in data if c in ('openAttrTag', 'closedAttrTag')):
        tag_name, attribs = content
        if tag_name in attribs_dict:
            attribs_dict[tag_name] = {k: v | {attribs[k]} if k in attribs else {'',} \
                                      for k, v in attribs_dict[tag_name].items()}                         
        else:
            attribs_dict[tag_name] = {key: OrderedSet([val]) for key, val in attribs.items()}
#     len_attribs_dict = {key: {k: len(v) for k, v in val.items()} for key, val in attribs_dict.items()}
    
#     for tag_name, attribs in len_attribs_dict.items():
    for tag_name, attribs in attribs_dict.items():
        #define value keys and feature keys
        if len(attribs) == 1:
            analyzed_dict[tag_name] = tuple((''.join(attribs.keys()), 'tag'),)
        elif len(attribs) >= 2:
            if 'n' in attribs:
                value = 'n'
            else:
                value = max(attribs, key=attribs.get)
            feature_name = max(attribs, key=lambda key: len(attribs[key]) \
                               if not key == value \
                               or key in kwargs['ignore_attrib_keys'] else False)
            feature_names = [feature_name]
            for k in attribs:
                if not k in (value, feature_name):
                    if len(attribs[k]) == len(attribs[feature_name]) \
                    and not k in kwargs['ignore_attrib_keys']:
                        feature_names.append(k)
            analyzed_dict[tag_name] = tuple((value, tuple(feature_names)),)
            
        #define sections
        if tag_name[0].startswith((tuple(kwargs['section_tags']))):
            section_keys = set(analyzed_dict[tag_name][1]) - kwargs['non_section_keys']
            if len(section_keys) == 0:
                pass
            
            elif len(section_keys) == 1:
                if set(attribs[''.join(section_keys)]) & kwargs['non_section_values']:
                    pass
                else:
                    if not 'n' in attribs:
                        pass
                    else:
                        sections.extend(list(attribs[''.join(section_keys)]))
                        orig_analyzed = analyzed_dict[tag_name]
                        analyzed_dict[tag_name] = tuple((orig_analyzed[0], tuple(section_keys)),)
            else:
                print('ERROR!')
                print(section_keys)
            
#             print(section_keys)
#             if len(section_keys) == 1:
#                 sections.extend(list(attribs_dict[tag_name][''.join(section_keys)] \
#                                      if not attribs_dict[tag_name][''.join(feature_name)] & \
#                                      kwargs['non_section_values'] else ''))
#             else:
#                 print('ERRORR')
                
    return analyzed_dict, sections
    
                                  
# def lenAttribsDict(dictionary):
#     """lenAttribsDict measures the length of the values in 
#     attribs_dict returned by attribsDict()"""
#     return {key: {k: len(v) for k, v in val.items()} for key, val in dictionary.items()}
                              
                                  
# def sectionElems(attribs_dict, section_labels, **kwargs):
#     """takes the attribs_dict, and section_tags
#     returned by attribsAnalysis() as input and returns the
#     sections that most probably define the structure of the XML.
#     """
#     section_dict = {}
#     sections = []
#     for tag_name in section_labels:
#         tag, keys = tag_name
#         if len(keys) == 1:
#             section_dict[tag_name] = (tag, keys[0])
#             sections.add(tag)
#         else:
#             if 'n' in attribs_dict[tag_name]:
#                 section_key = max(attribs_dict[tag_name], 
#                                   key=lambda key: attribs_dict[tag_name][key] \
#                                   if not key == 'n' 
#                                   and not key in kwargs['non_section_keys']
#                                   else OrderedSet())
#                 section_dict[tag_name] = (section_key, 'n')
#             else:
#                 value = max(attribs_dict[tag_name], 
#                             key=lambda key: attribs_dict[tag_name][key])
#                 section_key = max(attribs_dict[tag_name], 
#                                   key=lambda key: attribs_dict[tag_name][key] \
#                                   if not section_key == value 
#                                   and not section_key in kwargs['non_section_keys']
#                                   else OrderedSet())
#                 section_dict[tag_name] = (section_key, value)
#             sections.extend(list(i for i in attribs_dict[tag_name][section_key]))
#     return section_dict, sections
                
