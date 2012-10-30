import re

import wikiutils
from settings import Globals
import playerparser
import soccer

kitinfo_re = re.compile(r'\| *(body|shorts|socks|pattern_b)([12]) *= *([0-9a-fA-F]*)')

def getColorValue(string):
    if string == 'yellow':
        return soccer.Color(255, 255, 0)
    elif string == 'red':
        return soccer.Color(255, 0, 0)
    elif string == 'blue':
        return soccer.Color(0, 0, 255)
    elif string == 'green':
        return soccer.Color(0, 255, 0)
    elif string == 'black':
        return soccer.Color(0, 0, 0)
    elif string == 'white':
        return soccer.Color(255, 255, 255)

    if len(string) != 6:
        return soccer.Color()
    r = string[0:2]
    g = string[2:4]
    b = string[4:6]
    try:
        return soccer.Color(int(r, 16), int(g, 16), int(b, 16))
    except ValueError:
        print >> Globals.errlog, 'Unknown color "%s"' % string
        return soccer.Color()

def fetchTeamData(team):
    rvtext = wikiutils.getPage(team)
    if not rvtext:
        print 'No revision text.'
        return None

    players = []
    teamposition = None
    kit = [soccer.Kit(), soccer.Kit()]
    finishedReadingPlayers = False
    lookForSquadTemplate = False

    def teamError(msg):
        print >> Globals.errlog, "Team %s: %s" % (team.encode('utf-8'), msg.encode('utf-8'))

    for line in rvtext.split('\n'):
        lineWithoutSpaces = ''.join(line.split())
        if not finishedReadingPlayers:
            p = playerparser.fetchPlayer(line)
            if p:
                players.append(p)
            else:
                heading = wikiutils.getHeading(line)
                if heading:
                    if 'current squad' in heading.lower() or ('first' in heading.lower() and 'squad' in heading.lower()):
                        lookForSquadTemplate = True
                    else:
                        lookForSquadTemplate = False
                elif lookForSquadTemplate:
                    t = wikiutils.getTemplate(line)
                    if t:
                        text = wikiutils.getPage('Template:' + t)
                        if text:
                            players = playerparser.fetchPlayers(text)
                            if len(players) > 15:
                                finishedReadingPlayers = True

        if playerparser.endOfPlayerList(line):
            finishedReadingPlayers = True

        if lineWithoutSpaces.startswith("|position="):
            # this seems to usually be either this or last season's position
            # TODO: Problems arise when a team was promoted or relegated
            tp = wikiutils.getNumberKeyValue(line)
            if tp:
                teamposition = tp

        kitresults = kitinfo_re.findall(line)
        for kitresult in kitresults:
            columns = [x.strip() for x in line.split('|') if 'body' in x or 'shorts' in x or 'socks' in x or 'pattern_b' in x]
            # apparently, n may be more than 1 if more than one kit part is on a line
            for c in columns:
                try:
                    k, v = wikiutils.getKeyValue(c)
                except:
                    continue

                if k.startswith('body'):
                    k = k[4:]
                    if not k: continue
                    n = int(k[0]) - 1
                    if n == 0 or n == 1:
                        kit[n].bodycolor = getColorValue(v)
                elif k.startswith('shorts'):
                    k = k[6:]
                    if not k: continue
                    n = int(k[0]) - 1
                    if n == 0 or n == 1:
                        kit[n].shortscolor = getColorValue(v)
                elif k.startswith('socks'):
                    k = k[5:]
                    if not k: continue
                    n = int(k[0]) - 1
                    if n == 0 or n == 1:
                        kit[n].sockscolor = getColorValue(v)
                elif k.startswith('pattern_b'):
                    k = k[9:]
                    if not k: continue
                    n = int(k[0]) - 1
                    # TODO: body type, second color

    if len(players) < 15:
        print 'failed - %d players found.' % len(players)
        return None

    if not teamposition:
        teamposition = 0

    print 'done (kit %s, position %d, %d players)' % (kit[0].bodycolor, teamposition, len(players))

    return soccer.Team(team, kit, teamposition, players)


