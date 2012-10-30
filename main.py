#!/usr/bin/env python2
# coding: utf-8

import re
import sys
import os, errno
import json
import cPickle as pickle

import utils
import parser
from settings import Globals
import wikiutils

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

    while len(Globals.progress.leagues) > 0:
        if specificLeague:
            found = None
            for k in Globals.progress.leagues.keys():
                if k.startswith(specificLeague):
                    found = k
            if found:
                leaguetitle = found
            else:
                print >> sys.stderr, "I don't have league '%s' queued. I just have these:\n\n" % specificLeague
                for l in sorted(Globals.progress.leagues.keys()):
                    print >> sys.stderr, '\t%s' % l
                print >> sys.stderr, '\n'
                return
        else:
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
        rvtext = wikiutils.getPage(leaguetitle)
        if rvtext:
            leaguedata = parser.getLeagueData(leaguetitle, promotionleague, rvtext)
            if leaguedata.season and leaguedata.numteams and leaguedata.levelnum:
                print 'proceed to current season.'
                stext = wikiutils.getPage(leaguedata.season, True)
                if stext:
                    numCompleteTeams, numPartialTeams = parser.handleSeason(stext, leaguedata)
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
        else:
            print 'No revision text for league.'

        Globals.didSomething = True
        if leaguedata:
            Globals.progress.leagueProcessed(leaguedata, numCompleteTeams, numPartialTeams, numFollowingLeagues)
        else:
            del Globals.progress.leagues[leaguetitle]

        save()

        if specificLeague:
            return

def usage():
    print 'Usage: %s [--help] [tests|league to fetch]' % sys.argv[0]

def main():
    specificLeague = None
    if len(sys.argv) > 1:
        if sys.argv[1] == '-h' or sys.argv[1] == '--help':
            usage()
            sys.exit(0)
        else:
            specificLeague = sys.argv[1].decode('utf-8')
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
            except Exception, e:
                print >> sys.stderr, "Error: couldn't save progress:", str(e)
                pass
    else:
        if Globals.didSomething:
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
    if Globals.didSomething:
        save()
    Globals.errlog.close()

if __name__ == '__main__':
    main()
