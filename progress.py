import soccer

class Progress:
    def __init__(self):
        self.leagues = dict()
        self.processedleagues = dict()

    def leagueProcessed(self, l):
        self.processedleagues[l.title] = l
        if l.title in self.leagues:
            del self.leagues[l.title]

    def printProcessedLeagues(self):
        s = u''
        for l, data in sorted(self.processedleagues.items()):
            s += u'%s' % data
        return s

    def printQueuedLeagues(self):
        s = u''
        s += u'Leagues in queue:\n'
        for t, n in sorted(self.leagues.items()):
            s += u'%-40s %-40s\n' % (t, n)
        return s

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        s = u''
        s += u'Progress: %d leagues in the queue, %d processed\n' % (len(self.leagues), len(self.processedleagues))
        if self.processedleagues:
            s += u'%40s    %5s %5s %5s %5s %5s %5s %5s\n' % ('League', '1', '2', '3', '4', '5', '6', '7')
            for l, data in sorted(self.processedleagues.items()):
                if data.levelnum == 1:
                    teaminfo = dict()
                    teaminfo[1] = [(data.numCompleteTeams, data.numteams)]
                    visitedDeps = set()
                    openDeps = set(data.relegationleagues.keys())
                    while True:
                        if not openDeps:
                            break
                        dep = openDeps.pop()
                        try:
                            rel = self.processedleagues[dep]
                        except KeyError:
                            pass
                        else:
                            newDeps = set(rel.relegationleagues.keys())
                            newDeps -= visitedDeps
                            if newDeps:
                                openDeps |= newDeps
                            if rel.levelnum not in teaminfo:
                                teaminfo[rel.levelnum] = [(rel.numCompleteTeams, rel.numteams)]
                            else:
                                teaminfo[rel.levelnum].append((rel.numCompleteTeams, rel.numteams))

                    s += u'%40s => ' % data.title
                    for i in xrange(1, 8):
                        if i not in teaminfo:
                            s += u'%5s ' % '-'
                        else:
                            if len(teaminfo[i]) == 1:
                                stats = list(teaminfo[i][0])
                                if not stats[0]:
                                    stats[0] = 0
                                if not stats[1]:
                                    stats[1] = 0
                                s += u'%2d/%2d ' % (stats[0], stats[1])
                            else:
                                s += u'%4dL ' % len(teaminfo[i])
                    s += u'\n'

        return s


