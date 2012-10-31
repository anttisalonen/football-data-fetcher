import sys
import urllib2
import re

from lxml import etree

from settings import Globals

removeAngleBrackets_re = re.compile(r'\<[^>]*\>')

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

def stripFormatting(s):
    s2 = s.split('[[')
    if len(s2) > 1:
        s2 = s2[-1]
        s2 = s2.split(']]')
        if len(s2) > 1:
            return '[[' + s2[0] + ']]'
    return s

def unlinkify(origstr):
    s = stripFormatting(origstr)
    if s.startswith('[[') and s.endswith(']]'):
        s = s[2:][:-2]
        if '|' in s:
            ln = s.split('|')
            if len(ln) >= 2:
                return (ln[-1].strip(), ln[0].strip())
            else:
                return (s, None)
        else:
            return (s.strip(), s.strip())
    else:
        return (s, None)

def getKeyValue(line):
    try:
        vals = [s.strip() for s in line.split('=')]
        return vals[0], vals[1]
    except:
        print >> Globals.errlog, 'Error getting key-value pair from "%s"' % line
        raise

def getHeading(line):
    s = line.strip()
    if not s.startswith('==') or not s.endswith('=='):
        return None
    s = s.strip('==')
    s = s.strip()
    return s

def getPage(title, expandTemplates = False):
    title = title.replace(' ', '_')

    s = u'http://en.wikipedia.org/w/api.php?format=xml&action=query&titles=%s&prop=revisions&rvprop=content&redirects=1' % title
    if expandTemplates:
        s += '&rvexpandtemplates=1'
    sys.stdout.write('Processing %s... ' % title)
    sys.stdout.flush()
    infile = opener.open(urllib2.quote(s.encode('utf-8'), ':/&=?'))
    page = infile.read()

    pagexml = etree.XML(page)
    try:
        rvtext = pagexml.xpath('/api/query/pages/page/revisions/rev/text()')[0]
    except IndexError:
        print >> Globals.errlog, "Couldn't find wikitext for", title.encode('utf-8')
        return None

    if Globals.dumpTextFiles:
        with open(Globals.outputdir + titleToFilename(title) + '.txt', 'w') as f:
            f.write(rvtext.encode('utf-8'))

    return rvtext

def expandTemplate(text):
    s = u'http://en.wikipedia.org/w/api.php?action=expandtemplates&format=xml&text=%s' % text
    s2 = urllib2.quote(s.encode('utf-8'), ':/&=?')
    infile = opener.open(s2)
    page = infile.read()

    pagexml = etree.XML(page)
    try:
        text = pagexml.xpath('/api/expandtemplates/text()')[0]
        return text
    except IndexError:
        print >> Globals.errlog, "Couldn't expand template", title
        return None

def titleToFilename(title):
    return title.replace(' ', '_').replace('.', '').replace('/', '_')

def getNumberKeyValue(line):
    k, v = getKeyValue(removeAngleBrackets_re.sub('', line))
    name, link = unlinkify(v)
    pos = re.findall(r'\d+', name)
    if len(pos) >= 1:
        return int(pos[0])
    else:
        return None

def getTemplate(text):
    l = text.strip()
    if l.startswith('{{') and l.endswith('}}'):
        l = l.strip('{{').strip('}}')
        if '|' in l:
            return l.split('|')[0]
    else:
        return None


