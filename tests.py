#!/usr/bin/env python2
# coding: utf-8

import unittest

import wikiutils
import parser
import teamparser
import soccer

class ParseLeague(unittest.TestCase):
    def parseDump(self, name, seasontitle, numteams, numgroups = 0, levelnum = 0):
        leaguetext = open('tests/wikidumps/%s.txt' % name, 'r').read()
        if seasontitle:
            seasontext = open('tests/wikidumps/%s.txt' % seasontitle, 'r').read()
        else:
            seasontext = None

        leaguedata = soccer.LeagueData(name, '')
        parser.getLeagueData(leaguetext, leaguedata)

        groups = None
        if seasontext:
            parser.getLeagueData(seasontext, leaguedata)
            groups = parser.getSeasonTeams(seasontext, leaguedata)
        if not groups:
            groups = parser.getSeasonTeams(leaguetext, leaguedata)

        self.assertEqual(leaguedata.numteams, numteams)
        if numgroups:
            self.assertEqual(len(groups), numgroups)
        if levelnum:
            self.assertEqual(leaguedata.levelnum, levelnum)
        return leaguedata

    def test_parseKakkonen(self):
        ld = self.parseDump('Kakkonen', '2012_Kakkonen', 40, 4)

    def test_parseEnglishPremierLeague(self):
        self.parseDump('Premier_League', '2012–13_Premier_League', 20, 1, 1)

    def test_parseEnglishPremierLeagueSeason(self):
        for file in ['tests/wikidumps/2012–13_Premier_League.txt', 'tests/wikidumps/Premier_League.txt']:
            with open(file, 'r') as f:
                l = soccer.LeagueData('', '')
                l.numteams = 20
                groups = parser.getSeasonTeams(f.read(), l)
                self.assertEqual(len(groups), 1)
                teams = groups[0][1]
                teamnames = [t[0] for t in teams if t]
                teamlinks = [t[1] for t in teams if t]
                self.assertEqual(len(teams), 20)
                self.assertEqual(len(teamnames), 20)
                self.assertEqual(len(teamlinks), 20)
                self.assertIn(('Chelsea', 'Chelsea F.C.'), teams)
                self.assertIn(('Everton', 'Everton F.C.'), teams)
                self.assertIn(('Liverpool', 'Liverpool F.C.'), teams)
                self.assertIn(('Manchester United', 'Manchester United F.C.'), teams)
                self.assertIn('Tottenham Hotspur', teamnames)
                self.assertIn('West Ham United F.C.', teamlinks)

    def test_parseEnglishTopLeagues(self):
        for file in ['tests/wikidumps/Football_League_Championship.txt',
                'tests/wikidumps/Football_League_One.txt',
                'tests/wikidumps/Football_League_Two.txt']:
            with open(file, 'r') as f:
                leaguedata = soccer.LeagueData('', '')
                parser.getLeagueData(f.read(), leaguedata)
                self.assertEqual(leaguedata.numteams, 24)

    def test_parseEnglishTopSeasons(self):
        for file in ['tests/wikidumps/2012–13_Football_League_Championship.txt',
                'tests/wikidumps/2012–13_Football_League_One.txt',
                'tests/wikidumps/2012–13_Football_League_Two.txt']:
            with open(file, 'r') as f:
                l = soccer.LeagueData('', '')
                l.numteams = 24
                groups = parser.getSeasonTeams(f.read(), l)
                self.assertEqual(len(groups), 1)
                teams = groups[0][1]
                teamnames = [t[0] for t in teams if t]
                teamlinks = [t[1] for t in teams if t]
                self.assertEqual(len(teams), 24)
                self.assertEqual(len(teamnames), 24)
                self.assertEqual(len(teamlinks), 24)

    def test_parseTeamSquad(self):
        with open('tests/wikidumps/Template:Boca_Unidos_squad.txt', 'r') as f:
            team = teamparser.parseTeam('', f.read(), False)
            self.assertTrue(team)
            self.assertEqual(len(team.players), 33)
            self.assertEqual(team.players[32].name, 'José Luis Villanueva')
            self.assertEqual(team.players[32].pos, 'FW')
            self.assertEqual(team.players[32].nationality, 'CHI')

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
                self.assertEqual(len(leaguedata.relegationleagues), 0)
            else:
                self.assertEqual(len(leaguedata.relegationleagues), 1)
                self.assertIn(nextleaguename, leaguedata.relegationleagues.keys())
            self.assertEqual(leaguedata.title, leaguename)
            self.assertEqual(leaguedata.promotionleague, promotionleague)
            groups = parser.getSeasonTeams(open(seasonpath, 'r').read(), leaguedata)
            self.assertEqual(len(groups), 1)
            teams = groups[0][1]
            self.checkLeagueData(numteams, leaguedata, teams)

    def checkLeagueData(self, numTeams, leaguedata, teams):
        self.assertEqual(leaguedata.numteams, numTeams)
        teamnames = [t[0] for t in teams if t]
        teamlinks = [t[1] for t in teams if t]
        self.assertEqual(len(teams), numTeams)
        self.assertEqual(len(teamnames), numTeams)
        self.assertEqual(len(teamlinks), numTeams)

    def test_parseOldInfoboxFootball(self):
        with open('tests/wikidumps/Regionalliga_Nord.txt', 'r') as f:
            leaguedata = soccer.LeagueData('', '')
            parser.getLeagueData(f.read(), leaguedata)
            self.assertEqual(leaguedata.season, '2012–13 Fußball-Regionalliga')
            self.assertEqual(leaguedata.numteams, 18)
            self.assertEqual(leaguedata.levelnum, 4)
            self.assertEqual(len(leaguedata.relegationleagues), 4)
            self.assertIn('Oberliga Hamburg', leaguedata.relegationleagues.keys())
            self.assertIn('Bremen-Liga', leaguedata.relegationleagues.keys())
            self.assertIn('Schleswig-Holstein-Liga', leaguedata.relegationleagues.keys())
            self.assertIn('Oberliga Niedersachsen', leaguedata.relegationleagues.keys())

        leaguedata = self.parseDump('Oberliga_Niedersachsen', None, 16, 0, 5)
        self.assertEqual(len(leaguedata.relegationleagues), 4)
        self.assertIn('Landesliga Braunschweig', leaguedata.relegationleagues.keys())
        self.assertIn('Landesliga Lüneburg', leaguedata.relegationleagues.keys())
        self.assertIn('Landesliga Hannover', leaguedata.relegationleagues.keys())
        self.assertIn('Landesliga Weser-Ems', leaguedata.relegationleagues.keys())

    def test_ignoreHistoricalTeamList(self):
        with open('tests/wikidumps/Regionalliga_Süd.txt', 'r') as f:
            l = soccer.LeagueData('', '')
            l.numteams = 18
            teams = parser.getSeasonTeams(f.read(), l)
            self.assertTrue(not teams)

    def test_parseLegaProPrimaDivisione(self):
        leaguetext = open('tests/wikidumps/Lega_Pro_Prima_Divisione.txt', 'r').read()
        seasontext = open('tests/wikidumps/2012–13_Lega_Pro_Prima_Divisione.txt', 'r').read()
        leaguedata = soccer.LeagueData('', '')
        parser.getLeagueData(leaguetext, leaguedata)
        self.assertEqual(leaguedata.numteams, 33)
        groups = parser.getSeasonTeams(seasontext, leaguedata)
        self.assertEqual(len(groups), 2)

if __name__ == '__main__':
    unittest.main()

