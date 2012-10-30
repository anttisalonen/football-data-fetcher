import re

import wikiutils
import soccer
from settings import Globals

unlinker_re = re.compile(r'(.*)\[\[(.*)\|(.*)\]\](.*)')

def fetchPlayer(line):
    def playerError(msg):
        print >> Globals.errlog, "Player %s: %s" % (line.encode('utf-8'), msg.encode('utf-8'))

    lineWithoutSpaces = ''.join(line.split())
    ll = line.lower()
    if '{{fs player' in ll or \
            '{{football squad player' in ll or \
            '{{fs2 player' in ll:
        unlinkedline = line
        while True:
            res = unlinker_re.match(unlinkedline)
            if res:
                groups = res.groups()
                try:
                    unlinkedline = groups[0] + groups[2] + groups[3]
                except IndexError:
                    playerError(u"Couldn't find groups at %s" % groups)
                    break
            else:
                break

        columns = [s.strip() for s in unlinkedline.replace('{', '').replace('}', '').split('|')]
        number = None
        nationality = None
        pos = None
        name = None
        firstname = None
        lastname = None
        for column in columns:
            if '=' in column:
                try:
                    k, v = wikiutils.getKeyValue(column)
                except ValueError:
                    playerError("Couldn't parse player information column: %s" % column)
                    continue
                if k == 'no':
                    try:
                        number = int(v)
                    except (UnicodeEncodeError, ValueError):
                        pass # usually dash as a player number
                elif k == 'nat':
                    nationality = v
                elif k == 'pos':
                    pos = v
                elif k == 'name':
                    name = wikiutils.unlinkify(v)[0]
                elif k == 'first':
                    firstname = wikiutils.unlinkify(v)[0]
                elif k == 'last':
                    lastname = wikiutils.unlinkify(v)[0]

        if not name and firstname and lastname:
            name = firstname + ' ' + lastname

        if not number:
            number = 0

        if not nationality:
            nationality = 'NA'

        if nationality and pos and name:
            return soccer.Player(name, number, pos, nationality)

    return None

def endOfPlayerList(line):
    return '{{fs end}}' in line.lower() or '{[football squad end}}' in line.lower() or '{{football squad end2}}' in line.lower()

def fetchPlayers(text):
    players = []

    for line in text.split('\n'):
        p = fetchPlayer(line)
        if p:
            players.append(p)
        elif endOfPlayerList(line):
            break

    return players


