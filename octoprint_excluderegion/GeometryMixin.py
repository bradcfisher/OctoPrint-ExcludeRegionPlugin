# coding=utf-8
"""Module providing the GeometryMixin."""

from __future__ import absolute_import, division


ROUND_PLACES = 7
EPSILON = 0.00000005

def floatCmp(a, b):
    if (abs(a - b) < EPSILON):
        return 0
    return -1 if (a < b) else 1

class GeometryMixin(object):
    """Mixin applied to geometry objects."""

        