# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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
__plugin__.name = __addon__.getAddonInfo('name').decode('utf-8')
__plugin__.version = __addon__.getAddonInfo('version').decode('utf-8')
__plugin__.localize = lambda s: __addon__.getLocalizedString(s)
__plugin__.getSetting = lambda s: __addon__.getSetting(s) == 'true'
__plugin__.urlRootStr = 'plugin://{0}'.format(__addon__.getAddonInfo('id').decode('utf-8'))

__path__ = util.URL(sys.argv[0].split(__plugin__.urlRootStr)[-1],
                **dict(urlparse.parse_qsl(sys.argv[2][1:])))

xbmcplugin.setContent(__plugin__.handle, 'tvshows')

# Setup the logger before any modules that might use it are imported.
# Kodi logging does not support Unicode, so encode to UTF-8.
log = util.Logger(lambda m, l: xbmc.log(m.encode('utf-8'), l),
        name = __plugin__.name + ' v' + __plugin__.version,
        lvlDeb = xbmc.LOGDEBUG,
        lvlInfo = xbmc.LOGINFO,
        lvlWarn = xbmc.LOGWARNING,
        lvlErr = xbmc.LOGERROR)

log.info('Plugin started with handle: {0}. Python version: {1}.'.format(__plugin__.handle,
    sys.version.replace('\n', '')))

import resources.lib.dispatcher as dp
import resources.lib.urplay as ur

# Associate the plugin URLs to respective handler.
app = dp.Dispatcher(__plugin__, [
    (r'/?', ur.Index),
    (r'/Kategorier', ur.Categories),
    (r'/A-O', ur.AllProgrammes),
    (r'/Aktuellt', ur.CurrentShows),
    (r'/Series/.+', ur.Series),
    (r'/Produkter/[^/]+', ur.Video),
    (r'/(?:[^/]+/)*(?:[^/]+)?', ur.Videos)
])

# Run the addon application.
log.debug('Plugin base URL: ' + __plugin__.urlRootStr)
log.debug('Dispatching path: ' + unicode(__path__))
app.dispatch(__path__)