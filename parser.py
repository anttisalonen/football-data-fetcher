# coding: utf-8

from lxml import etree
import re

import wikiutils
import soccer
import teamparser
from settings import Globals

table_re = re.compile(r' *\{\| *class *= *"?wikitable"?.*')
br_re = re.compile(r'<br */?>')

def getTopLeagues():
    templates = ['UEFA_leagues', 'CONMEBOL_leagues', 'CONCACAF_leagues', 
            'CAF_leagues', 'AFC_leagues', 'OFC_leagues']
    leagues = dict()
    for t in templates:
        text = wikiutils.getPage('Template:' + t)
        if text:
            print 'done.'
            state = 0
            for line in text.split('\n'):
                lineWithoutSpaces = ''.join(line.split())
                if state == 0 and re.match('\|list[123456789]=', lineWithoutSpaces):
                    state = 1

                elif state == 1:
                    if lineWithoutSpaces:
                        if (lineWithoutSpaces[0] == '|' or lineWithoutSpaces[0] == '}'):
                            state == 0
                        if lineWithoutSpaces[0] == '*':
                            v = line.strip('*').strip()
                            name, link = wikiutils.unlinkify(v)
                            if link:
                                leagues[link] = name
                                print 'Found', name
    return leagues

def getLeagueData(rvtext, leaguedata):
    season = None
    relegationleagues = dict()
    numteams = 0
    levelnum = 0
    divisions = 0
    class InfoboxState:
        Outside = 0
        Entered = 1
        RelegationLeagues = 2
        NumTeams = 3
        NumLevel = 4
        Season = 5

    ibs = InfoboxState.Outside

    for line in rvtext.split('\n'):
        lineWithoutSpaces = ''.join(line.split())
        if not season and lineWithoutSpaces.startswith("|current="):
            k, v = wikiutils.getKeyValue(line)
            competition, competitionlink = wikiutils.unlinkify(v)
            season = competitionlink

        if not divisions and (lineWithoutSpaces.startswith("|divisions=") or lineWithoutSpaces.startswith("|division=")):
            tp = wikiutils.getNumberKeyValue(line)
            if tp:
                divisions = tp

        if not levelnum and (lineWithoutSpaces.startswith("|levels=") or lineWithoutSpaces.startswith("|level=")):
            tp = wikiutils.getNumberKeyValue(line)
            if tp:
                levelnum = tp

        if len(relegationleagues) == 0 and lineWithoutSpaces.startswith("|relegation="):
            k, v = wikiutils.getKeyValue(line)
            candidates = [wikiutils.unlinkify(x.strip()) for x in br_re.split(v)]
            for cn, cl in candidates:
                if cl:
                    relegationleagues[cl] = cl

        if not numteams and lineWithoutSpaces.startswith('|teams='):
            numteams = wikiutils.getNumberKeyValue(line)

        if ibs == InfoboxState.Outside and lineWithoutSpaces.startswith('{|class="infoboxfootball"'):
            # e.g. Regionalliga_Nord
            ibs = InfoboxState.Entered
        elif ibs != InfoboxState.Outside:
            if lineWithoutSpaces and lineWithoutSpaces[0] == '|':
                text = '|'.join(line.split('|')[2:])
                if not text and lineWithoutSpaces[0:2] == '|}':
                    ibs = InfoboxState.Outside
                    break
                elif text:
                    t, link = wikiutils.unlinkify(text)
                    tl = t.lower()
                    if 'background' in line:
                        if 'relegation' in tl:
                            ibs = InfoboxState.RelegationLeagues
                        elif 'number of clubs' in tl:
                            ibs = InfoboxState.NumTeams
                        elif 'level' in tl:
                            ibs = InfoboxState.NumLevel
                        elif 'current season' in tl:
                            ibs = InfoboxState.Season
                        else:
                            ibs = InfoboxState.Entered
                    else:
                        if ibs == InfoboxState.RelegationLeagues:
                            if not link:
                                ibs = InfoboxState.Entered
                            else:
                                relegationleagues[link] = link
                        elif ibs == InfoboxState.NumTeams:
                            pos = re.findall(r'\d+', t)
                            if len(pos) >= 1:
                                numteams = int(pos[0])
                        elif ibs == InfoboxState.NumLevel:
                            pos = re.findall(r'\d+', t)
                            if len(pos) >= 1:
                                levelnum = int(pos[0])
                        elif ibs == InfoboxState.Season:
                            if not link:
                                ibs = InfoboxState.Entered
                            else:
                                season = link

    if not leaguedata.season:
        leaguedata.season = season
    if not leaguedata.relegationleagues:
        leaguedata.relegationleagues = relegationleagues
    if not leaguedata.numteams:
        leaguedata.numteams = numteams
    if not leaguedata.divisions:
        leaguedata.divisions = divisions
    if not leaguedata.levelnum:
        leaguedata.levelnum = levelnum

def addOrUpdateTeamList(l, heading, teams):
    def cleaned(namelist):
        ret = []
        for t in sorted(namelist):
            ret.append(t.replace('&nbsp;', ' '))
        return ret
    """Check whether a list with the same team names already exists in the list.
    If this is the case, have the team list with more links in the list."""
    tlist = sorted([wikiutils.unlinkify(t) for t in teams])
    toinsert = cleaned([t[0] for t in tlist])
    previous = None
    teamPairList = [p[1] for p in l]
    prev = None
    for t in l:
        thistl = cleaned([x[0] for x in t[1]])
        if thistl == toinsert:
            prev = t
            break
    if prev:
        numLinksInPrev = len([x for x in prev[1] if x[1]])
        numLinksInThis = len([x for x in tlist if x[1]])
        if numLinksInThis > numLinksInPrev:
            l.remove(prev)
            l.append((heading, tlist))
    else:
        l.append((heading, tlist))

def getSeasonTeams(rvtext, leaguedata):
    """Collect all lists that seem to be club lists along with their corresponding headings.
    If one team list with the number of teams as length, we're done.
    If multiple team lists, all with the correct number of teams as length, are found,
    pick the one with the correct heading.
    If multiple team lists are found, all shorter than the correct number of teams,
    and the sum of the lists is the total number of teams, create one group for each list."""
    correctLengthTeamLists = []
    shorterTeamLists = []

    tableStatus = 0
    teamColumn = -1
    thisColumn = -1
    haveTeams = False
    thisTeamHeading = None

    """First collect all team lists."""
    for line in rvtext.split('\n'):
        lineWithoutSpaces = ''.join(line.split())

        ls = line.strip()
        # print "Table status", tableStatus, "line", ls
        hd = wikiutils.getHeading(ls)
        if hd:
            thisTeamHeading = hd

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
            elif len(ls) >= 2 and ls[0] == '|' and ls[1] != '}':
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
            # make sure there are no duplicates in the list - may happen
            # e.g. with historical winners tables (Regionalliga_Süd)
            if len(set(thisteams)) == len(thisteams):
                if len(thisteams) == leaguedata.numteams:
                    addOrUpdateTeamList(correctLengthTeamLists, thisTeamHeading, thisteams)
                elif thisteams and len(thisteams) < leaguedata.numteams:
                    # Only add list if the same team list not already added.
                    addOrUpdateTeamList(shorterTeamLists, thisTeamHeading, thisteams)

            tableStatus = 0
            thisteams = []
            thisTeamHeading = None

    groups = []
    if correctLengthTeamLists and leaguedata.divisions <= 1:
        if len(correctLengthTeamLists) == 1:
            groups = [('', correctLengthTeamLists[0][1])]
        else:
            if leaguedata.title:
                for theading, tlist in correctLengthTeamLists:
                    if theading and leaguedata.title in theading:
                        groups = [(theading, tlist)]
                        break
            if not groups:
                # if not found, default to the first one (correct in e.g. 2012_Ykkönen)
                groups = [('', correctLengthTeamLists[0][1])]

    elif shorterTeamLists and (leaguedata.divisions == 0 or len(shorterTeamLists) == leaguedata.divisions):
        totalNumTeams = sum([len(l[1]) for l in shorterTeamLists])
        if totalNumTeams == leaguedata.numteams:
            groups = shorterTeamLists

    return groups

def getTeamData(rvtext, leaguedata):
    if leaguedata.hasTeams():
        return

    groups = getSeasonTeams(rvtext, leaguedata)

    if groups:
        print len(groups), 'groups found.'
        for name, teams in groups:
            numCompleteTeams = 0
            group = soccer.LeagueGroup(name, leaguedata.title)
            print '%d teams in group %s.' % (len(teams), name)
            for name, link in teams:
                if link:
                    td = teamparser.fetchTeamData(link)
                    if td:
                        if len(td.players) > 0:
                            numCompleteTeams += 1
                        group.teams.append(td)
                    else:
                        group.teams.append(soccer.Team(name, [], 0, []))
            numPartialTeams = len(teams) - numCompleteTeams
            group.numPartialTeams = numPartialTeams
            group.numCompleteTeams = numCompleteTeams
            leaguedata.groups.append(group)
    else:
        print "Failed finding teams."


