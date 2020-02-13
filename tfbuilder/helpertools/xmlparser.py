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
xmlMetaRE       = re.compile(r'<\?.+\?>')


def xmlSplitter(xmlfile):
    '''The xmlReader reads a XML file completely into memory,
    while splitting the text on "<" and ">" into a list.
    '''        
    with open(xmlfile) as xml:
        data = ''.join([(line.strip() + ' ' if not line.strip().endswith('-') else line.strip()) \
                        for line in xml.readlines()])\
                 .replace('<', '#!#<')\
                 .replace('>', '>#!#')\
                 .split('#!#')
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
#     print(elem)
    elem = elem.strip('<>\/ ')
    elem = re.sub(r'\s*=\s*"\s*', '="', elem)
    tag = ''.join([c for c in elem[:elem.find(' ')] if not c.isdigit()])
    
    try:
        attribs = {k.strip(): v.strip('" ') for k, v in [elem.split('="') \
                          for elem in elem[elem.find(' '):].split('" ')]}
    except ValueError:
        elem = elem.replace("'", '"')
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


def dataParser(data, lang='generic'):
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
    parsed_data = []
    comment     = False
    
    for elem in data:
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
            elif xmlMetaRE.fullmatch(elem):
                code, content = 'comment', ''
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
            elif elem.strip() == '':
                code, content = None, elem
            else:
                code, content = 'text', elem
        parsed_data.append((code, content))
    return parsed_data
        
    
def metadataReader(data, lang='generic', **kwargs):
    """The **kwargs are the 'metadata' field in tf_config.py
    the **kwargs passed should be langsettings[lang]['xmlmetadata'] from tf_config.py
    
    data should be produced by dataParser
    """
    metadata   = {}
    body_index = False
    READ       = False
    CONC       = None
    CUR        = None
    TEMP       = [None, None]
    DELIM      = ''
    tagList    = []
    for code, content in data:
        if code == 'bodyStart':
            body_index = data.index((code, content)) + 1
            break
        elif code == 'text':
            content = content.strip('. ')
            if tagList and tagList[-1] in {'author', 'editor'}:
                content = ' '.join((c.title() if not c.lower() in {'of', 'the',} else c.lower()) \
                                    for c in content.split())
            else:
                content = content.strip()
            if READ:
                if tagList[-1] in metadata:
                    metadata[tagList[-1]] += f'{DELIM}{content}'
                else:
                    metadata[tagList[-1]] = content
        elif code in ('openTag', 'openAttrTag'):
            if code == 'openAttrTag':
                content = content[0][0]
            if content in kwargs:
                READ = True
                CONC = kwargs[content]['concat']
                DELIM = kwargs[content]['delimit']
                CUR = content
                tagList.append(CUR)
                continue
            if CONC == False:
                tagList.append(content)
            if content.endswith('Stmt'): 
                TEMP[0] = content
                TEMP[1] = CONC
                CONC = True
        elif code == 'closeTag':
            if tagList and content == tagList[-1]:
                if content == TEMP[0]:
                    CONC = TEMP[1]
                    TEMP = [None, None]
                del tagList[-1]
                if content == CUR:
                    READ = False
        else:
            continue
    for i in kwargs:
        if 'end' in kwargs[i] and i in metadata:
            if not metadata[i][-1] == kwargs[i]['end']:
                metadata[i] += kwargs[i]['end']
    
    return body_index, metadata
            

def attribsAnalysis(data, **kwargs):
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
#     pprint(attribs_dict)
    for tag_name, attribs in attribs_dict.items():
        #define value keys and feature keys
        if len(attribs) == 1:
            analyzed_dict[tag_name] = tuple((''.join(attribs.keys()), 'tag'),)
        elif len(attribs) >= 2:
            keyFound = False
            if 'n' in attribs:
                value = 'n'
            else:
                value = max(attribs, key=lambda key: len(attribs[key]) \
                               if not key in kwargs['ignore_attrib_keys'] else False)
            if set(attribs) & kwargs['section_keys']:
                feature_names = list((set(attribs) & kwargs['section_keys']),)
                keyFound = True
            else:
                feature_names = list((max(attribs, key=lambda key: len(attribs[key]) \
                               if not key == value \
                               and not key in kwargs['ignore_attrib_keys'] else False),))
            if not keyFound:
#                 print(f'attribs = {attribs}')
#                 print(f'feature_names = {feature_names} ')
                for k in attribs:
                    for key in feature_names:
                        if not k in (feature_names + list(value)):
                            if len(attribs[k]) == len(attribs[key]) \
                            and not k in kwargs['ignore_attrib_keys']:
                                feature_names.append(k)
            analyzed_dict[tag_name] = tuple((value, tuple(feature_names)),)
            
        #define sections
        value, feature_keys = analyzed_dict[tag_name]
        if tag_name[0] in kwargs['section_tags']:
            if feature_keys == 'tag':
                continue
            section_keys = set(feature_keys) \
                               - {k for k, v in attribs_dict[tag_name].items() if v & kwargs['non_section_values'] } \
                               - kwargs['non_section_keys'] \
                               - kwargs['ignore_attrib_keys']
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
                continue
               
    return analyzed_dict, sections
