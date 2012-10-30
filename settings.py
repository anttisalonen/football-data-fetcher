import utils
from progress import Progress

class Globals:
    appname = "football_data_fetcher"
    datadir = utils.getAppDataDir(appname) + '/'
    progress = Progress()
    outputdir = datadir + 'output/'
    utils.mkdir_p(outputdir)
    errlog = open(datadir + 'error.log', 'a')
    progpath = datadir + 'progress.save'
    didSomething = False
    dumpTextFiles = False


