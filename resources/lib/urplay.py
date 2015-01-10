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
import xbmcgui
import xbmcplugin
import json
import re

from interface import *
from util import Logger, safeListGet
import parsedom
parseDOM = parsedom.parseDOM
stripTags = parsedom.stripTags
replaceHTMLCodes = parsedom.replaceHTMLCodes

log = Logger()

# Monkeypatch parsedom to use our debugging system.
# Note that enabling parseDOM debug bloat the log file.
__DEBUG_PARSEDOM__ = False
def pLog(dsc, lvl):
    if __DEBUG_PARSEDOM__: log.debug(dsc)
parsedom.log = pLog

class StaticDir(Directory):
    _items = []
    def _fetch(self):
        log.debug('Printing the {0} page.'.format(type(self).__name__))
        for langCode, path in self._items:
            url = self._plugin.urlRootStr + path
            li = xbmcgui.ListItem(iconImage='DefaultFolder.png')
            li.setLabel(self._plugin.localize(langCode))
            yield url, li, True

class Index(StaticDir):
    _items = [
        # (30100, '/Start'),
        (30101, '/Mest-spelade'),
        (30102, '/Mest-delade'),
        (30103, '/Senaste'),
        (30104, '/Sista-chansen'),
        (30105, '/Kategorier'),
        (30106, '/Aktuellt'),
        (30107, '/A-O')
    ]

class Categories(StaticDir):
    _items = [
        (30200, '/Kategorier/Dokumentar'),
        (30201, '/Kategorier/Forelasningar-debatt'),
        (30202, '/Kategorier/Vetenskap'),
        (30203, '/Kategorier/Kultur-historia'),
        (30204, '/Kategorier/Samhalle'),
        (30205, '/Kategorier/Sprak'),
        (30206, '/Kategorier/Barn')
    ]

class URPlay(BaseHandler, WebEnabled):
    url = URL('http://urplay.se')

    def __init__(self, plugin, path):
        self.url += path
        super(URPlay, self).__init__(plugin, path)

class URPlayDirectory(URPlay, Directory):
    pass

class SubCategories(URPlayDirectory):
    def __init__(self, plugin, path):
        path.url = path.url[11:]
        super(SubCategories, self).__init__(plugin, path)

    def _fetch(self):
        if self.html:
            categories = parseDOM(self.html, 'ul', attrs = {'id': 'underkategori'})
            if categories:
                subCategories = re.findall(r'<a href="([^"]+?)">(.+?)</a>', categories[0])
                for href, name in subCategories:
                    li = xbmcgui.ListItem(iconImage='DefaultFolder.png')
                    li.setLabel(replaceHTMLCodes(name))
                    url = self._plugin.urlRootStr + href

                    yield url, li, True
            # In case no sub-categories are found, place a link to list videos for all topics.
            else:
                log.warning('No sub-categories found.')
                li = xbmcgui.ListItem(iconImage='DefaultFolder.png')
                li.setLabel(self._plugin.localize(30303))
                url = self._plugin.urlRootStr + unicode(self._path)
                yield url, li, True

class AllProgrammes(URPlayDirectory):
    def _fetch(self):
        if self.html:
            section = parseDOM(self.html, 'section', attrs = {'id': 'alphabet'})
            if section:
                programmes = re.findall(r'<a title="Visa TV-serien: ([^"]+?)" href="([^"]+?)">', section[0])
                for title, href in programmes:
                    li = xbmcgui.ListItem(title, iconImage='DefaultFolder.png')
                    # Add a path step to the url because otherwise we can't distinguish between a series,
                    # which is a collection of videos, or a single video to play.
                    url = self._plugin.urlRootStr + '/Series' + href

                    yield url, li, True

class CurrentShows(URPlayDirectory):
    def _fetch(self):
        if self.html:
            headings = parseDOM(self.html, 'div', attrs = {'class': 'list subject'})
            for heading in headings:
                li = xbmcgui.ListItem(iconImage='DefaultFolder.png')
                try:
                    label = parseDOM(heading, 'h2')[0]
                    plot = parseDOM(heading, 'p')[0]
                    url = self._plugin.urlRootStr + parseDOM(heading, 'a',
                        attrs = {'class': r'button[\d]?'}, ret = 'href')[0]
                except IndexError as e:
                    log.debug('Exception, ({0}), for heading: {1}'.format(e, heading))
                    # Skip this item since we didn't manage to collect
                    # all the essential information.
                    log.warning('Did not manage to decode a heading in current shows. Skip to next.')
                    continue

                li.setLabel(label)
                li.setInfo('Video', {'plot' : plot})

                yield url, li, True

class Videos(URPlayDirectory):
    url = URL('', product_type = 'programtv')

    def _fetch(self):
        if self.html:
            videos = parseDOM(self.html, 'section', attrs = {'class': 'tv'})
            for video in videos:
                li = xbmcgui.ListItem(iconImage='DefaultVideo.png')
                try:
                    url = self._plugin.urlRootStr + parseDOM(video, 'a', ret = 'href')[0]
                    videoInfo = parseDOM(video, 'a')[0]

                    # It seems that there is a javascript that updates the thumbnail image link
                    # to a high resolution one based on your screen size. Therefore we need to manually
                    # update each thumbnail link.
                    thumb = parseDOM(videoInfo, 'img', ret = 'src')[0].replace('1_t.jpg', '1_l.jpg', 1)

                    # Fetch video title and check if the video is part of a series.
                    title = parseDOM(videoInfo, 'h1')[0]
                    seriesTitle = stripTags(parseDOM(videoInfo, 'h2')[0]).replace('TV. ', '', 1)
                    label = title
                    if title != seriesTitle:
                        label = '{0} - {1}'.format(seriesTitle, title)
                except IndexError as e:
                    log.debug('Exception, ({0}), for video: {1}'.format(e, video))
                    # Skip this item since we didn't manage to collect
                    # all the essential information.
                    log.warning('Did not manage to decode a video listing. Skip to next.')
                    continue

                li.setThumbnailImage(thumb)
                li.setLabel(label)
                li.setProperty('IsPlayable', 'true');

                info = {}
                info['aired'] = safeListGet(parseDOM(videoInfo, 'time', ret = 'datetime'), 0, '')[:10]
                aired = ''
                if info['aired']:
                    aired = '{0}: {1}.\n'.format(self._plugin.localize(30300), info['aired'])

                noPlot = '- ' + self._plugin.localize(30302) + ' -'
                plot = safeListGet(parseDOM(videoInfo, 'p'), 0, noPlot)
                info['plot'] = aired + (plot or noPlot)

                info['duration'] = self.convertDuration(safeListGet(parseDOM(videoInfo, 'dd'), 0, ''))
                info['title'] = title
                info['tvshowtitle'] = seriesTitle
                li.setInfo('Video', info)

                yield url, li, False

            # Add a 'next page' item if pagination is available.
            nav = parseDOM(self.html, 'nav', attrs = {'class': 'pagination'})
            if nav:
                log.debug('Found nav item on page!')
                pages = re.findall(r'<a href=".*>(\d+)</a>', nav[0])
                if pages:
                    log.debug('Found the list of pages: ' + repr(pages))
                    try:
                        totalpages = int(pages[-1])
                        page = int(self._path.args.get('page', 1))
                    except ValueError:
                        log.error('Unable to convert "{0}" & "{1}" into integer.').format(pages[-1],
                            self._path.args.get('page'))
                    else:
                        if page < totalpages:
                            url = self._plugin.urlRootStr + unicode(URL(self._path, page = page + 1))
                            txt = self._plugin.localize(30301)
                            label = '{0}... ({1}/{2})'.format(txt, page, totalpages)

                            li = xbmcgui.ListItem(label, iconImage='DefaultFolder.png')
                            log.debug('Adding pagination ({0}/{1}) to: "{2}".'.format(page, totalpages, url))

                            yield url, li, True

    _durationRegex = re.compile(r'^(?:(\d+):)?([0-5]?[0-9]):([0-5]?[0-9])$')
    def convertDuration(self, dur):
        # UR Play format is h:mm:ss. Kodi want duration in minutes only.
        match = self._durationRegex.match(dur)
        if match:
            h, m, s = map(float, match.groups('0'))
            return unicode(int(round(h*60 + m + s/60)))
        return '0'

class Series(Videos):
    def __init__(self, plugin, path):
        # UR Play has the same path for both single video items
        # and a collection of videos of a series. Therefore we added a
        # path ("/Series") in the A-O handler above. Before we can fetch the
        # real URL we need to remove this part from the path received in the
        # constructor. That is done with the slice below.
        path.url = path.url[7:]
        super(Series, self).__init__(plugin, path)

class Video(URPlay):
    def process(self):
        try:
            match = re.search(r'urPlayer\.init\((.*?)\);', self.html)
            if match is None:
                raise IOError('No JSON data found on webpage')

            js = json.loads(match.group(1))

            # Determine which video stream to choose.
            # The force subtitles one, 'file_html5', has "burned in" subtitles.
            # This is a workaround until proper subtitle support is added.
            hd = self._plugin.getSetting('hd_quality')
            forceSub = self._plugin.getSetting('force_subtitles')
            fl = js['file_hd'] or js['file_flash']
            if hd and forceSub:
                fl = js['file_html5_hd'] or js['file_html5']
                fl = fl.split('urplay/_definst_/mp4:')[-1]
            elif forceSub:
                fl = js['file_html5'].split('urplay/_definst_/mp4:')[-1]
            elif not hd:
                fl = js['file_flash']

            streamURL = 'http://{streaming_config[streamer][redirect]}/'\
                    'urplay/_definst_/mp4:{vid_file}/'\
                    '{streaming_config[http_streaming][hls_file]}'.format(vid_file = fl, **js)
            li = xbmcgui.ListItem(path = streamURL)

        except (IOError, ValueError, KeyError) as e:
            log.error('Unable to decode video information ({1}).'.format(e))
            xbmcplugin.setResolvedUrl(self._plugin.handle, False, xbmcgui.ListItem())
        else:
            log.debug('Playing video from URL: "{0}"'.format(streamURL))
            xbmcplugin.setResolvedUrl(self._plugin.handle, True, li)

        # TODO: Subtitles!