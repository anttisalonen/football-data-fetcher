#!/usr/bin/env python2
# coding: utf-8

import urllib2
from lxml import etree
import re
import sys
import os, errno

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

attributeAtStart_re = re.compile(r'[\w\s]*\|(.*)', re.UNICODE)

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

def fetchTeamData(team):
    class Player:
        def __init__(self, name, number, pos, nationality):
            self.name = name
            self.number = number
            self.pos = pos
            self.nationality = nationality

    unlinker_re = re.compile(r'(.*)\[\[(.*)\|(.*)\]\](.*)')

    s = u'http://en.wikipedia.org/w/api.php?format=xml&action=query&titles=%s&prop=revisions&rvprop=content&redirects=1' % team.replace(' ', '_')
    sys.stdout.write('Processing %s... ' % team)
    sys.stdout.flush()
    infile = opener.open(s.encode('utf-8'))
    page = infile.read()
    filebasename = team.replace(' ', '_').replace('.', '')
    filename = '%s.%s' % (team.replace(' ', '_').replace('.', ''), 'xml')

    pagexml = etree.XML(page)
    try:
        rvtext = pagexml.xpath('/api/query/pages/page/revisions/rev/text()')[0]
    except IndexError:
        print >> sys.stderr, "Couldn't find wikitext for team", team
        return

    players = []

    with open('output/' + filebasename + '.txt', 'w') as f:
        f.write(rvtext.encode('utf-8'))

    for line in rvtext.split('\n'):
        if ('{{fs player' in line.lower() or '{{football squad player' in line.lower()) and line.strip()[-2:] == '}}':
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
                        name = unlinkify(v)[0]

            if number and nationality and pos and name:
                player = Player(name, number, pos, nationality)
                players.append(player)
        if '{{fs end}}' in line.lower() or '{[football squad end}}' in line.lower() or '{{football squad end2}}' in line.lower():
            # end of player list
            break

    if len(players) < 15:
        print 'failed - only %d players found.' % (len(players), team)
        return

    root = etree.Element("root")

    teamelem = etree.SubElement(root, 'Team')
    teamelem.set('name', team)
    for p in players:
        playerelem = etree.SubElement(teamelem, 'Player')
        playerelem.set('name', p.name)
        playerelem.set('number', str(p.number))
        playerelem.set('pos', p.pos)
        playerelem.set('nationality', p.nationality)

    with open('output/' + filebasename + '.xml', 'w') as f:
        f.write(etree.tostring(root, pretty_print=True))

    print 'done (%d players)' % len(players)

table_re = re.compile(r' *\{\| *class *= *"?wikitable"?.*')

def fetchLeagueData():
    leagues = ['2012–13_Premier_League', '2012–13_Fußball-Bundesliga', '2012_Norwegian_Premier_League',
            '2012-13_Scottish_Premier_League']

    leaguedata = []
    mkdir_p('output')

    for l in leagues:
        s = 'http://en.wikipedia.org/w/api.php?format=xml&action=query&titles=%s&prop=revisions&rvprop=content&redirects=1' % l.replace(' ', '_')
        sys.stdout.write('Processing %s...\n' % l)
        infile = opener.open(s)
        page = infile.read()
        filebasename = l.replace(' ', '_').replace('.', '')
        filename = '%s.%s' % (l.replace(' ', '_').replace('.', ''), 'xml')
        with open('output/' + filebasename + '.xml', 'w') as f:
            f.write(page)

        pagexml = etree.XML(page)
        try:
            rvtext = pagexml.xpath('/api/query/pages/page/revisions/rev/text()')[0]
        except IndexError:
            print >> sys.stderr, "Couldn't find wikitext for team", l
            continue

        handleLeague(rvtext, leaguedata)

def handleLeague(rvtext, leaguedata):
    teams = []

    tableStatus = 0
    teamColumn = -1
    thisColumn = -1
    for line in rvtext.split('\n'):
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

    for t in teams:
        name, link = unlinkify(t)
        fetchTeamData(link)

fetchLeagueData()
