from lxml import etree

def addColorElement(parent, name, color):
    elem = etree.SubElement(parent, name)
    elem.set('r', str(color.r))
    elem.set('g', str(color.g))
    elem.set('b', str(color.b))

class Color:
    def __init__(self, r = 0, g = 0, b = 0):
        self.r = r
        self.g = g
        self.b = b

    def __str__(self):
        return '(%d, %d, %d)' % (self.r, self.g, self.b)

class Player:
    def __init__(self, name, number, pos, nationality):
        self.name = name
        self.number = number
        self.pos = pos
        self.nationality = nationality

class KitType:
    Plain = 0
    Stripes = 1
    Vertical = 2
    Hoops = 3
    Horizontal = 4
    Half = 5
    Sash = 6

class Kit:
    def __init__(self):
        self.bodytype = KitType.Plain
        self.bodycolor = Color()
        self.bodycolor2 = Color()
        self.shortscolor = Color()
        self.sockscolor = Color()

class Team:
    def __init__(self, name, kits, pos, players):
        self.name = name
        self.kits = kits
        self.pos = pos
        self.players = players

    def toXML(self):
        teamelem = etree.Element('Team')
        teamelem.set('name', self.name)
        if self.pos:
            teamelem.set('position', str(self.pos))
        for k in self.kits:
            kitelem = etree.SubElement(teamelem, 'Kit')
            kitelem.set('type', str(k.bodytype))
            addColorElement(kitelem, 'Body', k.bodycolor)
            addColorElement(kitelem, 'Body2', k.bodycolor2)
            addColorElement(kitelem, 'Shorts', k.shortscolor)
            addColorElement(kitelem, 'Socks', k.sockscolor)
        for p in self.players:
            playerelem = etree.SubElement(teamelem, 'Player')
            playerelem.set('name', p.name)
            playerelem.set('number', str(p.number))
            playerelem.set('pos', p.pos)
            playerelem.set('nationality', p.nationality)

        return teamelem

class LeagueData:
    def __init__(self, leaguetitle, promotionleague):
        self.title = leaguetitle
        self.season = None
        self.relegationleagues = None
        self.numteams = 0
        self.promotionleague = promotionleague
        self.levelnum = 0
        self.numPartialTeams = 0
        self.numCompleteTeams = 0

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        s =  u'LeagueData:\n'
        s += u'\tTitle: %s\n' % self.title
        s += u'\tSeason: %s\n' % self.season
        s += u'\tRelegation leagues: %s\n' % self.relegationleagues
        s += u'\tNumber of teams: %s\n' % self.numteams
        s += u'\tPromotion league: %s\n' % self.promotionleague
        s += u'\tLevel number: %s\n' % self.levelnum
        return s

