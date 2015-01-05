# -*- coding: utf-8 -*-
import xbmcgui
import xbmcplugin
import requests
import json
import urllib
import util
from parsedom import parseDOM

log = util.Logger()

class BaseHandler(object):
    def __init__(self, plugin):
        self._plugin = plugin

    @property
    def URL(self):
        return 'http://urplay.se'

    def process(self):
        pass

class Collection(BaseHandler):
    def _fetch(self):
        return []

    def process(self):
        log.info('Fetching videos from "{0}".'.format(self.URL))
        items = self._fetch()
        # Unfortunately addDirectoryItems() does not work with generators.
        # Call list() on the generator object.
        xbmcplugin.addDirectoryItems(self._plugin.handle, list(items))
        xbmcplugin.endOfDirectory(self._plugin.handle)

class StaticDir(Collection):
    _items = []
    def _fetch(self):
        log.debug('Fetching {0} page!'.format(type(self).__name__))
        for langCode, uri in self._items:
            url = self._plugin.baseURL + uri
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

class VideoCollection(Collection):
    def __init__(self, plugin, path):
        super(VideoCollection, self).__init__(plugin)
        self._path = path
    
    @property
    def URL(self):
        return super(VideoCollection, self).URL + '/' + self._path

class CurrentVideos(VideoCollection):
    @property
    def URL(self):
        return super(CurrentVideos, self).URL + '/Aktuellt/' + self._path

class Series(VideoCollection):
    @property
    def URL(self):
        return super(Series, self).URL + '/Produkter/' + self._path

class Video(BaseHandler):
    def __init__(self, plugin, id):
        super(Video, self).__init__(plugin)
        self._id = id

    @property
    def URL(self):
        return super(Video, self).URL + '/Produkter/' + self._id

    def process(self):
        try:
            log.info('Fetching video info from "{0}".'.format(self.URL))
            req = requests.get(self.URL)
            req.raise_for_status()

            match = re.search(r'urPlayer\.init\((.*?)\);', req.text)
            if match is None:
                raise Exception('No JSON data found')

            js = json.loads(match.group(1))
            fl = js['file_hd'] if j['file_hd'] != '' else j['file_flash']
            vidURL = 'http://{streaming_config[streamer][redirect]}/'\
                    'urplay/_definst_/mp4:{vid_file}/'\
                    '{streaming_config[http_streaming][hls_file]}'.format(vid_file = fl, **js)

            li = xbmcgui.ListItem(name = self._id, path = vidURL)
            log.debug('Playing video from URL: "{0}"'.format(vidURL))
            xbmcplugin.setResolvedUrl(self._plugin.handle, True, li)

            # TODO: Subtitles!

        except Exception as e:
            xbmcplugin.setResolvedUrl(self._plugin.handle, False, None)
            log.error('Unable to fetch video info from url "{0}" ({1}).'.format(url, e))