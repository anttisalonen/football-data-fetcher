#!/usr/bin/env python2
# coding: utf-8

import unittest

import wikiutils
import parser
import teamparser
import soccer

class ParseLeague(unittest.TestCase):
    def test_parseEnglishPremierLeague(self):
        promotionleague = None
        leaguetitle = 'Premier_League'
        with open('tests/wikidumps/Premier_League.txt', 'r') as f:
            leaguedata = soccer.LeagueData(leaguetitle, promotionleague)
            parser.getLeagueData(f.read(), leaguedata)
            self.assertTrue(leaguedata.season == '2012–13 Premier League')
            self.assertTrue(leaguedata.numteams == 20)
            self.assertTrue(leaguedata.levelnum == 1)

    def test_parseEnglishPremierLeagueSeason(self):
        for file in ['tests/wikidumps/2012–13_Premier_League.txt', 'tests/wikidumps/Premier_League.txt']:
            with open(file, 'r') as f:
                teams = parser.getSeasonTeams(f.read(), 20, '')
                teamnames = [t[0] for t in teams if t]
                teamlinks = [t[1] for t in teams if t]
                self.assertTrue(len(teams) == 20)
                self.assertTrue(len(teamnames) == 20)
                self.assertTrue(len(teamlinks) == 20)
                self.assertTrue(('Chelsea', 'Chelsea F.C.') in teams)
                self.assertTrue(('Everton', 'Everton F.C.') in teams)
                self.assertTrue(('Liverpool', 'Liverpool F.C.') in teams)
                self.assertTrue(('Manchester United', 'Manchester United F.C.') in teams)
                self.assertTrue('Tottenham Hotspur' in teamnames)
                self.assertTrue('West Ham United F.C.' in teamlinks)

    def test_parseEnglishTopLeagues(self):
        for file in ['tests/wikidumps/Football_League_Championship.txt',
                'tests/wikidumps/Football_League_One.txt',
                'tests/wikidumps/Football_League_Two.txt']:
            with open(file, 'r') as f:
                leaguedata = soccer.LeagueData('', '')
                parser.getLeagueData(f.read(), leaguedata)
                self.assertTrue(leaguedata.numteams == 24)

    def test_parseEnglishTopSeasons(self):
        for file in ['tests/wikidumps/2012–13_Football_League_Championship.txt',
                'tests/wikidumps/2012–13_Football_League_One.txt',
                'tests/wikidumps/2012–13_Football_League_Two.txt']:
            with open(file, 'r') as f:
                teams = parser.getSeasonTeams(f.read(), 24, '')
                teamnames = [t[0] for t in teams if t]
                teamlinks = [t[1] for t in teams if t]
                self.assertTrue(len(teams) == 24)
                self.assertTrue(len(teamnames) == 24)
                self.assertTrue(len(teamlinks) == 24)

    def test_parseTeamSquad(self):
        with open('tests/wikidumps/Template:Boca_Unidos_squad.txt', 'r') as f:
            team = teamparser.parseTeam('', f.read(), False)
            self.assertTrue(team)
            self.assertTrue(len(team.players) == 33)
            self.assertTrue(team.players[32].name == 'José Luis Villanueva')
            self.assertTrue(team.players[32].pos == 'FW')
            self.assertTrue(team.players[32].nationality == 'CHI')

    def test_parseTeams(self):
        for file in ['tests/wikidumps/Everton_FC.txt',
                'tests/wikidumps/Parma_FC.txt',
                'tests/wikidumps/Rosenborg_BK.txt']:
            with open(file, 'r') as f:
                team = teamparser.parseTeam('', f.read(), False)
                self.assertTrue(team)
                self.assertTrue(len(team.players) > 20)
                self.assertTrue(team.pos > 0)
                self.assertTrue(team.pos <= 20)
                for p in team.players:
                    self.assertTrue(len(p.name) >= 3)
                    self.assertTrue(len(p.pos) >= 2)
                    self.assertTrue(len(p.nationality) >= 3)

    def test_parseScottishLeague(self):
        leagues = [('Scottish Premier League', 12), ('Scottish Football League First Division', 10),
                ('Scottish Football League Second Division', 10), ('Scottish Football League Third Division', 10)]
        for i in xrange(len(leagues)):
            leaguename = leagues[i][0]
            numteams = leagues[i][1]
            nextleaguename = leagues[i + 1][0] if i < len(leagues) - 1 else None
            seasonname = '2012–13 ' + leaguename.replace('Football League ', '')
            promotionleague = None if i == 0 else leagues[i - 1][0]
            leaguepath = 'tests/wikidumps/' + wikiutils.titleToFilename(leaguename) + '.txt'
            seasonpath = 'tests/wikidumps/' + wikiutils.titleToFilename(seasonname) + '.txt'
            leaguedata = soccer.LeagueData(leaguename, promotionleague)
            parser.getLeagueData(open(leaguepath, 'r').read(), leaguedata)
            if not nextleaguename:
                self.assertTrue(len(leaguedata.relegationleagues) == 0)
            else:
                self.assertTrue(len(leaguedata.relegationleagues) == 1)
                self.assertTrue(nextleaguename in leaguedata.relegationleagues.keys())
            self.assertTrue(leaguedata.title == leaguename)
            self.assertTrue(leaguedata.promotionleague == promotionleague)
            teams = parser.getSeasonTeams(open(seasonpath, 'r').read(), numteams, '')
            self.checkLeagueData(numteams, leaguedata, teams)

    def checkLeagueData(self, numTeams, leaguedata, teams):
        self.assertTrue(leaguedata.numteams == numTeams)
        teamnames = [t[0] for t in teams if t]
        teamlinks = [t[1] for t in teams if t]
        self.assertTrue(len(teams) == numTeams)
        self.assertTrue(len(teamnames) == numTeams)
        self.assertTrue(len(teamlinks) == numTeams)

    def test_parseOldInfoboxFootball(self):
        with open('tests/wikidumps/Regionalliga_Nord.txt', 'r') as f:
            leaguedata = soccer.LeagueData('', '')
            parser.getLeagueData(f.read(), leaguedata)
            self.assertTrue(leaguedata.season == '2012–13 Fußball-Regionalliga')
            self.assertTrue(leaguedata.numteams == 18)
            self.assertTrue(leaguedata.levelnum == 4)
            self.assertTrue(len(leaguedata.relegationleagues) == 4)
            self.assertTrue('Oberliga Hamburg' in leaguedata.relegationleagues.keys())
            self.assertTrue('Bremen-Liga' in leaguedata.relegationleagues.keys())
            self.assertTrue('Schleswig-Holstein-Liga' in leaguedata.relegationleagues.keys())
            self.assertTrue('Oberliga Niedersachsen' in leaguedata.relegationleagues.keys())

        with open('tests/wikidumps/Oberliga_Niedersachsen.txt', 'r') as f:
            leaguedata = soccer.LeagueData('', '')
            parser.getLeagueData(f.read(), leaguedata)
            self.assertTrue(leaguedata.numteams == 16)
            self.assertTrue(leaguedata.levelnum == 5)
            self.assertTrue(len(leaguedata.relegationleagues) == 4)
            self.assertTrue('Landesliga Braunschweig' in leaguedata.relegationleagues.keys())
            self.assertTrue('Landesliga Lüneburg' in leaguedata.relegationleagues.keys())
            self.assertTrue('Landesliga Hannover' in leaguedata.relegationleagues.keys())
            self.assertTrue('Landesliga Weser-Ems' in leaguedata.relegationleagues.keys())

    def test_ignoreHistoricalTeamList(self):
        with open('tests/wikidumps/Regionalliga_Süd.txt', 'r') as f:
            teams = parser.getSeasonTeams(f.read(), 18, '')
            self.assertTrue(teams is None)

if __name__ == '__main__':
    unittest.main()

