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
__plugin__.localize = lambda s: __addon__.getLocalizedString(s).encode('utf-8', 'ignore')
__plugin__.baseURL = 'plugin://{0}'.format(__addon__.getAddonInfo('id'))
__plugin__.url = sys.argv[0]
__plugin__.args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(__plugin__.handle, 'tvshows')

# Setup the logger before any modules that might use it are imported.
log = util.Logger(xbmc.log,
        name = __plugin__.name + ' v' + __plugin__.version,
        lvlDeb = xbmc.LOGDEBUG,
        lvlInfo = xbmc.LOGINFO,
        lvlWarn = xbmc.LOGWARNING,
        lvlErr = xbmc.LOGERROR)
log.info('Plugin started!')
log.debug('Plugin base URL: ' + __plugin__.baseURL)

import resources.lib.dispatcher as dp
import resources.lib.urplay as ur

# Associate the plugin URLs to respective handler.
app = dp.Dispatcher(__plugin__, [
    (r'/?', ur.Index),
    (r'/category', ur.Categories),
    (r'/category/([a-zA-Z0-9_\-.~]+)', ur.VideoCollection),
    (r'/programmes', ur.ProgrammesAToZ),
    (r'/series/([a-zA-Z0-9_\-.~]+)', ur.Series),
    (r'/current', ur.CurrentShows),
    (r'/current/([a-zA-Z0-9_\-.~]+)', ur.CurrentVideos),
    (r'/video/([a-zA-Z0-9_\-.~]+)', ur.Video)
])

# Run the addon application.
log.debug('Dispatching URL: ' + __plugin__.url)
app.dispatch(__plugin__.url)