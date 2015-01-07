# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcplugin
import xbmcaddon
import urlparse

import resources.lib.util as util

# Add-on info.
class Plugin:
    pass
__plugin__ = Plugin()
__addon__ = xbmcaddon.Addon()

__plugin__.handle = int(sys.argv[1])
__plugin__.name = __addon__.getAddonInfo('name')
__plugin__.version = __addon__.getAddonInfo('version')
__plugin__.localize = lambda s: __addon__.getLocalizedString(s).encode('utf-8')
__plugin__.urlRootStr = 'plugin://{0}'.format(__addon__.getAddonInfo('id'))
__plugin__.path = util.URL(sys.argv[0].split(__plugin__.urlRootStr)[-1],
                           **dict(urlparse.parse_qsl(sys.argv[2][1:])))

xbmcplugin.setContent(__plugin__.handle, 'tvshows')

# Setup the logger before any modules that might use it are imported.
log = util.Logger(xbmc.log,
        name = __plugin__.name + ' v' + __plugin__.version,
        lvlDeb = xbmc.LOGDEBUG,
        lvlInfo = xbmc.LOGINFO,
        lvlWarn = xbmc.LOGWARNING,
        lvlErr = xbmc.LOGERROR)
log.info('Plugin started! Name: {0}. Handle: {1}.'.format(__plugin__.name, __plugin__.handle))
log.debug('Plugin base URL: ' + __plugin__.urlRootStr)

import resources.lib.dispatcher as dp
import resources.lib.urplay as ur

# Associate the plugin URLs to respective handler.
app = dp.Dispatcher(__plugin__, [
    (r'/?', ur.Index),
    (r'/Kategorier', ur.Categories),
    (r'/A-O', ur.AllProgrammes),
    (r'/Aktuellt', ur.CurrentShows),
    (r'/Aktuellt/[^/]+', ur.Videos),
    (r'/Series/.+', ur.Series),
    (r'/Produkter/[^/]+', ur.Video),
    (r'/(?:[^/]+/)*(?:[^/]+)?', ur.Videos)
])

# Run the addon application.
log.debug('Dispatching path: ' + str(__plugin__.path))
app.dispatch(__plugin__.path)