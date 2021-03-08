# coding=utf-8
"""Module providing the Rectangle class."""

from __future__ import absolute_import, division

import math

from .CommonMixin import CommonMixin
from .GeometryMixin import GeometryMixin, ROUND_PLACES, floatCmp

INSIDE = 0  # 0000
LEFT = 1    # 0001
RIGHT = 2   # 0010
BOTTOM = 4  # 0100
TOP = 8     # 1000

Arc = None

def doImportsIfNeeded():
    global Arc, LineSegment
    if (Arc is None):
        from .Arc import Arc
        from .LineSegment import LineSegment


def append_arc_segment(result, arc, lastSweep, sweep, intersects):
    """
    Create a new arc segment and appends to the result.

    The new arc is created with the same center point and radius as the original,
    with the startAngle set to arc.startAngle + lastSweep, and ends at the angle represented
    by the sweep parameter in the original arc.

    No arc is added if the lastSweep and sweep values are identical.

    Parameters:
    -----------
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
        a = Arc(
            cx=arc.cx,
            cy=arc.cy,
            radius=arc.radius,
            startAngle=arc.startAngle + lastSweep,
            sweep=sweep - lastSweep
        )
        a.intersects = intersects
        result.append(a)

class Rectangle(CommonMixin, GeometryMixin):
    """
    Represents a geometrical rectangle.

    Attributes
    ----------
    x1 : float
        The X coordinate of the left edge.  Normalized to be <= x2.
    y1 : float
        The Y coordinate of the top edge.  Normalized to be <= y2.
    x2 : float
        The X coordinate of the right edge.  Normalized to be >= x1.
    y2 : float
        The Y coordinate of the bottom edge.  Normalized to be >= y1.
    """

    def __init__(self, **kwargs):
        """
        Initialize the instance properties.

        Parameters
        ----------
        kwargs.x1 : float
            The X coordinate of a vertical edges.
        kwargs.y1 : float
            The Y coordinate of a horizontal edge.
        kwargs.x2 : float
            The X coordinate of a vertical edges.
        kwargs.y2 : float
            The Y coordinate of a horizontal edge.
        """
        GeometryMixin.__init__(self)

        self.x1 = float(kwargs.get("x1", 0))
        self.y1 = float(kwargs.get("y1", 0))
        self.x2 = float(kwargs.get("x2", 0))
        self.y2 = float(kwargs.get("y2", 0))

        if (self.x1 > self.x2):
            [self.x1, self.x2] = [self.x2, self.x1]

        if (self.y1 > self.y2):
            [self.y1, self.y2] = [self.y2, self.y1]

    def __eq__(self, other):
        """Compare this object to another."""
        return (
            (other is not None) and
            (floatCmp(self.x1, other.x1) == 0) and
            (floatCmp(self.x2, other.x2) == 0) and
            (floatCmp(self.y1, other.y1) == 0) and
            (floatCmp(self.y2, other.y2) == 0)
        )

    def __repr__(self):
        """
        Return a string representation of this segment.

        Returns
        -------
        string
            String representation, such as "Rectangle[(1, 2)->(3, 4)]".
        """
        return "{}[({}, {})->({}, {})]".format(
            self.__class__.__name__, self.x1, self.y1, self.x2, self.y2
        )

    def roundValues(self, numPlaces=ROUND_PLACES):
        """Round internal values."""
        self.x1 = round(self.x1, numPlaces)
        self.y1 = round(self.y1, numPlaces)
        self.x2 = round(self.x2, numPlaces)
        self.y2 = round(self.y2, numPlaces)
        return self

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
        doImportsIfNeeded()
        if (isinstance(geometry, LineSegment)):
            return self.lineSegmentDifference(geometry)
        elif (isinstance(geometry, Arc)):
            return self.arcDifference(geometry)
        else:
            raise TypeError("geometry object must be an Arc or a LineSegment")

    def computeSegmentOutCode(self, x, y):
        """
        Compute the outcode for the point x,y relative to this rectangle.

        The outcode is a bitfield indicating if the point is inside, to the left, above,
        to the right or below the bounds of the rectangle.  It consists of four bits
        and may be one of the following values:

        0000 - The point is inside
        0001 - The point is to the left
        0101 - The point is below to the left
        1001 - The point is above to the left
        0010 - The point is to the right
        0110 - The point is below to the right
        1010 - The point is above to the right
        0100 - The point is below
        1000 - The point is above
        """
        if (x < self.x1):         # to the left of clip window
            code = LEFT
        elif (x > self.x2):       # to the right of clip window
            code = RIGHT
        else:
            code = INSIDE         # inside of clip window

        if (y < self.y1):         # below the clip window
            code |= BOTTOM
        elif (y > self.y2):       # above the clip window
            code |= TOP

        return code

    def lineSegmentDifference(self, lineSegment):
        """
        Compute the difference between this region and the specified LineSegment.

        https://en.wikipedia.org/wiki/Cohen%E2%80%93Sutherland_algorithm

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
        doImportsIfNeeded()
        x0, y0, x1, y1 = lineSegment.x1, lineSegment.y1, lineSegment.x2, lineSegment.y2

        # compute outcodes for P0, P1, and whatever point lies outside the clip rectangle
        outcode0 = self.computeSegmentOutCode(x0, y0)
        outcode1 = self.computeSegmentOutCode(x1, y1)
        insertPos = 0

        result = []
        while (True):
            if (not (outcode0 | outcode1)):
                # bitwise OR is 0: both points inside window
                segment = LineSegment(x1=x0, y1=y0, x2=x1, y2=y1)
                segment.intersects = True
                
                l = len(result)
                if (l == 0):    # Entirely contained
                    result.append(segment)
                elif (l == 2):  # Middle portion contained
                    result.insert(1, segment)
                else:
                    p = result[0]
                    if (x1 == p.x1) and (y1 == p.y1):  # Starting portion contained?
                        result.insert(0, segment)
                    else:  # Ending portion contained
                        result.append(segment)

                break

            if (outcode0 & outcode1):
                # bitwise AND is not 0: both points share an outside zone (LEFT, RIGHT, TOP,
                # or BOTTOM), so both must be outside window; accept and exit loop
                segment = LineSegment(x1=x0, y1=y0, x2=x1, y2=y1)
                segment.intersects = False
                result.append(segment)
                break

            # failed both tests, so calculate the line segment to clip
            # from an outside point to an intersection with clip edge

            # At least one endpoint is outside the clip rectangle; pick it.
            outcodeOut = outcode1 if outcode1 > outcode0 else outcode0

            # Now find the intersection point;
            # use formulas:
            #   slope = (y1 - y0) / (x1 - x0)
            #   x = x0 + (1 / slope) * (ym - y0), where ym is ymin or ymax
            #   y = y0 + slope * (xm - x0), where xm is xmin or xmax
            # No need to worry about divide-by-zero because, in each case, the
            # outcode bit being tested guarantees the denominator is non-zero
            if (outcodeOut & TOP):        # point is above the clip window
                x = x0 + (x1 - x0) * (self.y2 - y0) / (y1 - y0)
                y = self.y2
            elif (outcodeOut & BOTTOM):   # point is below the clip window
                x = x0 + (x1 - x0) * (self.y1 - y0) / (y1 - y0)
                y = self.y1
            elif (outcodeOut & RIGHT):    # point is to the right of clip window
                y = y0 + (y1 - y0) * (self.x2 - x0) / (x1 - x0)
                x = self.x2
            else:  # (outcodeOut & LEFT) - point is to the left of clip window
                y = y0 + (y1 - y0) * (self.x1 - x0) / (x1 - x0)
                x = self.x1

            # Now we move outside point to intersection point to clip
            # and get ready for next pass.
            if (outcodeOut == outcode0):
                segment = LineSegment(x1=x0, y1=y0, x2=x, y2=y)
                segment.intersects = False
                result.insert(0, segment)

                x0 = x
                y0 = y
                outcode0 = self.computeSegmentOutCode(x0, y0)
            else:
                segment = LineSegment(x1=x, y1=y, x2=x1, y2=y1)
                segment.intersects = False
                result.append(segment)

                x1 = x
                y1 = y
                outcode1 = self.computeSegmentOutCode(x1, y1)

        return result

    def intersectsRect(self, rect):
        """
        Test whether another Rectangle intersects with this Rectangle.

        Parameters
        ----------
        rect : Rectangle
            The rectangle to test

        Returns
        -------
        boolean
            True if the specified Rectangle intersects with this Rectangle, False otherwise.
        """
        return ((rect.x2 > self.x1) and (rect.x1 < self.x2) and
                (rect.y2 > self.y1) and (rect.y1 < self.y2))

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
        return ((rect.x1 >= self.x1) and (rect.x2 <= self.x2) and
                (rect.y1 >= self.y1) and (rect.y2 <= self.y2))

    def containsPoint(self, x, y):
        """
        Test whether a point is contained in this Rectangle.

        Parameters
        ----------
        x : float
            The x component of the point to test
        y : float
            The y component of the point to test

        Returns
        -------
        boolean
            True if the specified point is contained in this Rectangle, False otherwise.
        """
        return ((self.x1 <= x <= self.x2) and (self.y1 <= y <= self.y2))

    def computeArcVertIntAngles(self, x, arc):
        """
        Compute sweep of intersections of a vertical line segment of this rectangle and an arc.

        Returns
        -------
        A list of arc sweep values at which the given arc intersects the specified vertical
        line segment.
        """
        # pylint: disable=invalid-name

        # Circle:
        #   (x - cx)^2 + (y - cy)^2 = r^2
        # Solve for y:
        #   (y - cy)^2 = r^2 - (x - cx)^2
        #   y - cy = +/- sqrt(r^2 - (x - cx)^2)
        #   y = cy +/- sqrt(r^2 - (x - cx)^2)
        dx = x - arc.cx
        radius = arc.radius
        if (abs(dx) > radius):
            return []   # No intersection

        sr = math.sqrt(radius*radius - dx*dx)

        y1 = arc.cy + sr
        y2 = arc.cy - sr

        result = []
        if (self.y1 <= y1 <= self.y2):
            angle = math.atan2(sr, dx)
            if (arc.containsAngle(angle)):
                result.append(arc.angleToSweep(angle))

        if (sr != 0) and (self.y1 <= y2 <= self.y2):
            angle = math.atan2(-sr, dx)
            if (arc.containsAngle(angle)):
                result.append(arc.angleToSweep(angle))

        return result

    def computeArcHorizIntAngles(self, y, arc):
        """
        Compute sweep of intersections of a horizontal line segment of this rectangle and an arc.

        Returns
        -------
        A list of arc sweep values at which the given arc intersects the specified horizontal
        line segment.
        """
        # pylint: disable=invalid-name

        # Circle:
        #   (x - cx)^2 + (y - cy)^2 = r^2
        # Solve for x:
        #   (x - cx)^2 = r^2 - (y - cy)^2
        #   x - cx = sqrt(r^2 - (y - cy)^2)
        #   x = cx +/- sqrt(r^2 - (y - cy)^2)
        dy = y - arc.cy
        radius = arc.radius
        if (abs(dy) > radius):
            return []   # No intersection

        sr = math.sqrt(radius*radius - dy*dy)

        x1 = arc.cx + sr
        x2 = arc.cx - sr

        result = []
        if (self.x1 <= x1 <= self.x2):
            angle = math.atan2(dy, sr)
            if (arc.containsAngle(angle)):
                result.append(arc.angleToSweep(angle))

        if (sr != 0) and (self.x1 <= x2 <= self.x2):
            angle = math.atan2(dy, -sr)
            if (arc.containsAngle(angle)):
                result.append(arc.angleToSweep(angle))

        return result

    # https://stackoverflow.com/questions/27806805/intersection-of-rectangle-and-circle-or-arc
    def arcDifference(self, arc):
        """
        Compute the difference between this region and the specified Arc.

        Parameters
        ----------
        arc : Arc
            The Arc to compute the difference for

        Returns
        -------
        Returns a list containing 0 to 5 Arcs.  When the Arc is completely contained in
        this region, the list will be empty.  If the Arc and region do not overlap at all,
        then the original Arc is returned.  If the Arc and region overlap, but some of the
        arc falls outside the region, the returned list will contain 1 to 5 arcs.
        """
        doImportsIfNeeded()

        if (not self.intersectsRect(arc.bounds)):
            a = Arc(arc)
            a.intersects = False  # Completely outside the region
            return [a]

        if (self.containsRect(arc.bounds)):
            a = Arc(arc)
            a.intersects = True   # Completely inside the region
            return [a]

        # Compute angles of intersection with each edge
        anglesOfIntersection = []

        # Left edge
        if (arc.bounds.x1 < self.x1):
            anglesOfIntersection.extend(
                self.computeArcVertIntAngles(self.x1, arc)
            )

        # Right edge
        if (arc.bounds.x2 > self.x2):
            anglesOfIntersection.extend(
                self.computeArcVertIntAngles(self.x2, arc)
            )

        # Top edge
        if (arc.bounds.y1 < self.y1):
            anglesOfIntersection.extend(
                self.computeArcHorizIntAngles(self.y1, arc)
            )

        # Bottom edge
        if (arc.bounds.y2 > self.y2):
            anglesOfIntersection.extend(
                self.computeArcHorizIntAngles(self.y2, arc)
            )

        # Convert to sweep angles relative to the arc's startAngle, sort the result and iterate
        anglesOfIntersection = sorted(
            anglesOfIntersection,
            reverse=arc.clockwise
        )

        intersects = self.containsPoint(arc.x1, arc.y1)
        lastSweep = 0

        result = []
        for sweep in anglesOfIntersection:
            append_arc_segment(result, arc, lastSweep, sweep, intersects)
            intersects = not intersects
            lastSweep = sweep

        append_arc_segment(result, arc, lastSweep, arc.sweep, intersects)

        return result
