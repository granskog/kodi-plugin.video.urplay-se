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

# Monkeypatch parsedom to use our debugging system.
# Note that printing debug to xbmc seriously bloat the log file
# and slow things down.
__DEBUG_PARSEDOM__ = False
def pLog(dsc, lvl):
    if __DEBUG_PARSEDOM__: log.debug(dsc)
parsedomLog = pLog

class BaseHandler(object):
    __metaclass__ = URLBuilder
    
    url = URL('http://urplay.se')
    _html = None

    def __init__(self, plugin, path):
        self._plugin = plugin
        self.url += path

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
        log.debug('Start updating folder for "{0}".'.format(self._plugin.path))
        
        items = self._fetch()
        # Unfortunately addDirectoryItems() does not work with generators.
        # It expect a list, so call list() on the generator object.
        xbmcplugin.addDirectoryItems(self._plugin.handle, list(items))
        xbmcplugin.endOfDirectory(self._plugin.handle)

        log.debug('Done updating folder for "{0}".'.format(self._plugin.path))

    def onException(self, e):
        xbmcplugin.endOfDirectory(self._plugin.handle, succeeded = False)
        return super(Directory, self).onException(e)

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

class AllProgrammes(Directory):
    def _fetch(self):
        section = parseDOM(self.html, 'section', attrs = {'id': 'alphabet'})[0]
        programmes = re.findall(r'<a title="Visa TV-serien: ([^"]+?)" href="([^"]+?)">', section)
        for title, href in programmes:
            li = xbmcgui.ListItem(title, iconImage='DefaultFolder.png')
            # Add a path step to the url because otherwise we can't distinguish between a series,
            # which is a collection of videos, or a single video to play.
            url = self._plugin.urlRootStr + '/Series' + href
            yield url, li, True

class CurrentShows(Directory):
    def _fetch(self):
        headings = parseDOM(self.html, 'div', attrs = {'class': 'list subject'})
        for heading in headings:
            li = xbmcgui.ListItem(iconImage='DefaultFolder.png')
            li.setLabel(parseDOM(heading, 'h2')[0])
            li.setInfo('Video', {'plot' : parseDOM(heading, 'p')[0]})
            url = self._plugin.urlRootStr + parseDOM(heading, 'a',
                attrs = {'class': r'button[\d]?'}, ret = 'href')[0]
            yield url, li, True

class Videos(Directory):
    url = URL('', product_type = 'programtv')

    def _fetch(self):
        videos = parseDOM(self.html, "section", attrs = {'class': 'tv'})
        for video in videos:
            li = xbmcgui.ListItem(iconImage='DefaultVideo.png')
            url = self._plugin.urlRootStr + parseDOM(video, 'a', ret = 'href')[0]

            videoInfo = parseDOM(video, 'a')[0]
            # It seems that there is a javascript that updates the thumbnail image link
            # to a high resolution one based on your screen size. Therefore we need to manually
            # update each thumbnail link.
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

            aired = '' if not info['aired'] else '{0}: {1}.\n'.format(self._plugin.localize(30300),
                info['aired'])

            info['plot'] = aired + parseDOM(videoInfo, 'p')[0].encode('utf-8')
            info['title'] = title
            info['tvshowtitle'] = seriesTitle
            li.setInfo('Video', info)
            li.setProperty('IsPlayable', 'true');
            yield url, li, False

        # Add a 'next page' item if pagination is available.
        nav = parseDOM(self.html, "nav", attrs = {"class": "pagination"})
        if nav:
            log.debug('Found nav item on page!')
            pages = re.findall(r'<a href=".*>(\d+)</a>', nav[0])
            if pages:
                log.debug('Found the list of pages: ' + repr(pages))
                p = self._plugin.path
                try:
                    totalpages = int(pages[-1])
                    page = int(p.args.get('page', 1))
                except ValueError:
                    log.error('Unable to convert "{0}" & "{1}" into integer.').format(pages[-1],
                        p.args.get('page'))
                else:
                    if page < totalpages:
                        url = self._plugin.urlRootStr + str(URL(p, page = page + 1))
                        li = xbmcgui.ListItem(iconImage='DefaultFolder.png')
                        txt = self._plugin.localize(30301)
                        label = '{0}... ({1}/{2})'.format(txt, page, totalpages)
                        li.setLabel(label)
                        log.debug('Adding pagination ({0}/{1}) to: "{2}".'.format(page, totalpages, url))
                        yield url, li, True

    _durRegex = re.compile(r'^(?:(\d+):)?([0-5]?[0-9]):([0-5]?[0-9])$')
    def convertDuration(self, dur):
        # UR Play format is h:mm:ss. Kodi want duration in minutes only.
        match = self._durRegex.match(dur)
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

class Video(BaseHandler):
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