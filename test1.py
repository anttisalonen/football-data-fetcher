#!/usr/bin/env python2
# coding: utf-8

import urllib2
from lxml import etree
import re
import sys
import os, errno

unlinker_re = re.compile(r'(.*)\[\[(.*)\|(.*)\]\](.*)')
attributeAtStart_re = re.compile(r'[\w\s]*\|(.*)', re.UNICODE)
table_re = re.compile(r' *\{\| *class *= *"?wikitable"?.*')
kitinfo_re = re.compile(r'\| *(body|shorts|socks|pattern_b)([12]) *= *([0-9a-fA-F]*)')

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

class Team:
    def __init__(self, name, link):
        self.name = name
        self.link = link


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
            [a, b] = s.split('|')
            return (b.strip(), a.strip())
        else:
            return (s.strip(), s.strip())
    else:
        return (s, None)

def getKeyValue(line):
    [k, v] = [s.strip() for s in line.split('=')]
    return k, v

def getColorValue(string):
    if len(string) != 6:
        return Color()
    r = string[0:2]
    g = string[2:4]
    b = string[4:6]
    return Color(int(r, 16), int(g, 16), int(b, 16))

class Color:
    def __init__(self, r = 0, g = 0, b = 0):
        self.r = r
        self.g = g
        self.b = b

    def __str__(self):
        return '(%d, %d, %d)' % (self.r, self.g, self.b)

class Player:
    def __init__(self, name, number, pos, nationality):
        self.name = name
        self.number = number
        self.pos = pos
        self.nationality = nationality

class KitType:
    Plain = 0
    Stripes = 1
    Vertical = 2
    Hoops = 3
    Horizontal = 4
    Half = 5
    Sash = 6

class Kit:
    def __init__(self):
        self.bodytype = KitType.Plain
        self.bodycolor = Color()
        self.bodycolor2 = Color()
        self.shortscolor = Color()
        self.sockscolor = Color()

def addColorElement(parent, name, color):
    elem = etree.SubElement(parent, name)
    elem.set('r', str(color.r))
    elem.set('g', str(color.g))
    elem.set('b', str(color.b))

def fetchTeamData(team):
    rvtext = getPage(team)
    if not rvtext:
        return

    players = []
    teamposition = None
    kit = [Kit(), Kit()]
    finishedReadingPlayers = False

    for line in rvtext.split('\n'):
        if not finishedReadingPlayers and \
            (('{{fs player' in line.lower() or '{{football squad player' in line.lower()) and line.strip()[-2:] == '}}'):
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
                        k, v = getKeyValue(column)
                    except ValueError:
                        print >> sys.stderr, 'Could not parse column:', column
                        continue
                    if k == 'no':
                        try:
                            number = int(v)
                        except (UnicodeEncodeError, ValueError):
                            print >> sys.stderr, 'Unknown number'
                    elif k == 'nat':
                        nationality = v
                    elif k == 'pos':
                        pos = v
                    elif k == 'name':
                        name = unlinkify(v)[0]

            if number and nationality and pos and name:
                player = Player(name, number, pos, nationality)
                players.append(player)

        if '{{fs end}}' in line.lower() or '{[football squad end}}' in line.lower() or '{{football squad end2}}' in line.lower():
            # end of player list
            finishedReadingPlayers = True

        lineWithoutSpaces = ''.join(line.split())
        if lineWithoutSpaces.startswith("|position="):
            # this seems to usually be either this or last season's position
            # it's a bit problematic when a team was promoted or relegated, but...
            k, v = getKeyValue(line)
            pos = re.findall(r'\d+', v)
            if len(pos) == 1:
                teamposition = int(pos[0])

        kitresults = kitinfo_re.findall(line)
        for kitresult in kitresults:
            columns = [x.strip() for x in line.split('|') if 'body' in x]
            for c in columns:
                k, v = getKeyValue(c)
                if k.startswith('body'):
                    k = k[4:]
                    n = int(k[0]) - 1
                    kit[n].bodycolor = getColorValue(v)
                if k.startswith('shorts'):
                    k = k[6:]
                    n = int(k[0]) - 1
                    kit[n].shortscolor = getColorValue(v)
                if k.startswith('socks'):
                    k = k[5:]
                    n = int(k[0]) - 1
                    kit[n].sockscolor = getColorValue(v)
                if k.startswith('pattern_b'):
                    k = k[9:]
                    n = int(k[0]) - 1
                    # TODO: body type, second color

    if len(players) < 15:
        print 'failed - only %d players found.' % len(players)
        return

    if not teamposition:
        teamposition = 0

    root = etree.Element("root")

    teamelem = etree.SubElement(root, 'Team')
    teamelem.set('name', team)
    if teamposition:
        teamelem.set('position', str(teamposition))
    for k in kit:
        kitelem = etree.SubElement(teamelem, 'Kit')
        kitelem.set('type', str(k.bodytype))
        addColorElement(kitelem, 'Body', k.bodycolor)
        addColorElement(kitelem, 'Body2', k.bodycolor2)
        addColorElement(kitelem, 'Shorts', k.shortscolor)
        addColorElement(kitelem, 'Socks', k.sockscolor)
    for p in players:
        playerelem = etree.SubElement(teamelem, 'Player')
        playerelem.set('name', p.name)
        playerelem.set('number', str(p.number))
        playerelem.set('pos', p.pos)
        playerelem.set('nationality', p.nationality)

    with open('output/' + titleToFilename(team) + '.xml', 'w') as f:
        f.write(etree.tostring(root, pretty_print=True))

    print 'done (kit %s, position %d, %d players)' % (kit[0].bodycolor, teamposition, len(players))

def getPage(title):
    title = title.replace(' ', '_')

    s = u'http://en.wikipedia.org/w/api.php?format=xml&action=query&titles=%s&prop=revisions&rvprop=content&redirects=1' % title
    sys.stdout.write('Processing %s... ' % title)
    sys.stdout.flush()
    s2 = urllib2.quote(s.encode('utf-8'), ':/&=?')
    infile = opener.open(s2)
    page = infile.read()

    pagexml = etree.XML(page)
    try:
        rvtext = pagexml.xpath('/api/query/pages/page/revisions/rev/text()')[0]
    except IndexError:
        print >> sys.stderr, "Couldn't find wikitext for", title
        return None

    with open('output/' + titleToFilename(title) + '.txt', 'w') as f:
        f.write(rvtext.encode('utf-8'))

    return rvtext

def titleToFilename(title):
    return title.replace(' ', '_').replace('.', '')


def fetchLeagueData():
    leaguelist = [u'Premier_League', u'Fußball-Bundesliga', u'Norwegian_Premier_League', u'Scottish_Premier_League']

    leagues = set(leaguelist)
    processedleagues = set()

    leaguedata = []
    mkdir_p('output')

    while len(leagues) > 0:
        seasons = set()
        newleagues = set()
        for l in leagues:
            rvtext = getPage(l)
            if rvtext:
                s, relegationleagues = getLeagueData(rvtext)
                if s:
                    seasons.add(s)
                if relegationleagues:
                    newleagues.update(relegationleagues)
                    print 'Added %d new league(s).' % len(relegationleagues)
                else:
                    print 'No new leagues.'
        processedleagues |= leagues
        leagues = newleagues - processedleagues

        for s in seasons:
            rvtext = getPage(s)
            handleLeague(rvtext, leaguedata)

def getLeagueData(rvtext):
    season = None
    relegationleagues = None
    for line in rvtext.split('\n'):
        lineWithoutSpaces = ''.join(line.split())
        if not season and lineWithoutSpaces.startswith("|current="):
            k, v = getKeyValue(line)
            competition, competitionlink = unlinkify(v)
            season = competitionlink

        # TODO: handle infobox football like in Fußball-Regionalliga_Nord
        if not relegationleagues and lineWithoutSpaces.startswith("|relegation="):
            k, v = getKeyValue(line)
            candidates = [unlinkify(x.strip())[1] for x in v.split('<br />')]
            relegationleagues = [c for c in candidates if c]

    return season, relegationleagues

def handleLeague(rvtext, leaguedata):
    teams = []

    competition = None

    tableStatus = 0
    teamColumn = -1
    thisColumn = -1
    for line in rvtext.split('\n'):
        lineWithoutSpaces = ''.join(line.split())
        if not competition and lineWithoutSpaces.startswith("|competition="):
            k, v = getKeyValue(line)
            competition, competitionlink = unlinkify(v)

        ls = line.strip()
        # print "Table status", tableStatus, "line", ls
        if table_re.match(ls):
            tableStatus = 1
            teamColumn = -1
            thisteams = []

        elif tableStatus == 1:
            if ls and ls[0] == '!':
                teamColumn += 1
                if 'Team' in ls or 'Club' in ls:
                    tableStatus = 2

        elif tableStatus == 2:
            if ls[0:2] == '|-':
                tableStatus = 3
                thisColumn = -1

        elif tableStatus == 3:
            if ls[0:2] == '|-':
                tableStatus = 2
                thisColumn = -1
            elif ls and ls[0] == '|':
                thisColumn += 1
                if thisColumn == teamColumn:
                    teamName = ls.strip('|')
                    thisteams.append(teamName)
                    tableStatus = 2
                    thisColumn = -1

        if (tableStatus == 2 or tableStatus == 3) and ls[0:2] == '|}':
            tableStatus = 0
            if len(thisteams) > len(teams):
                teams = thisteams

    print len(teams), 'teams found.'

    for t in teams:
        name, link = unlinkify(t)
        if link:
            fetchTeamData(link)

fetchLeagueData()
