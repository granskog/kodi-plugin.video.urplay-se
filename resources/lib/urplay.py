# -*- coding: utf-8 -*-
import xbmcgui
import xbmcplugin
import json
import urllib2
import re

from util import Logger, URL, URLBuilder, safeListGet
from parsedom import parseDOM, stripTags
from parsedom import log as parsedomLog

log = Logger()
# "Patch" parsedom to use our debugging.
# Note that printing debug to xbmc seriously bloat
# the log file and slow things down. Use only when develop.
__DEBUG_PARSEDOM__ = False
def pLog(dsc, lvl):
    if __DEBUG_PARSEDOM__: log.debug(dsc)
parsedomLog = pLog

class BaseHandler(object):
    __metaclass__ = URLBuilder
    url = URL('http://urplay.se')
    _html = None

    def __init__(self, plugin):
        self._plugin = plugin

    @property
    def html(self):
        if not self._html:
            log.info('Fetching content from "{0}".'.format(self.url))
            request = urllib2.Request(str(self.url))
            response = urllib2.urlopen(request)
            self._html = response.read()
            log.debug('Received response, ok!')
        return self._html

    def process(self):
        pass

    def onException(self, e):
        if isinstance(e, (urllib2.URLError, urllib2.HTTPError)):
            log.error('Unable to fetch content from "{0}" ({1}).'.format(self.url, e))
            return True
        return False

class Directory(BaseHandler):
    def _fetch(self):
        return []

    def process(self):
        items = self._fetch()
        log.debug('Start updating folder for "{0}".'.format(self._plugin.url))
        # Unfortunately addDirectoryItems() does not work with generators.
        # It expect a list, so call list() on the generator object.
        xbmcplugin.addDirectoryItems(self._plugin.handle, list(items))
        xbmcplugin.endOfDirectory(self._plugin.handle)
        log.debug('Done updating folder for "{0}".'.format(self._plugin.url))

    def onException(self, e):
        xbmcplugin.endOfDirectory(self._plugin.handle, succeeded = False)
        return super(Directory, self).onException(e)

class StaticDir(Directory):
    _items = []
    def _fetch(self):
        log.debug('Printing the {0} page.'.format(type(self).__name__))
        for langCode, path in self._items:
            url = self._plugin.baseURL + path
            li = xbmcgui.ListItem(self._plugin.localize(langCode),
                iconImage='DefaultFolder.png')
            yield url, li, True

class Index(StaticDir):
    _items = [
        # (30100, '/startsida'),
        (30101, '/category/Mest-spelade'),
        (30102, '/category/Mest-delade'),
        (30103, '/category/Senaste'),
        (30104, '/category/Sista-chansen'),
        (30105, '/category'),
        (30106, '/current'),
        (30107, '/programmes')
    ]

class Categories(StaticDir):
    _items = [
        (30200, '/category/Dokumentar'),
        (30201, '/category/Forelasningar-debatt'),
        (30202, '/category/Vetenskap'),
        (30203, '/category/Kultur-historia'),
        (30204, '/category/Samhalle'),
        (30205, '/category/Sprak'),
        (30206, '/category/Barn')
    ]

class ProgrammesAToZ(StaticDir):
    _items = [
        (30100, '/')
    ]

class CurrentShows(StaticDir):
    _items = [
        (30100, '/')
    ]

class Videos(Directory):
    url = URL('/', product_type = 'programtv')
    def __init__(self, plugin, path):
        super(Videos, self).__init__(plugin)
        self.url.extend(path)

    def _fetch(self):
        videos = parseDOM(self.html, "section", attrs = {"class": "tv"})
        for video in videos:
            li = xbmcgui.ListItem(iconImage='DefaultVideo.png')
            url = '{0}/video/{1}'.format(self._plugin.baseURL,
                parseDOM(video, 'a', ret = 'id')[0])

            videoInfo = parseDOM(video, 'a')[0]
            li.setThumbnailImage(parseDOM(videoInfo, 'img', ret = 'src')[0].replace('1_t.jpg', '1_l.jpg', 1))

            # Fetch video title and check if the video is part of a series.
            title = parseDOM(videoInfo, 'h1')[0]
            seriesTitle = stripTags(parseDOM(videoInfo, 'h2')[0]).replace('TV. ', '', 1)
            label = title
            if title != seriesTitle:
                label = u'{0} - {1}'.format(seriesTitle, title)
            li.setLabel(label)

            info = {}
            info['aired'] = safeListGet(parseDOM(videoInfo, 'time', ret = 'datetime'), 0, '')[:10]
            info['duration'] = self.convertDuration(safeListGet(parseDOM(videoInfo, 'dd'), 0, ''))
            info['plot'] = '{0}: {1}.\n{2}'.format(self._plugin.localize(30300),
                info['aired'], parseDOM(videoInfo, 'p')[0].encode('utf-8'))
            info['title'] = title
            info['tvshowtitle'] = seriesTitle
            li.setInfo('Video', info)
            li.setProperty('IsPlayable', 'true');
            yield url, li, False

        # TODO Pagination!

    _cnvDurRegex = re.compile(r'^(?:(\d+):)?(\d{1,2}):(\d{1,2})$')
    def convertDuration(self, dur):
        # UR Play format is h:mm:ss. Kodi want duration in minutes only.
        match = self._cnvDurRegex.match(dur)
        if match:
            h, m, s = map(float, match.groups('0'))
            return str(int(round(h*60 + m + s/60)))
        return '0'

class CurrentVideos(Videos):
    url = URL('/Aktuellt/')

class Programmes(Videos):
    url = URL('/Produkter/')

class Video(BaseHandler):
    url = URL('/Produkter/')
    def __init__(self, plugin, id):
        super(Video, self).__init__(plugin)
        self._id = id
        self.url.extend(id)

    def process(self):
        match = re.search(r'urPlayer\.init\((.*?)\);', self.html)
        if match is None:
            raise IOError('No JSON data found on webpage')

        js = json.loads(match.group(1))
        fl = js['file_hd'] if js['file_hd'] != '' else js['file_flash']
        vidURL = 'http://{streaming_config[streamer][redirect]}/'\
                'urplay/_definst_/mp4:{vid_file}/'\
                '{streaming_config[http_streaming][hls_file]}'.format(vid_file = fl, **js)

        li = xbmcgui.ListItem(path = vidURL)
        log.debug('Playing video from URL: "{0}"'.format(vidURL))
        xbmcplugin.setResolvedUrl(self._plugin.handle, True, li)

        # TODO: Subtitles!

    def onException(self, e):
        xbmcplugin.setResolvedUrl(self._plugin.handle, False, xbmcgui.ListItem())
        if isinstance(e, (IOError, ValueError, KeyError)):
            # TODO: Notice user in gui!
            log.error('Unable to decode video information ({1}).'.format(e))
            return True
        return super(Video, self).onException(e)