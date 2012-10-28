#!/usr/bin/env python2
# coding: utf-8

import urllib2
from lxml import etree
import re
import sys
import os, errno
import json

import cPickle as pickle

def getAppDataDir(appname):
    # http://stackoverflow.com/questions/1084697/how-do-i-store-desktop-application-data-in-a-cross-platform-way-for-python
    if sys.platform == 'darwin':
        from AppKit import NSSearchPathForDirectoriesInDomains
        # http://developer.apple.com/DOCUMENTATION/Cocoa/Reference/Foundation/Miscellaneous/Foundation_Functions/Reference/reference.html#//apple_ref/c/func/NSSearchPathForDirectoriesInDomains
        # NSApplicationSupportDirectory = 14
        # NSUserDomainMask = 1
        # True for expanding the tilde into a fully qualified path
        appdata = os.path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], appname)
    elif sys.platform == 'win32':
        appdata = os.path.join(os.environ['APPDATA'], appname)
    else:
        appdata = os.path.expanduser(os.path.join("~", "." + appname))
    return appdata

unlinker_re = re.compile(r'(.*)\[\[(.*)\|(.*)\]\](.*)')
attributeAtStart_re = re.compile(r'[\w\s]*\|(.*)', re.UNICODE)
table_re = re.compile(r' *\{\| *class *= *"?wikitable"?.*')
kitinfo_re = re.compile(r'\| *(body|shorts|socks|pattern_b)([12]) *= *([0-9a-fA-F]*)')
removeAngleBrackets_re = re.compile(r'\<[^>]*\>')

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
    def __init__(self, name, title):
        self.name = name
        self.title = title


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
    try:
        vals = [s.strip() for s in line.split('=')]
        return vals[0], vals[1]
    except:
        print >> Globals.errlog, 'Error getting key-value pair from "%s"' % line
        raise

def getColorValue(string):
    if string == 'yellow':
        return Color(255, 255, 0)
    elif string == 'red':
        return Color(255, 0, 0)
    elif string == 'blue':
        return Color(0, 0, 255)
    elif string == 'green':
        return Color(0, 255, 0)
    elif string == 'black':
        return Color(0, 0, 0)
    elif string == 'white':
        return Color(255, 255, 255)

    if len(string) != 6:
        return Color()
    r = string[0:2]
    g = string[2:4]
    b = string[4:6]
    try:
        return Color(int(r, 16), int(g, 16), int(b, 16))
    except ValueError:
        print >> Globals.errlog, 'Unknown color "%s"' % string
        return Color()

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

def getHeading(line):
    s = line.strip()
    if not s.startswith('==') or not s.endswith('=='):
        return None
    s = s.strip('==')
    s = s.strip()
    return s

def fetchPlayer(line):
    def playerError(msg):
        print >> Globals.errlog, "Player %s: %s" % (line.encode('utf-8'), msg.encode('utf-8'))

    lineWithoutSpaces = ''.join(line.split())
    ll = line.lower()
    if '{{fs player' in ll or \
            '{{football squad player' in ll or \
            '{{fs2 player' in ll:
        unlinkedline = line
        while True:
            res = unlinker_re.match(unlinkedline)
            if res:
                groups = res.groups()
                try:
                    unlinkedline = groups[0] + groups[2] + groups[3]
                except IndexError:
                    playerError(u"Couldn't find groups at %s" % groups)
                    break
            else:
                break

        columns = [s.strip() for s in unlinkedline.replace('{', '').replace('}', '').split('|')]
        number = None
        nationality = None
        pos = None
        name = None
        firstname = None
        lastname = None
        for column in columns:
            if '=' in column:
                try:
                    k, v = getKeyValue(column)
                except ValueError:
                    playerError("Couldn't parse player information column: %s" % column)
                    continue
                if k == 'no':
                    try:
                        number = int(v)
                    except (UnicodeEncodeError, ValueError):
                        pass # usually dash as a player number
                elif k == 'nat':
                    nationality = v
                elif k == 'pos':
                    pos = v
                elif k == 'name':
                    name = unlinkify(v)[0]
                elif k == 'first':
                    firstname = unlinkify(v)[0]
                elif k == 'last':
                    lastname = unlinkify(v)[0]

        if not name and firstname and lastname:
            name = firstname + ' ' + lastname

        if not number:
            number = 0

        if nationality and pos and name:
            return Player(name, number, pos, nationality)

    return None

def endOfPlayerList(line):
    return '{{fs end}}' in line.lower() or '{[football squad end}}' in line.lower() or '{{football squad end2}}' in line.lower()

def fetchPlayers(text):
    players = []

    for line in text.split('\n'):
        p = fetchPlayer(line)
        if p:
            players.append(p)
        elif endOfPlayerList(line):
            break

    return players

class Team:
    def __init__(self, name, kits, pos, players):
        self.name = name
        self.kits = kits
        self.pos = pos
        self.players = players

    def toXML(self):
        teamelem = etree.Element('Team')
        teamelem.set('name', self.name)
        if self.pos:
            teamelem.set('position', str(self.pos))
        for k in self.kits:
            kitelem = etree.SubElement(teamelem, 'Kit')
            kitelem.set('type', str(k.bodytype))
            addColorElement(kitelem, 'Body', k.bodycolor)
            addColorElement(kitelem, 'Body2', k.bodycolor2)
            addColorElement(kitelem, 'Shorts', k.shortscolor)
            addColorElement(kitelem, 'Socks', k.sockscolor)
        for p in self.players:
            playerelem = etree.SubElement(teamelem, 'Player')
            playerelem.set('name', p.name)
            playerelem.set('number', str(p.number))
            playerelem.set('pos', p.pos)
            playerelem.set('nationality', p.nationality)

        return teamelem

def fetchTeamData(team):
    rvtext = getPage(team)
    if not rvtext:
        print 'No revision text.'
        return None

    players = []
    teamposition = None
    kit = [Kit(), Kit()]
    finishedReadingPlayers = False
    lookForSquadTemplate = False

    def teamError(msg):
        print >> Globals.errlog, "Team %s: %s" % (team.encode('utf-8'), msg.encode('utf-8'))

    for line in rvtext.split('\n'):
        lineWithoutSpaces = ''.join(line.split())
        if not finishedReadingPlayers:
            p = fetchPlayer(line)
            if p:
                players.append(p)
            else:
                heading = getHeading(line)
                if heading:
                    if 'current squad' in heading.lower() or ('first' in heading.lower() and 'squad' in heading.lower()):
                        lookForSquadTemplate = True
                    else:
                        lookForSquadTemplate = False
                elif lookForSquadTemplate:
                    t = getTemplate(line)
                    if t:
                        text = getPage('Template:' + t)
                        if text:
                            players = fetchPlayers(text)
                            if len(players) > 15:
                                finishedReadingPlayers = True

        elif endOfPlayerList(line):
            finishedReadingPlayers = True

        if lineWithoutSpaces.startswith("|position="):
            # this seems to usually be either this or last season's position
            # TODO: Problems arise when a team was promoted or relegated
            k, v = getKeyValue(removeAngleBrackets_re.sub('', line))
            pos = re.findall(r'\d+', v)
            if len(pos) == 1:
                teamposition = int(pos[0])

        kitresults = kitinfo_re.findall(line)
        for kitresult in kitresults:
            columns = [x.strip() for x in line.split('|') if 'body' in x]
            # apparently, n may be more than 1 if more than one kit part is on a line
            for c in columns:
                try:
                    k, v = getKeyValue(c)
                except:
                    continue

                if k.startswith('body'):
                    k = k[4:]
                    n = int(k[0]) - 1
                    if n == 0 or n == 1:
                        kit[n].bodycolor = getColorValue(v)
                elif k.startswith('shorts'):
                    k = k[6:]
                    n = int(k[0]) - 1
                    if n == 0 or n == 1:
                        kit[n].shortscolor = getColorValue(v)
                elif k.startswith('socks'):
                    k = k[5:]
                    n = int(k[0]) - 1
                    if n == 0 or n == 1:
                        kit[n].sockscolor = getColorValue(v)
                elif k.startswith('pattern_b'):
                    k = k[9:]
                    n = int(k[0]) - 1
                    # TODO: body type, second color

    if len(players) < 15:
        print 'failed - %d players found.' % len(players)
        return None

    if not teamposition:
        teamposition = 0

    print 'done (kit %s, position %d, %d players)' % (kit[0].bodycolor, teamposition, len(players))

    return Team(team, kit, teamposition, players)

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

class LeagueData:
    def __init__(self, title, season, relegationleagues, promotionleague, numteams):
        self.title = title
        self.season = season
        self.relegationleagues = relegationleagues
        self.numteams = numteams
        self.promotionleague = promotionleague

class ProcessedLeague:
    def __init__(self, leaguedata, numCompleteTeams, numPartialTeams, numFollowingLeagues):
        self.leaguedata = leaguedata
        self.numCompleteTeams = numCompleteTeams
        self.numPartialTeams = numPartialTeams
        self.numFollowingLeagues = numFollowingLeagues

class Progress:
    def __init__(self):
        self.leagues = dict()
        self.processedleagues = dict()

    def leagueProcessed(self, l, numCompleteTeams, numPartialTeams, numFollowingLeagues):
        self.processedleagues[l.title] = ProcessedLeague(l, numCompleteTeams, numPartialTeams, numFollowingLeagues)
        del self.leagues[l.title]

    def __str__(self):
        s = 'Progress: %d leagues in the queue, %d processed\n' % (len(self.leagues), len(self.processedleagues))
        if self.processedleagues:
            s += '%50s    %10s %10s %10s %10s\n' % ('League', 'total', 'complete', 'partial', 'following')
            for l, data in sorted(self.processedleagues.items()):
                s += '%50s => %10d %10d %10d %10d\n' % (data.leaguedata.title.encode('utf-8'),
                        data.leaguedata.numteams, data.numCompleteTeams, data.numPartialTeams, data.numFollowingLeagues)

        if self.leagues:
            s += 'Leagues in queue:\n'
            for l in self.leagues.keys():
                s += l.encode('utf-8') + '\n'
        return s

def getTopLeagues():
    templates = ['UEFA_leagues', 'CONMEBOL_leagues']
    leagues = dict()
    for t in templates:
        text = getPage('Template:' + t)
        if text:
            print 'done.'
            state = 0
            for line in text.split('\n'):
                lineWithoutSpaces = ''.join(line.split())
                if state == 0 and lineWithoutSpaces == '|list1=':
                    state = 1

                elif state == 1:
                    if lineWithoutSpaces[0] == '|' or lineWithoutSpaces[0] == '}':
                        break
                    if lineWithoutSpaces[0] == '*':
                        v = line.strip('*').strip()
                        name, link = unlinkify(v)
                        if link:
                            leagues[link] = name
                            print 'Found', name
    return leagues

def fetchLeagueData():
    didSomething = False
    try:
        load()
        print Globals.progress
    except IOError as exc:
        if exc.errno == errno.ENOENT:
            print 'No previous progress - starting from the top.'
            Globals.progress.leagues = getTopLeagues()
            Globals.progress.processedleagues = dict()
            save()
        else:
            raise

    if len(Globals.progress.processedleagues) == 0 and len(Globals.progress.leagues) == 0:
        print 'No progress - starting from the top.'
        Globals.progress.leagues = getTopLeagues()
        Globals.progress.processedleagues = dict()
        save()

    while len(Globals.progress.leagues) > 0:
        leaguetitle = iter(Globals.progress.leagues).next()
        numCompleteTeams = 0
        numPartialTeams = 0
        numFollowingLeagues = 0

        promotionleague = None
        for processedleaguename, processedleague in Globals.progress.processedleagues.items():
            if processedleague.leaguedata.relegationleagues and leaguetitle in processedleague.leaguedata.relegationleagues:
                promotionleague = processedleaguename
                break

        leaguedata = None
        rvtext = getPage(leaguetitle)
        if rvtext:
            leaguedata = getLeagueData(leaguetitle, promotionleague, rvtext)
            if leaguedata.season and leaguedata.numteams:
                print 'proceed to current season.'
                stext = getPage(leaguedata.season, True)
                if stext:
                    numCompleteTeams, numPartialTeams = handleSeason(stext, leaguedata)
                    if leaguedata.relegationleagues:
                        numFollowingLeagues = 0
                        for rln, rll in leaguedata.relegationleagues.items():
                            if rln not in Globals.progress.leagues:
                                Globals.progress.leagues[rll] = rln
                                numFollowingLeagues += 1
                        print 'Added %d new league(s).' % numFollowingLeagues
                else:
                    print 'Failed - no season text.'
            else:
                print 'Failed.'

        didSomething = True
        Globals.progress.leagueProcessed(leaguedata, numCompleteTeams, numPartialTeams, numFollowingLeagues)

    return didSomething

def getLeagueData(leaguetitle, promotionleague, rvtext):
    season = None
    relegationleagues = dict()
    numteams = 0

    for line in rvtext.split('\n'):
        lineWithoutSpaces = ''.join(line.split())
        if not season and lineWithoutSpaces.startswith("|current="):
            k, v = getKeyValue(line)
            competition, competitionlink = unlinkify(v)
            season = competitionlink

        # TODO: handle infobox football like in Fußball-Regionalliga_Nord
        if len(relegationleagues) == 0 and lineWithoutSpaces.startswith("|relegation="):
            k, v = getKeyValue(line)
            candidates = [unlinkify(x.strip()) for x in v.split('<br />')]
            for cn, cl in candidates:
                if cl:
                    relegationleagues[cn if cn else cl] = cl

        if not numteams and lineWithoutSpaces.startswith('|teams='):
            k, v = getKeyValue(line)
            name, link = unlinkify(v)
            try:
                numteams = int(name)
            except ValueError:
                # TODO: parse fail here due to one league split across multiple levels
                pass

    return LeagueData(leaguetitle, season, relegationleagues, promotionleague, numteams)

def getTemplate(text):
    l = text.strip()
    if l.startswith('{{') and l.endswith('}}'):
        l = l.strip('{{').strip('}}')
        if '|' in l:
            return l.split('|')[0]
    else:
        return None

def handleSeason(rvtext, leaguedata):
    teams = None

    tableStatus = 0
    teamColumn = -1
    thisColumn = -1
    haveTeams = False

    for line in rvtext.split('\n'):
        lineWithoutSpaces = ''.join(line.split())

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
            elif ls and ls[0] == '|' and ls[1] != '}':
                columns = ls.split('||')
                if len(columns) == 1:
                    ''' Columns divided by line. It looks like this (e.g. Premier League):
                    {| class="wikitable sortable"
                    ! Team
                    ! Location
                    ! Stadium
                    |-
                    | [[Arsenal]]
                    | [[London]]
                    | [[Emirates Stadium]]
                    |-
                    ...
                    |}
                    '''
                    thisColumn += 1
                    if thisColumn == teamColumn:
                        teamName = ls.strip('|')
                        thisteams.append(teamName)
                        tableStatus = 2
                        thisColumn = -1
                else:
                    ''' Columns on one line. It looks like this (e.g. Football_League_Championship):
                    {| class="wikitable sortable"
                    ! Team
                    ! Location
                    ! Stadium
                    |-
                    | {{ fb team Barnsley }} || [[Barnsley]] || [[Oakwell]]
                    |-
                    ...
                    |}
                    '''
                    columns = [x.strip() for x in ls[1:].split('||')]
                    if len(columns) > teamColumn:
                        thisteams.append(columns[teamColumn])
                    tableStatus = 2

        if (tableStatus == 2 or tableStatus == 3) and ls[0:2] == '|}':
            tableStatus = 0
            if len(thisteams) == leaguedata.numteams:
                teams = thisteams
                break

    numPartialTeams = 0
    numCompleteTeams = 0

    if teams:
        print len(teams), 'teams found.'
        root = etree.Element("League")
        root.set('title', leaguedata.title)
        for t in teams:
            name, link = unlinkify(t)
            if link:
                td = fetchTeamData(link)
                if td and len(td.players) > 0:
                    numCompleteTeams += 1
                    teamelem = td.toXML()
                    root.append(teamelem)
        numPartialTeams = len(teams) - numCompleteTeams
        with open(Globals.outputdir + leaguedata.title + '.xml', 'w') as f:
            f.write(etree.tostring(root, pretty_print=True))
    else:
        print "Failed finding teams."

    return numCompleteTeams, numPartialTeams

class Globals:
    appname = "football_data_fetcher"
    datadir = getAppDataDir(appname) + '/'
    progress = Progress()
    outputdir = datadir + 'output/'
    mkdir_p(outputdir)
    errlog = open(datadir + 'error.log', 'a')
    progpath = datadir + 'progress.json'

def main():
    didSomething = False
    try:
        didSomething = fetchLeagueData()
    except:
        # http://www.doughellmann.com/articles/how-tos/python-exception-handling/index.html
        try:
            raise
        finally:
            try:
                cleanup()
            except Exception, e:
                print >> sys.stderr, "Error: couldn't save progress:", str(e)
                pass
    else:
        if didSomething:
            print 'Success!'
            cleanup()

def save():
    with open(Globals.progpath, 'w') as f:
        pickle.dump(Globals.progress, f)

def load():
    with open(Globals.progpath, 'r') as f:
        Globals.progress = pickle.load(f)

def cleanup():
    print Globals.progress
    save()
    Globals.errlog.close()

if __name__ == '__main__':
    main()
