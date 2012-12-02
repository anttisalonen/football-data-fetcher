#!/usr/bin/env python2
# coding: utf-8

from lxml import etree

import re
import sys
import os, errno
import json
import cPickle as pickle

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

def usage():
    print 'Usage: %s [--help] [-l] [league to fetch]' % sys.argv[0]
    print '\nFetches soccer league, team and player data from Wikipedia and'
    print 'stores the result in $HOME/.football_data_fetcher.\n'
    print '\t-l\tOnly fetch league structure (no XML created)'

def main():
    specificLeague = None
    for arg in sys.argv[1:]:
        if arg == '-h' or arg == '--help':
            usage()
            sys.exit(0)
        elif arg == '-l':
            Globals.fetchTeams = False
        else:
            specificLeague = arg.decode('utf-8')
            Globals.dumpTextFiles = True
    try:
        fetchLeagueData(specificLeague)
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
