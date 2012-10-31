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
                if state == 0 and lineWithoutSpaces == '|list1=':
                    state = 1

                elif state == 1:
                    if lineWithoutSpaces:
                        if (lineWithoutSpaces[0] == '|' or lineWithoutSpaces[0] == '}'):
                            break
                        if lineWithoutSpaces[0] == '*':
                            v = line.strip('*').strip()
                            name, link = wikiutils.unlinkify(v)
                            if link:
                                leagues[link] = name
                                print 'Found', name
    return leagues

def getLeagueData(leaguetitle, promotionleague, rvtext):
    season = None
    relegationleagues = dict()
    numteams = 0
    levelnum = 0
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

    return soccer.LeagueData(leaguetitle, season, relegationleagues, promotionleague, numteams, levelnum)

def getSeasonTeams(rvtext, numteams):
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
            tableStatus = 0
            # make sure there are no duplicates in the list - may happen
            # e.g. with historical winners tables (Regionalliga_Süd)
            if len(thisteams) == numteams and len(set(thisteams)) == len(thisteams):
                teams = thisteams
                break

    if teams:
        teamres = []
        for t in teams:
            name, link = wikiutils.unlinkify(t)
            teamres.append((name, link))
        return teamres
    else:
        return None

def handleSeason(rvtext, leaguedata):
    teams = getSeasonTeams(rvtext, leaguedata.numteams)

    numPartialTeams = 0
    numCompleteTeams = 0

    if teams:
        print len(teams), 'teams found.'
        root = etree.Element("League")
        root.set('title', leaguedata.title)
        for name, link in teams:
            if link:
                td = teamparser.fetchTeamData(link)
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


