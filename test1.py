import urllib2
from lxml import etree
import re
import sys

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

teams = ['Manchester United', 'Barcelona FC', 'Bayern Munich', 'East Fife F.C.', 'SV_Waldhof_Mannheim']

class Player:
    def __init__(self, name, number, pos, nationality):
        self.name = name
        self.number = number
        self.pos = pos
        self.nationality = nationality

def unlinkify(s):
    if s.startswith('[[') and s.endswith(']]'):
        s = s[2:][:-2]
        if '|' in s:
            return s.split('|')[1].strip()
        else:
            return s
    else:
        return s

teamdata = []

for t in teams:
    s = 'http://en.wikipedia.org/w/api.php?format=xml&action=query&titles=%s&prop=revisions&rvprop=content&redirects=1' % t.replace(' ', '_')
    print 'Processing %s...' % t
    infile = opener.open(s)
    page = infile.read()
    filebasename = t.replace(' ', '_').replace('.', '')
    filename = '%s.%s' % (t.replace(' ', '_').replace('.', ''), 'xml')
    with open(filebasename + '.xml', 'w') as f:
        f.write(page)

    pagexml = etree.XML(page)
    try:
        rvtext = pagexml.xpath('/api/query/pages/page/revisions/rev/text()')[0]
    except IndexError:
        print >> sys.stderr, "Couldn't find wikitext for team", t
        continue

    players = []

    unlinker_re = re.compile(r'(.*)\[\[(.*)\|(.*)\]\](.*)')

    for line in rvtext.split('\n'):
        if '{{fs player' in line.lower() and line.strip()[-2:] == '}}':
            unlinkedline = line
            while True:
                res = unlinker_re.match(unlinkedline)
                if res:
                    groups = res.groups()
                    try:
                        unlinkedline = groups[0] + groups[2] + groups[3]
                    except IndexError:
                        print >> sys.stderr, "Couldn't find groups at", groups
                        break
                else:
                    break

            columns = [s.strip() for s in unlinkedline.replace('{', '').replace('}', '').split('|')]
            number = None
            nationality = None
            pos = None
            name = None
            for column in columns:
                if '=' in column:
                    try:
                        [k, v] = [s.strip() for s in column.split('=')]
                    except ValueError:
                        print >> sys.stderr, 'Could not parse column:', column
                        continue
                    if k == 'no':
                        try:
                            number = int(v)
                        except (UnicodeEncodeError, ValueError):
                            print >> sys.stderr, 'Unknown number', v
                    elif k == 'nat':
                        nationality = v
                    elif k == 'pos':
                        pos = v
                    elif k == 'name':
                        name = unlinkify(v)
            if number and nationality and pos and name:
                player = Player(name, number, pos, nationality)
                players.append(player)

    teamdata.append((t, players))

root = etree.Element("root")

for teamname, playerlist in teamdata:
    if playerlist:
        teamelem = etree.SubElement(root, 'Team')
        teamelem.set('name', teamname)
        for p in playerlist:
            playerelem = etree.SubElement(teamelem, 'Player')
            playerelem.set('name', p.name)
            playerelem.set('number', str(p.number))
            playerelem.set('pos', p.pos)
            playerelem.set('nationality', p.nationality)

with open('output.xml', 'w') as f:
    f.write(etree.tostring(root, pretty_print=True))
