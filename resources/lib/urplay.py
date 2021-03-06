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
import xbmc
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

class ExcAwareHandler(BaseHandler):
    def execute(self):
        try:
            self._execute()
         # If a serius error occured notify the user via a dialog.
        except HandlingError, e:
            log.error('Exception during handling of "{0}" ({1}).'.format(self._path, e))
            # The message code can be an integer or a tuple of multiple codes. The dialog
            # only has three text lines so slice the tuple before calling xbmc dialog.
            if e.notifyUsr:
                msg = e.msgCode
                if isinstance(msg, int):
                    msg = (msg,)
                msg = map(self._plugin.localize, msg[:3])
                xbmcgui.Dialog().ok(self._plugin.name, *msg)

    def _execute(self):
        raise NotImplementedError

class DirectoryEmptyError(HandlingError):
    pass

class Directory(ExcAwareHandler):

    def _fetchItems(self):
        raise NotImplementedError

    def _execute(self):
        log.debug('Start updating folder for "{0}".'.format(self._path))
        try:
            # Apparently xbmcplugin.addDirectoryItems() does not work with generators.
            # It expects a list, so call list() on the generator object.
            itemlist = list(self._fetchItems())
            xbmcplugin.addDirectoryItems(self._plugin.handle, itemlist)

            xbmcplugin.endOfDirectory(self._plugin.handle)
            log.debug('Done updating folder for "{0}".'.format(self._path))
            # If no items found raise en error so other classes may react if
            # they wish. It will get caught and logged in parent class, but we do not
            # notify the user. Since we already ended the directory with success the user
            # will see an empty folder.
            if not itemlist:
                raise DirectoryEmptyError('No items retrieved for path: '.format(self._path), False)

        # Tell Kodi that we didn't manage to fetch the directory successfully.
        except ItemFetchError, e:
            xbmcplugin.endOfDirectory(self._plugin.handle, succeeded = False)
            raise

class StaticDir(Directory):
    _items = []
    def _fetchItems(self):
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
        (30107, '/A-O'),
        (30108, '/Search')
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

class URPlay(ExcAwareHandler, WebEnabled):
    url = URL('http://urplay.se')

    def __init__(self, plugin, path):
        self.url += path
        super(URPlay, self).__init__(plugin, path)

class ItemFetchError(HandlingError):
    pass

class URPlayDirectory(URPlay, Directory):
    def _listItemGenerator(self):
        raise NotImplementedError

    def _fetchItems(self):
        try:
            self.fetchHTML()
        except ConnectionError, e:
            raise ItemFetchError(e, True, (30401, 30400))
        else:
            return self._listItemGenerator()

class AllProgrammes(URPlayDirectory):
    def _listItemGenerator(self):
        section = parseDOM(self.html, 'section', attrs = {'id': 'alphabet'})
        if section:
            programmes = re.findall(r'<a title="Visa TV-serien: ([^"]+?)" href="([^"]+?)">', section[0])
            for title, href in programmes:
                li = xbmcgui.ListItem(title, iconImage='DefaultFolder.png')
                # Add a path step to the url because otherwise we can't distinguish between a series,
                # which is a collection of videos, or a single video to play.
                url = self._plugin.urlRootStr + '/Serie' + href

                yield url, li, True

class CurrentShows(URPlayDirectory):
    def _listItemGenerator(self):
        headers = parseDOM(self.html, 'div', attrs = {'class': 'list subject'})
        for header in headers:
            li = xbmcgui.ListItem(iconImage='DefaultFolder.png')
            try:
                label = parseDOM(header, 'h2')[0]
                plot = parseDOM(header, 'p')[0]
                url = self._plugin.urlRootStr + parseDOM(header, 'a',
                    attrs = {'class': r'button[\d]?'}, ret = 'href')[0]
            except IndexError as e:
                log.debug('Exception, ({0}), for header: {1}'.format(e, header))
                # Skip this item since we didn't manage to collect
                # all the essential information.
                log.warning('Did not manage to decode a header in current shows. Skip to next.')
                continue

            li.setLabel(label)
            li.setInfo('Video', {'plot' : plot})

            yield url, li, True

class Videos(URPlayDirectory):
    url = URL('', product_type = 'programtv')

    def _listItemGenerator(self):
        videos = parseDOM(self.html, 'section', attrs = {'class': r'tv|series'})
        for video in videos:
            li = xbmcgui.ListItem(iconImage='DefaultVideo.png')
            try:
                videoInfo = parseDOM(video, 'a')[0]

                # It seems that there is a javascript that updates the thumbnail image link
                # to a high resolution one based on your screen size. Therefore we need to manually
                # update each thumbnail link.
                thumb = parseDOM(videoInfo, 'img', ret = 'src')[0].replace('1_t.jpg', '1_l.jpg', 1)

                # Fetch video title and check if the video is part of a series.
                title = replaceHTMLCodes(parseDOM(videoInfo, 'h1')[0])
                h2 = parseDOM(videoInfo, 'h2')
                prodType = parseDOM(h2, 'span', attrs = {'class': 'product-type'})[0]
                isSeries = prodType.startswith('Serie')

                # Fix url, since otherwise a series has the same url as a single video.
                url = parseDOM(video, 'a', ret = 'href')[0]
                if isSeries:
                    url = '/Serie' + url
                url = self._plugin.urlRootStr + url

                # Format the series title and construct the list item label.
                seriesTitle = stripTags(h2[0]).replace(prodType, '', 1).strip()
                label = title
                if not isSeries and (title != seriesTitle):
                    label = '{0} - {1}'.format(seriesTitle, title)
                elif isSeries:
                    label = self._plugin.localize(30303) + ': ' + title
            except IndexError as e:
                log.debug('Exception, ({0}), for video: {1}'.format(e, video))
                # Skip this item since we didn't manage to collect
                # all the essential information.
                log.warning('Did not manage to decode a video listing. Skip to next.')
                continue

            li.setThumbnailImage(thumb)
            li.setLabel(label)
            li.setProperty('IsPlayable', 'false' if isSeries else 'true');

            # Try to assemble video listing details.
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

            yield url, li, isSeries # If this item is a series, it should be a folder.

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
        path.url = path.url[6:]
        super(Series, self).__init__(plugin, path)

class SubCategories(Videos):
    def __init__(self, plugin, path):
        path.url = path.url[11:]
        super(SubCategories, self).__init__(plugin, path)

    def _listItemGenerator(self):
        # List item generator for sub-categories.
        def liGenerator(cat):
            for href, name in cat:
                li = xbmcgui.ListItem(iconImage='DefaultFolder.png')
                li.setLabel(replaceHTMLCodes(name))
                url = self._plugin.urlRootStr + replaceHTMLCodes(href)
                yield url, li, True

        # Search html for sub-categories.
        categories = parseDOM(self.html, 'ul', attrs = {'id': 'underkategori'})
        subCategories = None
        if categories:
            subCategories = re.findall(r'<a href="([^"]+?)">(.+?)</a>', categories[0])

        # Return the appropriate generator object. In the case no sub-categories are found,
        # fall-back by trying to list all videos instead. This works, because the page already
        # lists all videos if no sub-category in query, i.e. same as the sub-category "All Topics".
        if subCategories:
            return liGenerator(subCategories)
        else:
            log.warning('No sub-categories found. Trying to list videos from {0}.'.format(unicode(self.url)))
            return super(SubCategories, self)._listItemGenerator()

class Search(Videos):
    def __init__(self, plugin, path):
        super(Search, self).__init__(plugin, URL('/Produkter'))

    def _execute(self):
        try:
            super(Search, self)._execute()
        except DirectoryEmptyError, e:
            e.msgCode = 30403 # No search results.
            e.notifyUsr = True
            raise

    def _fetchItems(self):
        hdr = self._plugin.name + ': ' + self._plugin.localize(30108)
        kb = xbmc.Keyboard(heading = hdr)
        kb.doModal()
        if kb.isConfirmed():
            ss = kb.getText().decode('utf-8')
            log.debug('Got search string: "{0}".'.format(ss))
            # Return videos for search URL.
            self.url.args['q'] = ss
            return super(Search, self)._fetchItems()
        else:
            raise ItemFetchError('User cancelled search.', False)


class StreamURLError(HandlingError):
    pass

class Video(URPlay):
    def _execute(self):
        try:
            self.fetchHTML()
            match = re.search(r'urPlayer\.init\((.*?)\);', self.html)
            if match is None:
                raise IOError('No JSON data found on webpage')

            js = json.loads(match.group(1))

            # Determine which video stream to choose.
            # The force subtitles one, 'file_html5', has "burned in" subtitles.
            # This is a workaround until proper subtitle support is added.
            hd = self._plugin.getSetting('hd_quality')
            forceSub = self._plugin.getSetting('force_subtitles')
            fl =  js['file_http_hd'] or js['file_http']
            if hd and forceSub:
                fl = js['file_http_sub_hd'] or js['file_http_sub']
                # fl = fl.split('urplay/_definst_/mp4:')[-1]
            elif forceSub:
                fl = js['file_http_sub']#.split('urplay/_definst_/mp4:')[-1]
            elif not hd:
                fl = js['file_http']

            streamURL = 'http://{streaming_config[streamer][redirect]}/{vid_file}/'\
                    '{streaming_config[http_streaming][hls_file]}'.format(vid_file = fl, **js)
            li = xbmcgui.ListItem(path = streamURL)

        except (ConnectionError, IOError, ValueError, KeyError), e:
            log.error('Unable to decode video information ({0}).'.format(e))
            # Tell Kodi we didn't resolved the url.
            xbmcplugin.setResolvedUrl(self._plugin.handle, False, xbmcgui.ListItem())
            raise StreamURLError(e, True, (30402, 30400))
        else:
            log.debug('Playing video from URL: "{0}"'.format(streamURL))
            xbmcplugin.setResolvedUrl(self._plugin.handle, True, li)

        # TODO: Subtitles!