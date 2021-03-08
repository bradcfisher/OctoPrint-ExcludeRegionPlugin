# coding=utf-8
"""Module providing the Circle class."""

from __future__ import absolute_import, division

import math

from .CommonMixin import CommonMixin
from .GeometryMixin import GeometryMixin, ROUND_PLACES, floatCmp
from .LineSegment import LineSegment
from .Arc import Arc


# Compute where along the segment the point falls
# Point is on segment iff: 0 <= dotproduct <= 1
def normalized_dot_prod(segment, x, y):
    """Compute the normalized dot product of a point relative to a line segment."""
    deltaX = (segment.x2 - segment.x1)
    deltaY = (segment.y2 - segment.y1)
    squaredlengthba = deltaX*deltaX + deltaY*deltaY
    return ((x - segment.x1) * deltaX + (y - segment.y1) * deltaY) / squaredlengthba


def append_arc_segment(result, arc, lastSweep, sweep, intersects):
    """
    Create a new arc segment and appends to the result.

    The new arc is created with the same center point and radius as the original,
    with the startAngle set to arc.startAngle + lastSweep, and ends at the angle represented
    by the sweep parameter in the original arc.

    No arc is added if the lastSweep and sweep values are identical.

    Parameters
    ----------
    result : List of Arc
        The list to append the new arg segment to.
    arc : Arc
        The arc to segment.
    lastSweep : float
        The previous segment's ending sweep, relative to the original arc startAngle.
    sweep : float
        The ending sweep for the new arc, relative to the original arc startAngle.
    intersects : boolean
        Whether this portion of the arc intersects or not.
    """
    if (lastSweep != sweep):
        newArc = Arc(
            cx=arc.cx,
            cy=arc.cy,
            radius=arc.radius,
            startAngle=arc.startAngle + lastSweep,
            sweep=sweep - lastSweep
        )
        newArc.intersects = intersects
        result.append(newArc)


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
        # pylint: disable=invalid-name
        GeometryMixin.__init__(self)

        self.cx = float(kwargs.get("cx", 0))
        self.cy = float(kwargs.get("cy", 0))
        self.radius = float(kwargs.get("radius", 1))

        if (self.radius <= 0):
            raise ValueError("The radius must be greater than 0")

    def __eq__(self, other):
        """Compare this object to another."""
        return (
            (other is not None) and
            (floatCmp(self.cx, other.cx) == 0) and
            (floatCmp(self.cy, other.cy) == 0) and
            (floatCmp(self.radius, other.radius) == 0)
        )

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

    def geometryDifference(self, geometry):
        """
        Compute the intersections & differences between this region and the specified geometry.

        Parameters
        ----------
        geometry : Arc | LineSegment
            The geometry to compute the intersections & differences for

        Returns
        -------
        Returns a list containing 1 or more geometries of the same type as the input.  The original
        geometry will be segmented into separate sections based on where it intersects the circle.
        An additional 'intersects' property will be added to each returned geometry portion to
        indicate whether that portion intersects the circle or not.
        """
        if (isinstance(geometry, LineSegment)):
            return self.lineSegmentDifference(geometry)

        if (isinstance(geometry, Arc)):
            return self.arcDifference(geometry)

        raise TypeError("geometry object must be an Arc or a LineSegment")

    def lineSegmentDifference(self, lineSegment):
        """
        Compute the intersections & differences between this region and the specified LineSegment.

        https://mathworld.wolfram.com/Circle-LineIntersection.html

        Parameters
        ----------
        lineSegment : LineSegment
            The segment to compute the intersections & differences for

        Returns
        -------
        Returns a list containing 1 or more LineSegments.  The original LineSegment will be
        segmented into separate sections based on where it intersects the circle.  An
        additional 'intersects' property will be added to each returned line segment to indicate
        whether that portion of the segment intersects the circle or not.
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
            lineSeg = LineSegment(lineSegment)
            lineSeg.intersects = False
            return [lineSeg]   # No intersection (<0) or line is tangent (=0)

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

        dp1 = normalized_dot_prod(lineSegment, x1, y1)
        dp2 = normalized_dot_prod(lineSegment, x2, y2)
        if (dp2 < dp1):
            dp1, dp2 = dp2, dp1
            x1, y1, x2, y2 = x2, y2, x1, y1

        p1Match = 0 <= dp1 <= 1
        p2Match = 0 <= dp2 <= 1

        if p1Match or p2Match:
            ex1 = lineSegment.x1
            ey1 = lineSegment.y1
            ex2 = lineSegment.x2
            ey2 = lineSegment.y2

            if (p1Match):
                if (
                    (floatCmp(lineSegment.x1 - x1, 0) != 0) or
                    (floatCmp(lineSegment.y1 - y1, 0) != 0)
                ):
                    ex1 = x1
                    ey1 = y1
                    lineSeg = LineSegment(x1=lineSegment.x1, y1=lineSegment.y1, x2=x1, y2=y1)
                    lineSeg.intersects = False
                    result.append(lineSeg)

            lineSeg2 = None
            if (p2Match):
                if (
                    (floatCmp(lineSegment.x2 - x2, 0) != 0) or
                    (floatCmp(lineSegment.y2 - y2, 0) != 0)
                ):
                    ex2 = x2
                    ey2 = y2
                    lineSeg2 = LineSegment(x1=x2, y1=y2, x2=lineSegment.x2, y2=lineSegment.y2)
                    lineSeg2.intersects = False

            if (floatCmp(ex2 - ex1, 0) != 0) or (floatCmp(ey2 - ey1, 0) != 0):
                lineSeg = LineSegment(x1=ex1, y1=ey1, x2=ex2, y2=ey2)
                lineSeg.intersects = True
                result.append(lineSeg)

            if (lineSeg2 is not None):
                result.append(lineSeg2)
        else:
            lineSeg = LineSegment(lineSegment)
            lineSeg.intersects = False
            result.append(lineSeg)

        return result

    # based on the math here:
    # http://math.stackexchange.com/a/1367732
    # https://gist.github.com/jupdike/bfe5eb23d1c395d8a0a1a4ddd94882ac
    def computeArcIntAngles(self, arc):
        """
        Compute the sweep angles at which an arc intersects this circle.

        Parameters
        ----------
        arc : Arc
            The arc for which to compute the sweep angles of intersection.

        Returns
        -------
        List of float
            List of sweep angles at which the arc intersects the circle, or an empty list
            if there is no intersection.
        """
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
        c = math.sqrt(
            2 * (self.radius * self.radius + arc.radius * arc.radius) / R2 - (r2r2 * r2r2) / R4 - 1
        )

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

        # print(">>> gx=", gx, ", gy=", gy)
        # print(">>> p1=(", ix1, ", ", iy1, ") angle=", math.atan2(iy1 - arc.cy, ix1 - arc.cx))
        # print(">>> p2=(", ix2, ", ", iy2, ") angle=", math.atan2(iy2 - arc.cy, ix2 - arc.cx))

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
        Returns a list containing 1 or more Arcs based on the input.  The original Arc
        will be segmented into separate sections based on where it intersects the circle.
        An additional 'intersects' property will be added to each returned Arc portion to
        indicate whether that portion intersects the circle or not.
        """
        # May intersect in 0, 1 or 2 points
        anglesOfIntersection = self.computeArcIntAngles(arc)

        intersects = self.containsPoint(arc.x1, arc.y1)

        # Convert to sweep angles relative to the arc's startAngle, sort the result and iterate
        anglesOfIntersection = sorted(
            anglesOfIntersection,
            reverse=arc.clockwise
        )

        lastSweep = 0

        # print(">>> intersects=", intersects, ", anglesOfIntersection=", anglesOfIntersection)

        result = []
        for sweep in anglesOfIntersection:
            append_arc_segment(result, arc, lastSweep, sweep, intersects)
            intersects = not intersects
            lastSweep = sweep

        append_arc_segment(result, arc, lastSweep, arc.sweep, intersects)

        return result
