# coding=utf-8
"""Module providing the CircularRegion class."""

from __future__ import absolute_import

import uuid
import math

from .CommonMixin import CommonMixin


class CircularRegion(CommonMixin):
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
        """
        # pylint: disable=invalid-name
        if args:
            toCopy = args[0]
            assert isinstance(toCopy, CircularRegion), "Expected a CircularRegion instance"

            self.cx = toCopy.cx
            self.cy = toCopy.cy
            self.r = toCopy.r
            self.id = toCopy.id
        else:
            regionId = kwargs.get("id", None)

            self.cx = float(kwargs.get("cx", 0))
            self.cy = float(kwargs.get("cy", 0))
            self.r = float(kwargs.get("r", 0))
            if (regionId is None):
                self.id = str(uuid.uuid4())
            else:
                self.id = regionId

    # pylint: disable=invalid-name
    def containsPoint(self, x, y):
        """
        Check if the specified point is contained in this region.

        Returns
        -------
        True if the point is inside this region, and False otherwise.
        """
        return self.r >= math.hypot(x - self.cx, y - self.cy)

    def containsRegion(self, otherRegion):
        """
        Check if another region is fully contained in this region.

        Returns
        -------
        True if the other region is fully contained inside this region, and False otherwise.
        """
        from octoprint_excluderegion.RectangularRegion import RectangularRegion

        if (isinstance(otherRegion, RectangularRegion)):
            return (
                self.containsPoint(otherRegion.x1, otherRegion.y1) and
                self.containsPoint(otherRegion.x2, otherRegion.y1) and
                self.containsPoint(otherRegion.x2, otherRegion.y2) and
                self.containsPoint(otherRegion.x1, otherRegion.y2)
            )
        elif (isinstance(otherRegion, CircularRegion)):
            dist = math.hypot(self.cx - otherRegion.cx, self.cy - otherRegion.cy) + otherRegion.r
            return (dist <= self.r)
        else:
            raise ValueError("unexpected type: {otherRegion}".format(otherRegion=otherRegion))
