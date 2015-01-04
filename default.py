# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import re

import resources.lib.util as util

# Add-on info.
proc_handle = int(sys.argv[1])

xbmcplugin.setContent(proc_handle, 'tvshows')
__addon__ = xbmcaddon.Addon()
__localize__ = __addon__.getLocalizedString

# Setup the logger before any modules that might use it are imported.
log = util.Logger(xbmc.log,
        name = __addon__.getAddonInfo('name') + ' v' + __addon__.getAddonInfo('version'),
        lvlDeb = xbmc.LOGDEBUG,
        lvlInfo = xbmc.LOGINFO,
        lvlWarn = xbmc.LOGWARNING,
        lvlErr = xbmc.LOGERROR)
log.info('Plugin started!')

import resources.lib.dispatcher as dp
import resources.lib.urplay as ur

baseURL = 'plugin://{0}'.format(__addon__.getAddonInfo('id'))
log.debug('Plugin base URL: ' + baseURL)

# Associate the plugin URL to respective handler.
app = dp.Dispatcher(baseURL, [
    (r'/', ur.Index),
    (r'/kategori', ur.Categories),
    (r'/kategori/([a-zA-Z0-9_\-.~]+)', ur.Videos),
    (r'/a-to-o', ur.AToO),
    (r'/video/([a-zA-Z0-9_\-.~]+)', ur.PlayVideo)
])

# Run the addon application.
url = sys.argv[0]
log.debug('Dispatching URL: ' + url)
app.dispatch(url)