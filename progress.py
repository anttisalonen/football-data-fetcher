import soccer

class Progress:
    def __init__(self):
        self.leagues = dict()
        self.processedleagues = dict()

    def leagueProcessed(self, l, numCompleteTeams, numPartialTeams, numFollowingLeagues):
        self.processedleagues[l.title] = soccer.ProcessedLeague(l, numCompleteTeams, numPartialTeams, numFollowingLeagues)
        del self.leagues[l.title]

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        s = u''
        for l, data in sorted(self.processedleagues.items()):
            s += u'%s' % data
        s += u'Progress: %d leagues in the queue, %d processed\n' % (len(self.leagues), len(self.processedleagues))
        if self.processedleagues:
            s += u'%40s    %5s %5s %5s %5s %5s %5s %5s\n' % ('League', '1', '2', '3', '4', '5', '6', '7')
            for l, data in sorted(self.processedleagues.items()):
                if data.leaguedata.levelnum == 1:
                    teaminfo = dict()
                    teaminfo[1] = [(data.numCompleteTeams, data.leaguedata.numteams)]
                    visitedDeps = set()
                    openDeps = set(data.leaguedata.relegationleagues.keys())
                    while True:
                        if not openDeps:
                            break
                        dep = openDeps.pop()
                        try:
                            rel = self.processedleagues[dep]
                        except KeyError:
                            pass
                        else:
                            newDeps = set(rel.leaguedata.relegationleagues.keys())
                            newDeps -= visitedDeps
                            if newDeps:
                                openDeps |= newDeps
                            if rel.leaguedata.levelnum not in teaminfo:
                                teaminfo[rel.leaguedata.levelnum] = [(rel.numCompleteTeams, rel.leaguedata.numteams)]
                            else:
                                teaminfo[rel.leaguedata.levelnum].append((rel.numCompleteTeams, rel.leaguedata.numteams))

                    s += u'%40s => ' % data.leaguedata.title
                    for i in xrange(1, 8):
                        if i not in teaminfo:
                            s += u'%5s ' % '-'
                        else:
                            if len(teaminfo[i]) == 1:
                                stats = teaminfo[i][0]
                                s += u'%2d/%2d ' % (stats[0], stats[1])
                            else:
                                s += u'%4dL ' % len(teaminfo[i])
                    s += u'\n'

        if self.leagues:
            s += u'Leagues in queue:\n'
            for t, n in sorted(self.leagues.items()):
                s += u'%-40s %-40s\n' % (t, n)
        return s


