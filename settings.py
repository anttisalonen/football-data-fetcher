import utils
from progress import Progress
import time
import os

class Globals:
    appname = "football_data_fetcher"
    progress = Progress()
    didSomething = False
    dumpTextFiles = False
    fetchTeams = True
    progpath = None

    @staticmethod
    def setDataDir(dd):
        if Globals.progpath:
            raise RuntimeError('Data directory already set!')
        if not dd:
            datadir = time.strftime("output_%Y-%m-%d-%H-%M", time.localtime())
        else:
            datadir = str(dd)
        Globals.outputdir = datadir + '/output/'
        if os.path.exists(Globals.outputdir):
            print 'Using existing directory "%s" as output directory.' % datadir
        else:
            print 'Creating new directory "%s" as output directory.' % datadir
        utils.mkdir_p(Globals.outputdir)
        Globals.errlog = open(datadir + '/error.log', 'a')
        Globals.progpath = datadir + '/progress.save'

