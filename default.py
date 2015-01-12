# -*- coding: utf-8 -*-

# This file is part of 'UR Play Video Plugin' for Kodi Media Player, henceforth 'this program'.
# Copyright (C) 2015 David Gran Skog
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
import sys
import xbmc
import xbmcplugin
import xbmcaddon
import urlparse

import resources.lib.util as util
import resources.lib.dispatcher as dp
import resources.lib.urplay as ur

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

# Setup the logger. Kodi logging does not support Unicode, so encode to UTF-8.
log = util.Logger()
log.setupLogger(lambda m, l: xbmc.log(m.encode('utf-8'), l),
        name = __plugin__.name + ' v' + __plugin__.version,
        lvlDeb = xbmc.LOGDEBUG,
        lvlInfo = xbmc.LOGINFO,
        lvlWarn = xbmc.LOGWARNING,
        lvlErr = xbmc.LOGERROR)

log.info('Plugin started with handle: {0}. Python version: {1}.'.format(__plugin__.handle,
    sys.version.replace('\n', '')))

# Associate the plugin URLs to respective handler.
app = dp.Dispatcher(__plugin__, [
    (r'/?', ur.Index),
    (r'/Kategorier', ur.Categories),
    (r'/Kategorier/[^/]+', ur.SubCategories),
    (r'/A-O', ur.AllProgrammes),
    (r'/Aktuellt', ur.CurrentShows),
    (r'/Search', ur.Search),
    (r'/Series/.+', ur.Series),
    (r'/Produkter/[^/]+', ur.Video),
    # All other URLs are interpreted as a path to a videos directory.
    (r'/(?:[^/]+/)*(?:[^/]+)?', ur.Videos)
])

# Run the addon application.
log.debug('Plugin base URL: ' + __plugin__.urlRootStr)
log.debug('Dispatching path: ' + unicode(__path__))
app.dispatch(__path__)