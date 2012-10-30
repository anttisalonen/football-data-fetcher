#!/usr/bin/env python2
# coding: utf-8

import unittest

import parser
import soccer

class ParseLeague(unittest.TestCase):
    def test_parseEnglishPremierLeague(self):
        promotionleague = None
        leaguetitle = 'Premier_League'
        with open('tests/wikidumps/Premier_League.txt', 'r') as f:
            leaguedata = parser.getLeagueData(leaguetitle, promotionleague, f.read())
            self.assertTrue(leaguedata.season == '2012–13 Premier League')
            self.assertTrue(leaguedata.numteams == 20)
            self.assertTrue(leaguedata.levelnum == 1)

    def test_parseEnglishPremierLeagueSeason(self):
        for file in ['tests/wikidumps/2012–13_Premier_League.txt', 'tests/wikidumps/Premier_League.txt']:
            with open(file, 'r') as f:
                teams = parser.getSeasonTeams(f.read(), 20)
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
                leaguedata = parser.getLeagueData('', '', f.read())
                self.assertTrue(leaguedata.numteams == 24)

    def test_parseEnglishTopSeasons(self):
        for file in ['tests/wikidumps/2012–13_Football_League_Championship.txt',
                'tests/wikidumps/2012–13_Football_League_One.txt',
                'tests/wikidumps/2012–13_Football_League_Two.txt']:
            with open(file, 'r') as f:
                teams = parser.getSeasonTeams(f.read(), 24)
                teamnames = [t[0] for t in teams if t]
                teamlinks = [t[1] for t in teams if t]
                self.assertTrue(len(teams) == 24)
                self.assertTrue(len(teamnames) == 24)
                self.assertTrue(len(teamlinks) == 24)

if __name__ == '__main__':
    unittest.main()

