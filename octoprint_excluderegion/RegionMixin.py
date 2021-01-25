# coding=utf-8
"""Module providing the RegionMixin class."""

from __future__ import absolute_import, division

import uuid

from .CommonMixin import CommonMixin
from .Layer import Layer


class RegionMixin(CommonMixin):
    """
    Mixin applied to all regions to exclude from printing.

    Attributes
    ----------
    id : string
        Unique identifier assigned to the region.
    minLayer : Layer
        The minimum layer at which this region should be enforced.  Default is 0.
    maxLayer : Layer
        The maximum layer at which this region should be enforced.  Default is None.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the instance properties.

        Parameters
        ----------
        toCopy :  RegionMixin
            If provided, the new instance will be a clone of this instance.

        kwargs.id : string
            Unique identifier assigned to the region.
        kwargs.minLayer : Layer
            The minimum layer at which this region should be enforced.  Default is 0.
        kwargs.maxLayer : Layer
            The maximum layer at which this region should be enforced.  Default is None.
        """
        # pylint: disable=invalid-name
        if args:
            toCopy = args[0]
            assert isinstance(toCopy, self.__class__), "Expected a " + self.__class__ + " instance"

            self.id = toCopy.id
            self.minLayer = Layer(toCopy.minLayer)
            if (toCopy.maxLayer is None):
                self.maxLayer = None
            else:
                self.maxLayer = Layer(toCopy.minLayer)
        else:
            regionId = kwargs.get("id", None)
            if (regionId is None):
                self.id = str(uuid.uuid4())
            else:
                self.id = regionId

            minLayer = kwargs.get("minLayer", None)
            if (minLayer is None):
                self.maxLayer = Layer()
            else:
                self.minLayer = Layer(**minLayer)

            maxLayer = kwargs.get("maxLayer", None)
            if (maxLayer is None):
                self.maxLayer = None
            else:
                self.maxLayer = Layer(**maxLayer)

    def toDict(self):
        d = CommonMixin.toDict(self)
        minLayer = d.get("minLayer")
        if (minLayer is not None):
            d["minLayer"] = minLayer.toDict()
        maxLayer = d.get("maxLayer")
        if (maxLayer is not None):
            d["maxLayer"] = maxLayer.toDict()
        return d;

    def getMinHeight(self):
        return 0 if self.minLayer is None else self.minLayer.height

    def getMaxHeight(self):
        return None if self.maxLayer is None else self.maxLayer.height

    def inHeightRange(self, z):
        max = self.getMaxHeight()
        return ((self.getMinHeight() <= z) and (max is None or max >= z))
