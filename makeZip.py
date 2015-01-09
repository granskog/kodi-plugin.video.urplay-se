# -*- coding: utf-8 -*-
import sys
import os
import xml.etree.ElementTree as ET
import zipfile
import __main__
_thisFile = __main__.__file__

def makeZippy(argv):
    try:
        tree = ET.parse('addon.xml')
    except IOError:
        sys.exit('Unable to open addon.xml.')
    except ET.ParseError:
        sys.exit('Invalid file format.')

    _root = tree.getroot()
    if _root is not None:
        try:
            _version = _root.attrib['version']
            _id = _root.attrib['id']
        except KeyError:
            sys.exit("Unable to find 'version' and 'plugin id' in addon.xml.")

    if len(argv) >= 1:
        zfName = argv[0]
        if not zfName.endswith('.zip'):
            zfName += '.zip'
    else:
        zfName = '{}-{}.zip'.format(_id, _version)

    zippy = zipfile.ZipFile(zfName, 'w',  zipfile.ZIP_DEFLATED)

    _excludes = set([_thisFile, zfName])
    # In the case one shuld need to include .zip files in the distrubution
    # package, just remove it below. It's there to not include previously
    # made zippys by accident.
    _excludeFileTypes = ('.zip', '.pyo', '.pyc', '.xbt', '.xpr', '.pdf',
        '.doc', '.dll', '.exe', 'Thumbs.db', 'thumbs.db')
    for root, dirs, files in os.walk('.', topdown = True):
        files = [f for f in files if not f.startswith('.') and f not in _excludes]
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.endswith(_excludeFileTypes):
                continue
            path = os.path.join(_id, os.path.relpath((os.path.join(root, f))))
            print 'Writing "{}" to zippy with internal path: '.format(f), path
            zippy.write(os.path.join(root, f), path)

    zippy.close()
    print '\o/\n |  Made zippy with name "{}"!\n ^'.format(zfName)

if __name__ == '__main__':

    makeZippy(sys.argv[1:])