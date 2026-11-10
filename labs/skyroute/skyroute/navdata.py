# -*- coding: utf-8 -*-
#
# navdata.py - SRN-1 nav data reader
#
# Ported from the old ground-station reader (Fortran) in 2009.
# 2014: NV records.  2017: added cache, the planner was re-reading the
# file for every leg.  TODO: py3 cleanup (still has to run on the 2.7 box)
#
from __future__ import print_function

import os
import sys

_CACHE = {}
_DEF = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir,
                    'data', 'navdata.srn')

try:
    basestring
except NameError:
    basestring = str


class Fix(object):
    """One nav point. lat/lon in decimal deg, elev in ft, freq in MHz."""

    __slots__ = ('kind', 'ident', 'lat', 'lon', 'elev', 'freq', 'name')

    def __init__(self, kind, ident, lat, lon, elev=0, freq=None, name=''):
        self.kind = kind
        self.ident = ident
        self.lat = lat
        self.lon = lon
        self.elev = elev
        self.freq = freq
        self.name = name

    def __repr__(self):
        return 'Fix(%s %s %.4f %.4f)' % (self.kind, self.ident, self.lat, self.lon)


def _dms(s):
    # N33411800 / W112045700
    h = s[0]
    s = s[1:]
    if len(s) == 8:
        d, s = s[:2], s[2:]
    else:
        d, s = s[:3], s[3:]
    v = int(d) + int(s[:2]) / 60. + int(s[2:4]) / 3600. + int(s[4:6]) / 360000.
    if h in 'SW':
        v = -v
    return v


def _rd(p):
    d = {}
    f = open(p, 'r')
    try:
        for l in f.readlines():
            l = l.rstrip('\r\n')
            if not l.strip() or l[0] == '*':
                continue
            t = l[0:2]
            if t not in ('AP', 'WP', 'NV'):
                continue
            try:
                e = l[30:35].strip()
                fq = l[36:42].strip()
                k = l[3:8].strip()
                d[k] = Fix(t, k, _dms(l[9:18]), _dms(l[19:29]), int(e or 0),
                           fq and float(fq) or None, l[43:].strip())
            except:
                pass  # bad rec, skip (see AMDT notes in the data file)
    finally:
        f.close()
    return d


def load(path=None):
    """Return {ident: Fix} for an SRN-1 file. Cached per path."""
    p = path or _DEF
    if p not in _CACHE:  # was _CACHE.has_key(p)
        _CACHE[p] = _rd(p)
    return _CACHE[p]


def lookup(ident, path=None):
    """Find a fix by ident, or None."""
    if not isinstance(ident, basestring):
        return None
    return load(path).get(ident.strip().upper())


def clear():
    _CACHE.clear()


if __name__ == '__main__':
    for k, v in sorted(load(sys.argv[1] if len(sys.argv) > 1 else None).items()):
        print('%-5s %s' % (k, v))
