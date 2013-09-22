#!/usr/bin/env python2
# coding: utf-8

from lxml import etree

import re
import sys
import os, errno
import json
import cPickle as pickle
import argparse

import utils
import parser
from settings import Globals
import wikiutils
import soccer

def fetchLeagueData(specificLeague):
    try:
        load()
    except IOError as exc:
        if exc.errno == errno.ENOENT:
            print 'No previous progress - starting from the top.'
            Globals.progress.leagues = parser.getTopLeagues()
            Globals.progress.processedleagues = dict()
            save()
        else:
            raise

    if len(Globals.progress.processedleagues) == 0 and len(Globals.progress.leagues) == 0:
        print 'No progress - starting from the top.'
        Globals.progress.leagues = parser.getTopLeagues()
        Globals.progress.processedleagues = dict()
        save()

    while specificLeague or len(Globals.progress.leagues) > 0:
        if specificLeague:
            found = None
            for k in Globals.progress.leagues.keys():
                if specificLeague in k:
                    found = k
                    leaguetitle = found
                    leaguename, country, toplevelleague, confederationname = Globals.progress.leagues[found]
                    break

            if not found:
                for k in Globals.progress.processedleagues.keys():
                    if specificLeague == k:
                        found = k
                        leaguetitle = found
                        league = Globals.progress.processedleagues[found]
                        country = league.country
                        toplevelleague = league.toplevelleague
                        confederationname = league.confederation
                        break

            if not found:
                print >> sys.stderr, "I don't have league '%s' queued.\n" % specificLeague
                print >> sys.stderr, "%s\n" % Globals.progress.printQueuedLeagues()
                return
        else:
            leaguetitle = iter(Globals.progress.leagues).next()
            leaguename, country, toplevelleague, confederationname = Globals.progress.leagues[leaguetitle]

        promotionleague = None
        for processedleaguename, processedleague in Globals.progress.processedleagues.items():
            if processedleague.relegationleagues and leaguetitle in processedleague.relegationleagues:
                promotionleague = processedleaguename
                break

        leaguedata = None
        rvtext = wikiutils.getPage(leaguetitle)
        if rvtext:
            """First get and parse the league text as it may contain a link to the current season.
            Then, try to complement any league data from the season page.
            Finally, try to get the team data, from the season link first if possible."""
            leaguedata = soccer.LeagueData(leaguetitle, promotionleague, confederationname, country, toplevelleague)
            parser.getLeagueData(rvtext, leaguedata)
            if leaguedata.season:
                stext = wikiutils.getPage(leaguedata.season, True)
            else:
                stext = None

            if stext:
                parser.getLeagueData(stext, leaguedata)

            # overwrite levelnum from the wiki info as it seems to be unreliable (e.g. Venezuelan_Segunda_División)
            if not promotionleague:
                leaguedata.levelnum = 1
            else:
                leaguedata.levelnum = Globals.progress.processedleagues[promotionleague].levelnum + 1

            if Globals.fetchTeams:
                if stext:
                    parser.getTeamData(stext, leaguedata)
                parser.getTeamData(rvtext, leaguedata)

            if leaguedata.hasTeams():
                root = leaguedata.toXML()
                outdir = Globals.outputdir + wikiutils.titleToFilename(leaguedata.confederation) + '/' + country + '/'
                utils.mkdir_p(outdir)
                with open(outdir + wikiutils.titleToFilename(leaguedata.title) + '.xml', 'w') as f:
                    f.write(etree.tostring(root, pretty_print=True))

                if leaguedata.relegationleagues:
                    for rln, rll in leaguedata.relegationleagues.items():
                        if rln not in Globals.progress.leagues:
                            Globals.progress.leagues[rll] = (rln, country, toplevelleague, confederationname)
                    print '%d following league(s): %s' % (len(leaguedata.relegationleagues), leaguedata.relegationleagues.keys())
                else:
                    print 'No following leagues.'
            else:
                print 'Failed to fetch teams.'
        else:
            print 'No revision text for league.'

        Globals.didSomething = True
        if leaguedata:
            Globals.progress.leagueProcessed(leaguedata)
        else:
            del Globals.progress.leagues[leaguetitle]

        save()

        if specificLeague:
            return

def main():
    parser = argparse.ArgumentParser(description = 'Fetch soccer league, team and player data from Wikipedia.')
    parser.add_argument('-L', dest = 'specific_league', type = str,
            default = '', help = 'fetch only one league')
    parser.add_argument('-l', dest = 'fetch_only_leagues', action = 'store_true', help = 'fetch only leagues')
    parser.add_argument('-o', dest = 'output_dir', action = 'store', type = str, default = '', help = 'output directory')

    args = parser.parse_args()
    Globals.setDataDir(args.output_dir)
    if args.fetch_only_leagues:
        Globals.fetchTeams = False
        Globals.dumpTextFiles = True
    try:
        fetchLeagueData(args.specific_league)
    except:
        # http://www.doughellmann.com/articles/how-tos/python-exception-handling/index.html
        try:
            raise
        finally:
            try:
                cleanup()
                print Globals.progress
            except Exception, e:
                print >> sys.stderr, "Error: couldn't save progress:", str(e)
                pass
    else:
        if Globals.didSomething:
            print 'Finished.'
            cleanup()
        print Globals.progress
        run_tests(Globals.progress)

def run_tests(progress):
    to_test = {
            'England'                : [0.95, 0.95, 0.95, 0.90, 0.90],
            'Scotland'               : [0.95, 0.95, 0.95, 0.95],
            'Brazil'                 : [1.00, 1.00, 0.90],
            'Italy'                  : [0.95, 0.95, 0.90],
            'France'                 : [0.90, 0.90, 0.90],
            'Germany'                : [0.90, 0.85, 0.85],
            'Japan'                  : [0.90, 0.90, 0.50],
            'Austria'                : [0.90, 0.90, 0.25],
            'Belgium'                : [1.00, 1.00],
            'Argentina'              : [0.95, 0.95],
            'Thailand'               : [0.95, 0.95],
            'Spain'                  : [0.90, 0.90],
            'Netherlands'            : [0.90, 0.90],
            'Portugal'               : [0.90, 0.90],
            'Finland'                : [0.90, 0.90],
            'Poland'                 : [0.90, 0.90],
            'Russia'                 : [0.80, 0.70],
            'Norway'                 : [0.80, 0.70],
            'Iceland'                : [0.80, 0.70],
            'Sweden'                 : [0.95],
            'Chile'                  : [0.90],
            'Denmark'                : [0.90],
            'Ecuador'                : [0.90],
            'United States & Canada' : [0.90],
            'Switzerland'            : [0.90],
            'Turkey'                 : [0.90],
            'Peru'                   : [0.90],
            }

    for country, level in to_test.items():
        for key, data in progress.processedleagues.items():
            if data.country == country:
                if data.levelnum - 1 < len(level) and not isinstance(level[data.levelnum - 1], tuple):
                    try:
                        have_percentage = data.totalCompleteTeams / float(data.getTotalNumTeams())
                    except ZeroDivisionError:
                        have_percentage = 0.0
                    level[data.levelnum - 1] = level[data.levelnum - 1], have_percentage

    OKGREEN = '\033[92m'
    ENDC = '\033[0m'
    FAIL = '\033[91m'

    for country, level in sorted(to_test.items()):
        for l, n in enumerate(level):
            if isinstance(n, tuple):
                if n[1] < n[0]:
                    color = FAIL
                    ps = ' (expected %d%%)' % int(n[0] * 100)
                else:
                    color = ENDC
                    ps = ''
                print >> sys.stderr, color + '%-30sLevel %d: %3d%% complete teams found%s.' % (
                        country, l + 1, int(n[1] * 100), ps)
            else:
                print >> sys.stderr, FAIL + '%-30sLevel %d: missing.' % (country, l + 1)

    print ENDC

def save():
    with open(Globals.progpath, 'wb') as f:
        pickle.dump(Globals.progress, f)

def load():
    with open(Globals.progpath, 'rb') as f:
        Globals.progress = pickle.load(f)

def cleanup():
    if Globals.didSomething:
        save()
    Globals.errlog.close()

if __name__ == '__main__':
    main()
