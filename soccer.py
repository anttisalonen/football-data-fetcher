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

# Not a group of leagues, but a parallel division
class LeagueGroup:
    def __init__(self, grouptitle, leaguetitle):
        self.title = grouptitle
        if self.title is None:
            self.title = ""
        self.leaguetitle = leaguetitle
        self.teams = []
        self.numPartialTeams = 0
        self.numCompleteTeams = 0

class LeagueData:
    def __init__(self, leaguetitle = '', promotionleague = '', confederation = '', country = '', toplevelleague = ''):
        self.title = leaguetitle
        self.groups = []
        self.season = ''
        self.relegationleagues = dict()
        self.promotionleague = promotionleague
        if not self.promotionleague:
            self.promotionleague = ''
        self.levelnum = 0
        self.divisions = 0
        self.numteams = 0
        self.confederation = confederation
        self.toplevelleague = toplevelleague
        self.country = country

    def getTotalCompleteTeams(self):
        return sum([group.numCompleteTeams for group in self.groups])

    def getTotalNumTeams(self):
        return self.numteams

    def hasTeams(self):
        for g in self.groups:
            if g.numPartialTeams or g.numCompleteTeams:
                return True
        return False

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        s =  u'LeagueData:\n'
        s += u'\tTitle: %s\n' % self.title
        s += u'\tSeason: %s\n' % self.season.decode('utf-8')
        s += u'\tRelegation leagues: %s\n' % self.relegationleagues
        s += u'\tNumber of teams: %s\n' % self.numteams
        s += u'\tPromotion league: %s\n' % self.promotionleague
        s += u'\tLevel number: %s\n' % self.levelnum
        s += u'\tDivisions: %s\n' % self.divisions
        return s

    def toXML(self):
        root = etree.Element("League")
        root.set('title', self.title)
        root.set('season', self.season)
        root.set('number_of_teams', str(self.numteams))
        root.set('promotion_league', self.promotionleague)
        root.set('level_number', str(self.levelnum))
        root.set('divisions', str(self.divisions if self.divisions else len(self.groups)))
        root.set('confederation', self.confederation)
        root.set('country', self.country)
        root.set('toplevel_league', self.toplevelleague)

        relegationLeagues = etree.SubElement(root, 'Relegation_Leagues')
        for l, l2 in self.relegationleagues.items():
            rl = etree.SubElement(relegationLeagues, 'League')
            rl.set('title', l)

        for g in self.groups:
            groupelem = etree.SubElement(root, 'Group')
            groupelem.set('title', g.title)
            for td in g.teams:
                teamelem = td.toXML()
                groupelem.append(teamelem)
        return root

