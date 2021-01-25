# coding=utf-8
"""Module providing the CircularRegion class."""

from __future__ import absolute_import, division

import math

from .RegionMixin import RegionMixin


class CircularRegion(RegionMixin):
    """
    A circular region to exclude from printing.

    Attributes
    ----------
    cx : float
        The x coordinate of the region's center point.
    cy : float
        The y coordinate of the region's center point.
    r : float
        The radius of the region.
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
        toCopy :  CircularRegion
            If provided, the new instance will be a clone of this instance.

        kwargs.cx : float
            The x coordinate of the region's center point.
        kwargs.cy : float
            The y coordinate of the region's center point.
        kwargs.r : float
            The radius of the region.
        kwargs.id : float
            Unique identifier assigned to the region.
        kwargs.minLayer : Layer
            The minimum layer at which this region should be enforced.  Default is 0.
        kwargs.maxLayer : Layer
            The maximum layer at which this region should be enforced.  Default is None.
        """
        RegionMixin.__init__(self, *args, **kwargs)
        
        # pylint: disable=invalid-name
        if args:
            toCopy = args[0]
            assert isinstance(toCopy, self.__class__), "Expected a " + self.__class__ + " instance"

            self.cx = toCopy.cx
            self.cy = toCopy.cy
            self.r = toCopy.r
            self.id = toCopy.id
        else:
            self.cx = float(kwargs.get("cx", 0))
            self.cy = float(kwargs.get("cy", 0))
            self.r = float(kwargs.get("r", 0))

    # pylint: disable=invalid-name
    def containsPoint(self, x, y, z):
        """
        Check if the specified point is contained in this region.

        Parameters
        ----------
        x : float
            The x component of the point to test
        y : float
            The y component of the point to test
        z : float
            The z component of the point to test

        Returns
        -------
        True if the point is inside this region, and False otherwise.
        """
        return self.inHeightRange(z) and self.r >= math.hypot(x - self.cx, y - self.cy)

    def containsRegion(self, otherRegion):
        """
        Check if another region is fully contained in this region.

        Returns
        -------
        True if the other region is fully contained inside this region, and False otherwise.
        """
        from octoprint_excluderegion.RectangularRegion import RectangularRegion

        if (isinstance(otherRegion, RectangularRegion)):
            z = self.getMinHeight()
            return (
                self.containsPoint(otherRegion.x1, otherRegion.y1, z) and
                self.containsPoint(otherRegion.x2, otherRegion.y1, z) and
                self.containsPoint(otherRegion.x2, otherRegion.y2, z) and
                self.containsPoint(otherRegion.x1, otherRegion.y2, z)
            )
        elif (isinstance(otherRegion, CircularRegion)):
            dist = math.hypot(self.cx - otherRegion.cx, self.cy - otherRegion.cy) + otherRegion.r
            return (dist <= self.r)
        else:
            raise ValueError("unexpected type: {otherRegion}".format(otherRegion=otherRegion))
