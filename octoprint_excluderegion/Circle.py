# coding=utf-8
"""Module providing the Circle class."""

from __future__ import absolute_import, division

import math

from .CommonMixin import CommonMixin
from .GeometryMixin import GeometryMixin, ROUND_PLACES, EPSILON
from .LineSegment import LineSegment


# Compute where along the segment the point falls
# Point is on segment iff: 0 <= dotproduct <= 1
def normalizedDotProd(segment, x, y):
    """Compute the normalized dot product of a point relative to a line segment."""
    dx = (segment.x2 - segment.x1)
    dy = (segment.y2 - segment.y1)
    squaredlengthba = dx*dx + dy*dy
    return ((x - segment.x1) * dx + (y - segment.y1) * dy) / squaredlengthba


def append_arc_segment(result, arc, lastSweep, sweep):
    """
    Append an new arc segment to a list if the provided sweep values are within the arc's range.

    The new arc is created with the same center point and radius as the original,
    with the startAngle set to arc.startAngle + lastSweep, and ends at the angle represented
    by the sweep parameter in the original arc.
    """
    # pylint: disable=import-outside-toplevel
    from .Arc import Arc

    if (arc.clockwise):
        add = (arc.sweep <= sweep < lastSweep <= 0)
    else:
        add = (arc.sweep >= sweep > lastSweep >= 0)

    if (add):
        result.append(
            Arc(
                cx=arc.cx,
                cy=arc.cy,
                radius=arc.radius,
                startAngle=arc.startAngle + lastSweep,
                sweep=sweep - lastSweep
            )
        )


class Circle(CommonMixin, GeometryMixin):
    """
    Represents a geometrical circle.

    Attributes
    ----------
    cx : float
        The x coordinate of the circle's center point.
    cy : float
        The y coordinate of the circle's center point.
    radius : float
        The radius of the circle.
    """

    def __init__(self, **kwargs):
        """
        Initialize the instance properties.

        Parameters
        ----------
        kwargs.cx : float
            The x coordinate of the circle's center point.
        kwargs.cy : float
            The y coordinate of the circle's center point.
        kwargs.radius : float
            The radius of the circle.
        """
        GeometryMixin.__init__(self)

        self.cx = float(kwargs.get("cx", 0))
        self.cy = float(kwargs.get("cy", 0))
        self.radius = float(kwargs.get("radius", 1))

        if (self.radius <= 0):
            raise ValueError("The radius must be greater than 0")

    def __eq__(self, other):
        """Compare this object to another."""
        return (self.cx == other.cx) and (self.cy == other.cy) and (self.radius == other.radius)

    def __repr__(self):
        """
        Return a string representation of this segment.

        Returns
        -------
        string
            String representation, such as "Rectangle[(1, 2)->(3, 4)]".
        """
        return "{}[({}, {}) radius={}]".format(
            self.__class__.__name__, self.cx, self.cy, self.radius
        )

    def roundValues(self, numPlaces=ROUND_PLACES):
        """Round internal values."""
        self.cx = round(self.cx, numPlaces)
        self.cy = round(self.cy, numPlaces)
        self.radius = round(self.radius, numPlaces)
        return self

    def containsRect(self, rect):
        """
        Test whether another Rectangle is fully contained inside this Rectangle.

        Parameters
        ----------
        rect : Rectangle
            The rectangle to test

        Returns
        -------
        boolean
            True if the specified Rectangle is fully contained in this Rectangle, False otherwise.
        """
        return (
            self.containsPoint(rect.x1, rect.y1) and
            self.containsPoint(rect.x2, rect.y1) and
            self.containsPoint(rect.x2, rect.y2) and
            self.containsPoint(rect.x1, rect.y2)
        )

    # pylint: disable=invalid-name
    def containsPoint(self, x, y):
        """
        Check if the specified point is contained in this circle.

        Parameters
        ----------
        x : float
            The x component of the point to test
        y : float
            The y component of the point to test

        Returns
        -------
        True if the point is inside this circle, and False otherwise.
        """
        return self.radius >= math.hypot(x - self.cx, y - self.cy)

    def lineSegmentDifference(self, lineSegment):
        """
        Compute the difference between this region and the specified LineSegment.

        https://mathworld.wolfram.com/Circle-LineIntersection.html

        Parameters
        ----------
        lineSegment : LineSegment
            The segment to compute the difference for

        Returns
        -------
        Returns a list containing 0, 1 or 2 LineSegments.  When the LineSegment is completely
        contained in this region, the list will be empty.  If the LineSegment and region do
        not overlap at all, or one end of the LineSegment is inside this region, then a single
        LineSegment is returned.  If the LineSegment and region overlap, but both ends of the
        LineSegment fall outside the region, then two LineSegments are returned.
        """
        dx = lineSegment.x2 - lineSegment.x1
        dy = lineSegment.y2 - lineSegment.y1

        # print(" >>> dx=", dx, ", dy=", dy)

        dr2 = math.hypot(dx, dy)
        dr2 = dr2 * dr2

        D = lineSegment.x1 * lineSegment.y1 - lineSegment.x2 * lineSegment.y2

        discriminant = self.radius * self.radius * dr2 - D * D

        # print(" >>> dr2=", dr2, ", D=", D, ", discriminant=", discriminant)
        if (discriminant <= 0):
            return [lineSegment]   # No intersection (<0) or line is tangent (=0)

        # Two possible points of intersection
        srDisc = math.sqrt(discriminant)
        sdydxDisc = (-1 if dy < 0 else 1) * dx * srDisc
        adyDisc = abs(dy) * srDisc

        x1 = (D * dy + sdydxDisc) / dr2
        y1 = (-D * dx + adyDisc) / dr2

        x2 = (D * dy - sdydxDisc) / dr2
        y2 = (-D * dx - adyDisc) / dr2

        # print(" >>> srDisc=", srDisc, ", sdydxDisc=", sdydxDisc, ", adyDisc=", adyDisc)
        # print(" >>> x1=", x1, ", y1=", y1, ", x2=", x2, ", y2=", y2)

        result = []

        dp1 = normalizedDotProd(lineSegment, x1, y1)
        dp2 = normalizedDotProd(lineSegment, x2, y2)
        if (dp2 < dp1):
            dp1, dp2 = dp2, dp1
            x1, y1, x2, y2 = x2, y2, x1, y1

        p1Match = 0 <= dp1 <= 1
        p2Match = 0 <= dp2 <= 1

        if p1Match or p2Match:
            if (p1Match):
                if (abs(lineSegment.x1 - x1) > EPSILON) or (abs(lineSegment.y1 - y1) > EPSILON):
                    result.append(LineSegment(x1=lineSegment.x1, y1=lineSegment.y1, x2=x1, y2=y1))

            if (p2Match):
                if (abs(lineSegment.x2 - x2) > EPSILON) or (abs(lineSegment.y2 - y2) > EPSILON):
                    result.append(LineSegment(x1=x2, y1=y2, x2=lineSegment.x2, y2=lineSegment.y2))
        else:
            result.append(lineSegment)

        return result

    # based on the math here:
    # http://math.stackexchange.com/a/1367732
    # https://gist.github.com/jupdike/bfe5eb23d1c395d8a0a1a4ddd94882ac
    def computeArcIntAngles(self, arc):
        centerdx = self.cx - arc.cx
        centerdy = self.cy - arc.cy

        R = math.sqrt(centerdx * centerdx + centerdy * centerdy)
        if (not (abs(self.radius - arc.radius) <= R <= self.radius + arc.radius)):  # no intersect
            return []  # empty list of results

        # intersection(s) should exist
        R2 = R * R
        R4 = R2 * R2

        r2r2 = self.radius * self.radius - arc.radius * arc.radius
        a = r2r2 / (2 * R2)
        c = math.sqrt(2 * (self.radius * self.radius + arc.radius * arc.radius) / R2 - (r2r2 * r2r2) / R4 - 1)

        fx = (self.cx + arc.cx) / 2 + a * (arc.cx - self.cx)
        gx = c * (arc.cy - self.cy) / 2
        ix1 = fx + gx
        ix2 = fx - gx

        fy = (self.cy + arc.cy) / 2 + a * (arc.cy - self.cy)
        gy = c * (self.cx - arc.cx) / 2
        iy1 = fy + gy
        iy2 = fy - gy

        result = []

        # note if gy == 0 and gx == 0 then the circles are tangent and there is only one solution
        # In that case, we simply return an empty list
        
        #print(">>> gx=", gx, ", gy=", gy)
        #print(">>> p1=(", ix1, ", ", iy1, ") angle=", math.atan2(iy1 - arc.cy, ix1 - arc.cx))
        #print(">>> p2=(", ix2, ", ", iy2, ") angle=", math.atan2(iy2 - arc.cy, ix2 - arc.cx))

        if (gx != 0) or (gy != 0):
            angle = math.atan2(iy1 - arc.cy, ix1 - arc.cx)
            if (arc.containsAngle(angle)):
                result.append(arc.angleToSweep(angle))

            angle = math.atan2(iy2 - arc.cy, ix2 - arc.cx)
            if (arc.containsAngle(angle)):
                result.append(arc.angleToSweep(angle))

        return result

    def arcDifference(self, arc):
        """
        Compute the difference between this region and the specified Arc.

        Parameters
        ----------
        arc : Arc
            The Arc to compute the difference for

        Returns
        -------
        Returns a list containing 0, 1 or 2 Arcs.  When the Arc is completely contained in
        this region, the list will be empty.  If the Arc and region do not overlap at all,
        or one end of the Arc is inside this region, then a single Arc is returned.  If the
        Arc and region overlap, but both ends of the Arc fall outside the region, then two
        Arcs are returned.
        """
        # May intersect in 0, 1 or 2 points
        anglesOfIntersection = self.computeArcIntAngles(arc)

        include = not self.containsPoint(arc.x1, arc.y1)

        if (not anglesOfIntersection):
            if (include):
                return [arc]  # No intersection
            else:
                return []     # Contained

        # Convert to sweep angles relative to the arc's startAngle, sort the result and iterate
        anglesOfIntersection = sorted(
            anglesOfIntersection,
            reverse=arc.clockwise
        )

        lastSweep = 0

        #print(">>> include=", include, ", anglesOfIntersection=", anglesOfIntersection)

        result = []
        for sweep in anglesOfIntersection:
            if (include):
                append_arc_segment(result, arc, lastSweep, sweep)

            include = not include
            lastSweep = sweep

        if (include):
            append_arc_segment(result, arc, lastSweep, arc.sweep)

        return result
