# coding=utf-8
"""Module providing the RectangularRegion class."""

from __future__ import absolute_import, division

import uuid

from .CommonMixin import CommonMixin


class RectangularRegion(CommonMixin):
    """
    A rectangular region to exclude from printing.

    The region is defined by specifying the four edge coordinates.

    Attributes
    ----------
    x1 : float
        The x coordinate of the left edge.  Expected to be <= x2.
    y1 : float
        The y coordinate of the top edge.  Expected to be <= y2.
    x2 : float
        The x coordinate of the right edge.  Expected to be >= x1.
    y2 : float
        The y coordinate of the bottom edge.  Expected to be >= y1.
    id : string
        Unique identifier assigned to the region.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the instance properties.

        Following construction, x1 <= x2 and y1 <= y2 will hold true for the respective object
        properties.

        Parameters
        ----------
        toCopy :  RectangularRegion
            If provided, the new instance will be a clone of this instance.

        kwargs.x1 : float
            The x coordinate of a vertical edge.
        kwargs.y1 : float
            The x coordinate of a horizontal edge.
        kwargs.x2 : float
            The x coordinate of a vertical edge.
        kwargs.y2 : float
            The x coordinate of a horizontal edge.
        kwargs.id : string
            Unique identifier assigned to the region.
        """
        # pylint: disable=invalid-name
        if args:
            toCopy = args[0]
            assert isinstance(toCopy, RectangularRegion), "Expected a RectangularRegion instance"

            self.x1 = toCopy.x1
            self.y1 = toCopy.y1
            self.x2 = toCopy.x2
            self.y2 = toCopy.y2
            self.id = toCopy.id
        else:
            regionId = kwargs.get("id", None)
            x1 = float(kwargs.get("x1", 0))
            y1 = float(kwargs.get("y1", 0))
            x2 = float(kwargs.get("x2", 0))
            y2 = float(kwargs.get("y2", 0))

            if (x2 < x1):
                x1, x2 = x2, x1

            if (y2 < y1):
                y1, y2 = y2, y1

            self.x1 = x1
            self.y1 = y1
            self.x2 = x2
            self.y2 = y2

            # pylint: disable=invalid-name
            if (regionId is None):
                self.id = str(uuid.uuid4())
            else:
                self.id = regionId

    def containsPoint(self, x, y):
        """
        Check if the specified point is contained in this region.

        Returns
        -------
        True if the point is inside this region, and False otherwise.
        """
        return (x >= self.x1) and (x <= self.x2) and (y >= self.y1) and (y <= self.y2)

    def containsRegion(self, otherRegion):
        """
        Check if another region is fully contained in this region.

        Returns
        -------
        True if the other region is fully contained inside this region, and False otherwise.
        """
        from octoprint_excluderegion.CircularRegion import CircularRegion

        if (isinstance(otherRegion, RectangularRegion)):
            return (
                (otherRegion.x1 >= self.x1) and
                (otherRegion.x2 <= self.x2) and
                (otherRegion.y1 >= self.y1) and
                (otherRegion.y2 <= self.y2)
            )
        elif (isinstance(otherRegion, CircularRegion)):
            return (
                (otherRegion.cx - otherRegion.r >= self.x1) and
                (otherRegion.cx + otherRegion.r <= self.x2) and
                (otherRegion.cy - otherRegion.r >= self.y1) and
                (otherRegion.cy + otherRegion.r <= self.y2)
            )
        else:
            raise ValueError("unexpected type: {otherRegion}".format(otherRegion=otherRegion))
