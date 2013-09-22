import re

import wikiutils
import soccer
from settings import Globals

def unlink_wiki(line):
    if '[[' in line:
        l1, l2 = line.split('[[', 1)
        if ']]' not in l2:
            # wiki syntax error
            return l1 + l2
        else:
            l3, l4 = l2.split(']]', 1)
            if '|' in l3:
                l3 = l3.split('|', 1)[1]
            return l1 + l3 + unlink_wiki(l4)
    else:
        return line

def fetchPlayer(line):
    def playerError(msg):
        print >> Globals.errlog, "Player %s: %s" % (line.encode('utf-8'), msg.encode('utf-8'))

    lineWithoutSpaces = ''.join(line.split())
    ll = line.lower()
    if '{{fs player' in ll or \
            '{{football squad player' in ll or \
            '{{fs2 player' in ll:
        unlinkedline = unlink_wiki(line)

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


