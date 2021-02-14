# coding=utf-8
"""Module providing the RectangularRegion class."""

from __future__ import absolute_import, division

from .RegionMixin import RegionMixin
from .Rectangle import Rectangle


class RectangularRegion(Rectangle, RegionMixin):
    """
    A rectangular region to exclude from printing.

    The region is defined by specifying the four edge coordinates.

    Attributes
    ----------
    x1 : float
        The X coordinate of the left edge.  Expected to be <= x2.
    y1 : float
        The Y coordinate of the top edge.  Expected to be <= y2.
    x2 : float
        The X coordinate of the right edge.  Expected to be >= x1.
    y2 : float
        The Y coordinate of the bottom edge.  Expected to be >= y1.
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

        Following construction, x1 <= x2 and y1 <= y2 will hold true for the respective object
        properties.

        Parameters
        ----------
        toCopy :  RectangularRegion
            If provided, the new instance will be a clone of this instance.

        kwargs.x1 : float
            The X coordinate of a vertical edge.
        kwargs.y1 : float
            The Y coordinate of a horizontal edge.
        kwargs.x2 : float
            The X coordinate of a vertical edge.
        kwargs.y2 : float
            The Y coordinate of a horizontal edge.
        kwargs.id : string
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
            Rectangle.__init__(self, x1=toCopy.x1, y1=toCopy.y1, x2=toCopy.x2, y2=toCopy.y2)
            self.id = toCopy.id
        else:
            Rectangle.__init__(
                    self,
                    x1=float(kwargs.get("x1", 0)),
                    y1=float(kwargs.get("y1", 0)),
                    x2=float(kwargs.get("x2", 0)),
                    y2=float(kwargs.get("y2", 0))
            )

    def containsPoint3d(self, x, y, z):
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
        return self.inHeightRange(z) and self.containsPoint(x, y)

    def containsRegion(self, otherRegion):
        """
        Check if another region is fully contained in this region.

        Returns
        -------
        True if the other region is fully contained inside this region, and False otherwise.
        """
        # pylint: disable=import-outside-toplevel
        from octoprint_excluderegion.CircularRegion import CircularRegion

        if (isinstance(otherRegion, RectangularRegion)):
            return (
                (otherRegion.x1 >= self.x1) and
                (otherRegion.x2 <= self.x2) and
                (otherRegion.y1 >= self.y1) and
                (otherRegion.y2 <= self.y2)
            )

        if (isinstance(otherRegion, CircularRegion)):
            return (
                (otherRegion.cx - otherRegion.r >= self.x1) and
                (otherRegion.cx + otherRegion.r <= self.x2) and
                (otherRegion.cy - otherRegion.r >= self.y1) and
                (otherRegion.cy + otherRegion.r <= self.y2)
            )

        raise ValueError("unexpected type: {otherRegion}".format(otherRegion=otherRegion))
