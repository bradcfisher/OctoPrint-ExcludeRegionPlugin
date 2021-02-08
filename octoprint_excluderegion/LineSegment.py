# coding=utf-8
"""Module providing the LineSegment class."""

from __future__ import absolute_import, division

import math

from .CommonMixin import CommonMixin
from .GeometryMixin import GeometryMixin
from .Rectangle import Rectangle


class LineSegment(CommonMixin, GeometryMixin):
    """
    Represents a geometrical line segment.

    Attributes
    ----------
    x1 : float
        The X coordinate of the start point.
    y1 : float
        The Y coordinate of the start point.
    x2 : float
        The X coordinate of the ending point.
    y2 : float
        The Y coordinate of the ending point.
    bounds : Rectangle
        Axis-aligned tight bounding box.
    """

    def __init__(self, **kwargs):
        """
        Initialize the instance properties.

        Parameters
        ----------
        toCopy :  LineSegment
            If provided, the new instance will be a clone of this instance.

        kwargs.x1 : float
            The X coordinate of the start point.
        kwargs.y1 : float
            The Y coordinate of the start point.
        kwargs.x2 : float
            The X coordinate of the end point.
        kwargs.y2 : float
            The Y coordinate of the end point.
        """
        GeometryMixin.__init__(self)

        # p y lint: disable=invalid-name
        self.x1 = float(kwargs.get("x1", 0))
        self.y1 = float(kwargs.get("y1", 0))
        self.x2 = float(kwargs.get("x2", 0))
        self.y2 = float(kwargs.get("y2", 0))

        self.length = math.hypot(self.x1 - self.x2, self.y1 - self.y2)
        self.bounds = Rectangle(x1=self.x1, y1=self.y1, x2=self.x2, y2=self.y2)

    def __repr__(self):
        """
        Return a string representation of this segment.

        Returns
        -------
        string
            String representation, such as "LineSegment[(1, 2)->(3, 4)]".
        """
        return "{}[({}, {})->({}, {})]".format(
            self.__class__.__name__, self.x1, self.y1, self.x2, self.y2
        )
