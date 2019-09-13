import re
import operator
from pprint import pprint
from collections import OrderedDict
from data.attrib_errors import error_dict
from ordered_set import OrderedSet

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


def attribClean(elem, lang='generic', **kwargs):
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
    # clean the elem
    elem = elem.strip('<>\/ ')
    elem = re.sub(r'\s*=\s*"\s*', '="', elem)
    # define the tag
    tag = elem[:elem.find(' ')]
    # convert the attributes to a dict
    attribs = {k.strip(): v.strip('" ') for k, v in [elem.split('="') \
        for elem in elem[elem.find(' '):].split('" ')]}
    # correct any mistakes in the attributes 
    # if 'attrib_errors' is provided in the config.py
    if lang in kwargs:
        attribs = {k: (kwargs[lang][v] \
                           if v in kwargs[lang] \
                           else v) \
                       for k, v in attribs.items()}
    return tag, attribs


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
    # Application of patterns:
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
            content = attribClean(elem, lang=lang, **error_dict)
        elif closedAttrTagRE.fullmatch(elem):
            code = 'closedAttrTag'
            content = attribClean(elem, lang=lang, **error_dict)
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
#         print(code, content)
        if code == 'bodyStart':
            body_index = data.index(elem) + 1
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
                content = content[0]
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
    section_tags = OrderedSet()
    open_section_tags = set()
    
    for elem in data:
        code, content = elemParser(elem, lang=lang, **error_dict)
        if code in ('openAttrTag', 'closedAttrTag'):
            tag, attribs = content
            # The 'startswith' statement is there, because some XML files use 
            # e.g. div1, div2, div3 as structuring tags.
            # In this case, kwargs['structure_tag'] = 'div'
            for sec_tag in kwargs['section_tags']:
                if tag.startswith(sec_tag):
                    if kwargs['non_section_keys'] & set(attribs):
                        tag_name = tuple((tag, tuple(key for key in attribs.keys() \
                                          if key not in kwargs['ignore_attrib_keys'])))
                        break
                    tag = sec_tag
                    tag_name = tuple((tag, tuple(key for key in attribs.keys() \
                                      if key not in kwargs['ignore_attrib_keys'])))
                    section_tags.add(tag_name)
                    break
            else:        
                tag_name = tuple((tag, tuple(key for key in attribs.keys() \
                                  if key not in kwargs['ignore_attrib_keys'])))
            if tag_name in attribs_dict:
                for attrib in attribs:
                    if attrib in attribs_dict[tag_name]:
                        attribs_dict[tag_name][attrib].add(attribs[attrib])
                    else:
                        attribs_dict[tag_name][attrib] = OrderedSet([attribs[attrib]])
            else:
                attribs_dict[tag_name] = {k: OrderedSet([v]) for k, v in attribs.items()}
            if code == 'openAttrTag' and tag_name in section_tags:
                open_section_tags.add(tag_name)
        else:
            continue
#     pprint(attribs_dict)
#     pprint(section_tags)
#     pprint(open_section_tags)
    return attribs_dict, section_tags, open_section_tags
    
                                  
def lenAttribsDict(dictionary):
    """lenAttribsDict measures the length of the values in 
    attribs_dict returned by attribsDict()"""
    return {key: {k: len(v) for k, v in val.items()} for key, val in dictionary.items()}
                              
                                  
def sectionElems(attribs_dict, section_labels, **kwargs):
    """takes the attribs_dict, and section_tags
    returned by attribsAnalysis() as input and returns the
    sections that most probably define the structure of the XML.
    """
#     print(attribs_dict)
    print(section_labels)
    section_dict = {}
    sections = []
    for tag_name in section_labels:
        tag, keys = tag_name
        if len(keys) == 1:
            section_dict[tag_name] = (tag, keys[0])
            sections.add(tag)
        else:
            if 'n' in attribs_dict[tag_name]:
                section_key = max(attribs_dict[tag_name], 
                                  key=lambda key: attribs_dict[tag_name][key] \
                                  if not key == 'n' 
                                  and not key in kwargs['non_section_keys']
                                  else OrderedSet())
                section_dict[tag_name] = (section_key, 'n')
            else:
                value = max(attribs_dict[tag_name], 
                            key=lambda key: attribs_dict[tag_name][key])
                section_key = max(attribs_dict[tag_name], 
                                  key=lambda key: attribs_dict[tag_name][key] \
                                  if not section_key == value 
                                  and not section_key in kwargs['non_section_keys']
                                  else OrderedSet())
                section_dict[tag_name] = (section_key, value)
#             print(section_dict)

            sections.extend(list(i for i in attribs_dict[tag_name][section_key]))
    print(sections)
#     sections = list(sections)
#     print(sections)
    return section_dict, sections
                
