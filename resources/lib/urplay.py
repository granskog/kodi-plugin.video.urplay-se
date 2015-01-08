# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import xbmcgui
import xbmcplugin
import json
import re

from interface import *
from util import Logger, safeListGet
from parsedom import parseDOM, stripTags

log = Logger()

# Monkeypatch parsedom to use our debugging system.
# Note that printing debug to xbmc seriously bloat the log file
# and slow things down.
import parsedom
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
        (30200, '/Dokumentar'),
        (30201, '/Forelasningar-debatt'),
        (30202, '/Vetenskap'),
        (30203, '/Kultur-historia'),
        (30204, '/Samhalle'),
        (30205, '/Sprak'),
        (30206, '/Barn')
    ]

class URPlay(BaseHandler, WebEnabled):
    url = URL('http://urplay.se')

    def __init__(self, plugin, path):
        self.url += path
        super(URPlay, self).__init__(plugin, path)

class URPlayDirectory(URPlay, Directory):
    pass

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
            videos = parseDOM(self.html, "section", attrs = {'class': 'tv'})
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
                        label = u'{0} - {1}'.format(seriesTitle, title)
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

                noPlot = '-'+self._plugin.localize(30302)+'-'
                plot = safeListGet(parseDOM(videoInfo, 'p'), 0,noPlot)
                info['plot'] = aired + (plot or noPlot)

                info['duration'] = self.convertDuration(safeListGet(parseDOM(videoInfo, 'dd'), 0, ''))
                info['title'] = title
                info['tvshowtitle'] = seriesTitle
                li.setInfo('Video', info)

                yield url, li, False

            # Add a 'next page' item if pagination is available.
            nav = parseDOM(self.html, "nav", attrs = {"class": "pagination"})
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
                            url = self._plugin.urlRootStr + str(URL(self._path, page = page + 1))
                            txt = self._plugin.localize(30301)
                            label = '{0}... ({1}/{2})'.format(txt, page, totalpages)

                            li = xbmcgui.ListItem(iconImage='DefaultFolder.png')
                            li.setLabel(label)
                            log.debug('Adding pagination ({0}/{1}) to: "{2}".'.format(page, totalpages, url))

                            yield url, li, True

    _durationRegex = re.compile(r'^(?:(\d+):)?([0-5]?[0-9]):([0-5]?[0-9])$')
    def convertDuration(self, dur):
        # UR Play format is h:mm:ss. Kodi want duration in minutes only.
        match = self._durationRegex.match(dur)
        if match:
            h, m, s = map(float, match.groups('0'))
            return str(int(round(h*60 + m + s/60)))
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
            fl = js['file_hd'] if js['file_hd'] != '' else js['file_flash']
            vidURL = 'http://{streaming_config[streamer][redirect]}/'\
                    'urplay/_definst_/mp4:{vid_file}/'\
                    '{streaming_config[http_streaming][hls_file]}'.format(vid_file = fl, **js)
            li = xbmcgui.ListItem(path = vidURL)

        except (IOError, ValueError, KeyError) as e:
            log.error('Unable to decode video information ({1}).'.format(e))
            xbmcplugin.setResolvedUrl(self._plugin.handle, False, xbmcgui.ListItem())
        else:
            log.debug('Playing video from URL: "{0}"'.format(vidURL))
            xbmcplugin.setResolvedUrl(self._plugin.handle, True, li)

        # TODO: Subtitles!