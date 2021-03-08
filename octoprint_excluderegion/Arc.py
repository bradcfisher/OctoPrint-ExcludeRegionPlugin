# coding=utf-8
"""Module providing the Arc class."""

from __future__ import absolute_import, division

import math

from .CommonMixin import CommonMixin
from .GeometryMixin import GeometryMixin, ROUND_PLACES, floatCmp
from .Rectangle import Rectangle

PI = math.pi
TWO_PI = PI * 2
PI_Q1 = PI / 2
PI_Q2 = PI
PI_Q3 = PI * 1.5


def normalize_radians(angle):
    """Normalize an angle in radians to guarantee it falls in the range [0,2pi)."""
    result = math.fmod(angle, TWO_PI)
    return result if (result >= 0) else result + TWO_PI


class Arc(CommonMixin, GeometryMixin):  # pylint: disable=too-many-instance-attributes
    """
    Represents a geometrical arc.

    Attributes
    ----------
    cx : float
        The X coordinate of the center point.
    cy : float
        The Y coordinate of the center point.
    radius : float
        The radius of the arc.
    startAngle : float
        The starting angle of the arc, normalized to [0, 2pi)
    endAngle : float
        The ending angle of the arc, equivalent to startAngle + sweep (-2pi, 4pi)
    sweep : float
        The angular sweep of the arc, normalized to [-2pi, 2pi]
    length : float
        The length of the arc.
    clockwise : boolean
        Whether the arc sweeps clockwise [True] or counterclockwise [False]
    major : boolean
        Whether the arc represents the major portion of the circle or not
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

    @staticmethod
    def fromRadiusP1P2Clockwise(
            radius, x1, y1, x2, y2, clockwise
    ):  # pylint: disable=too-many-locals
        """
        Create an arc given a radius, start point, end point and direction.

        Parameters
        ----------
        radius : float
            The radius of the arc to compute the center point offset for.
            A positive value will result in the shortest arc proceeding in the specified direction,
            a negative radius will mirror the calculated center point on the chord between the two
            endpoints to produce the longer arc between the two endpoints.  A value of 0 is not
            permitted.
        x1 : float
            The X coordinate of the start point.
        y1 : float
            The Y coordinate of the start point.
        x2 : float
            The X coordinate of the end point.
        y2 : float
            The Y coordinate of the end point.
        clockwise : boolean
            Whether the arc proceeds in a clockwise [true] or counter-clockwise [false] direction.

        Returns
        -------
        Arc
            The computed Arc geometry based on the input parameters.

            Raises an exception if radius == 0 or the distance between the end points is
            greater that twice the radius.
        """
        # pylint: disable=invalid-name

        if (not radius):
            raise ValueError("Radius cannot be 0")

        if (x1 == x2 and y1 == y2):
            raise ValueError("The two end points cannot be identical")

        # clockwise -1/1, counterclockwise 1/-1
        e = -1 if (clockwise ^ (radius < 0)) else 1

        # X and Y differences
        deltaX = x2 - x1
        deltaY = y2 - y1

        # Linear distance between the points
        dist = math.hypot(deltaX, deltaY)
        halfDist = dist / 2

        if (halfDist > abs(radius)):
            raise ValueError(
                "Radius cannot be less than half the distance between the two end points"
            )

        # Midpoint of chord between the two endpoints
        midX = (x1 + x2) / 2
        midY = (y1 + y2) / 2

        # Distance to the arc pivot point
        h2 = (radius - halfDist) * (radius + halfDist)
        h = math.sqrt(h2) if (h2 > 0) else 0

        # Slope of the perpendicular bisector
        sx = -deltaY / dist
        sy = deltaX / dist

        # Pivot point of the arc
        centerX = midX + e * h * sx
        centerY = midY + e * h * sy

        return Arc.fromCenterP1P2Clockwise(centerX, centerY, x1, y1, x2, y2, clockwise)

    @staticmethod
    def fromCenterP1P2Clockwise(
        cx, cy, x1, y1, x2, y2, clockwise, lenient=True
    ):  # pylint: disable=too-many-arguments,invalid-name,too-many-locals
        """
        Create an arc given the center point, the end points of the arc, and direction.

        Parameters
        ----------
        cx : float
            The X coordinate of the center point.
        cy : float
            The Y coordinate of the center point.
        x1 : float
            The X coordinate of the starting point.
        y1 : float
            The Y coordinate of the starting point.
        x2 : float
            The X coordinate of the ending point.
        y2 : float
            The Y coordinate of the ending point.
        clockwise : boolean
            Whether the arc proceeds in a clockwise [true] or counter-clockwise [false] direction.
        lenient : boolean = True
            If False, will report an error if the specified end points are not equidistant
            from the center point or not.  If True, and the endpoints are not equidistant, then
            the radius of the returned arc will be equal to the distance between the start point
            and the center point.

        Returns
        -------
        Arc
            The computed Arc geometry based on the input parameters.
        """
        dx1 = x1 - cx
        dy1 = y1 - cy
        dx2 = x2 - cx
        dy2 = y2 - cy

        radius = math.hypot(dx1, dy1)

        if (not lenient):
            radius2 = math.hypot(dx2, dy2)
            if (floatCmp(radius - radius2, 0) != 0):
                raise ValueError("End points must be the same distance from the center")

        startAngle = math.atan2(dy1, dx1)
        endAngle = math.atan2(dy2, dx2)

        return Arc.fromCenterRadiusStartEndClockwise(
                   cx, cy, radius, startAngle, endAngle, clockwise
               )

    @staticmethod
    def fromCenterRadiusStartEndClockwise(
        cx, cy, radius, startAngle, endAngle, clockwise
    ):  # pylint: disable=invalid-name
        """
        Create an arc given a center point, radius, start angle, end angle, and direction.

        Parameters
        ----------
        radius : float
            The radius of the arc.
        cx : float
            The X coordinate of the center point.
        cy : float
            The Y coordinate of the center point.
        startAngle : float
            The starting angle of the arc, in radians.
        endAngle : float
            The ending angle of the arc, in radians.
        clockwise : boolean
            Whether the arc proceeds in a clockwise [true] or counter-clockwise [false] direction.

        Returns
        -------
        Arc
            The computed Arc geometry based on the input parameters.
        """
        sweep = normalize_radians(endAngle - startAngle) - (TWO_PI if clockwise else 0)
        return Arc(cx=cx, cy=cy, radius=radius, startAngle=startAngle, sweep=sweep)

    def __init__(self, *args, **kwargs):
        """
        Initialize the instance properties.

        Parameters
        ----------
        toCopy :  Arc
            If provided, the new instance will be a clone of this instance.

        kwargs.cx : float
            The x coordinate of the center point.
        kwargs.cy : float
            The x coordinate of the center point.
        kwargs.radius : float
            The radius of the arc
        kwargs.startAngle : float
            The starting angle of the arc
        kwargs.sweep : float
            The angle sweep of the arc
        """
        # pylint: disable=invalid-name
        GeometryMixin.__init__(self)

        if (args):
            other = args[0]
            self.cx = other.cx
            self.cy = other.cy
            self.radius = other.radius
            self.startAngle = normalize_radians(other.startAngle)
            self.sweep = other.sweep
        else:
            # pylint: disable=invalid-name
            self.cx = float(kwargs.get("cx", 0))
            self.cy = float(kwargs.get("cy", 0))
            self.radius = float(kwargs.get("radius", 1))
            self.startAngle = normalize_radians(float(kwargs.get("startAngle", 0)))
            self.sweep = float(kwargs.get("sweep", 0))

        if (self.radius <= 0):
            raise ValueError("The radius must be greater than 0")
        if (self.sweep < 0):
            self.sweep = -normalize_radians(-self.sweep)
            if (self.sweep == 0):
                self.sweep = -TWO_PI
        else:
            self.sweep = normalize_radians(self.sweep)
            if (self.sweep == 0):
                self.sweep = TWO_PI

        self.compute()

    def compute(self):
        """Compute values for the properties derived from the initial inputs."""
        # Start point
        self.x1 = math.cos(self.startAngle) * self.radius + self.cx
        self.y1 = math.sin(self.startAngle) * self.radius + self.cy

        # End point
        self.endAngle = self.startAngle + self.sweep
        self.x2 = math.cos(self.endAngle) * self.radius + self.cx
        self.y2 = math.sin(self.endAngle) * self.radius + self.cy

        self.clockwise = (self.sweep < 0)

        abssweep = abs(self.sweep)
        self.major = (abssweep > PI)
        self.length = abssweep * self.radius

        self.bounds = self.computeBounds()

    def computeBounds(self):
        """
        Compute the minimum axis-aligned bounding rectangle for the arc.

        Returns
        -------
        Rectangle
            The minimum axis-aligned bounding rectangle for the arc.
        """
        # Normalize to counterclockwise
        sweep = self.sweep
        if (sweep < 0):
            sweep = -sweep
            x1, x2, y1, y2 = self.x2, self.x1, self.y2, self.y1
            startAngle = normalize_radians(self.endAngle)
        else:
            x1, x2, y1, y2 = self.x1, self.x2, self.y1, self.y2
            startAngle = self.startAngle

        endAngle = startAngle + sweep

        # Top (+y)
        if (startAngle < PI_Q1 < endAngle):
            minY = self.cy + self.radius
        else:
            minY = y1 if (y1 > y2) else y2

        # Left (-x)
        if (startAngle < PI_Q2 < endAngle):
            minX = self.cx - self.radius
        else:
            minX = x1 if (x1 < x2) else x2

        # Bottom (-y)
        if (startAngle < PI_Q3 < endAngle):
            maxY = self.cy - self.radius
        else:
            maxY = y1 if (y1 < y2) else y2

        # Right (+x)
        if (endAngle > TWO_PI):
            maxX = self.cx + self.radius
        else:
            maxX = x1 if (x1 > x2) else x2

        return Rectangle(x1=minX, y1=minY, x2=maxX, y2=maxY)

    def angleToSweep(self, angle):
        """
        Given an angle returns the angle as a sweep normalized to the arc's direction.

        Returns
        -------
        double
            The specified angle as a sweep normalized to the arc's direction.
        """
        angle = normalize_radians(angle) - self.startAngle

        if (self.clockwise):
            if (angle > 0):
                angle -= TWO_PI
        elif (angle < 0):
            angle += TWO_PI

        return angle

    def containsAngle(self, angle):
        """
        Determine if the specified angle falls inside the range of the arc.

        Returns
        -------
        boolean
            True if the specified angle is in the range of the arc, False otherwise.
        """
        sweep = self.angleToSweep(angle)
        return (sweep >= self.sweep) if (self.clockwise) else (sweep <= self.sweep)

    def roundValues(self, numPlaces=ROUND_PLACES):
        """
        Round internal values.

        The following values are rounded and used to recompute the others:
        - cx, cy, radius, startAngle, sweep
        """
        self.cx = round(self.cx, numPlaces)
        self.cy = round(self.cy, numPlaces)
        self.radius = round(self.radius, numPlaces)
        self.startAngle = round(self.startAngle, numPlaces)
        self.sweep = round(self.sweep, numPlaces)
        self.compute()
        return self

    def __eq__(self, other):
        """Compare this object to another."""
        return (
            (other is not None) and
            (floatCmp(self.cx, other.cx) == 0) and
            (floatCmp(self.cy, other.cy) == 0) and
            (floatCmp(self.radius, other.radius) == 0) and
            (floatCmp(self.startAngle, other.startAngle) == 0) and
            (floatCmp(self.sweep, other.sweep) == 0)
        )

    def __repr__(self):
        """
        Return a string representation of this Arc.

        Returns
        -------
        string
            String representation, such as "Arc[(1, 2) r=5 start=0.4 sweep=1]".
        """
        return "{}[({}, {}) radius={} startAngle={} sweep={})]".format(
            self.__class__.__name__, self.cx, self.cy, self.radius, self.startAngle, self.sweep
        )

        # print(">> Arc: center     = ({}, {})".format(self.cx, self.cy))
        # print(">>      radius     = {}".format(self.radius))
        # print(">>      start      = ({}, {})".format(self.x1, self.y1))
        # print(">>      end        = ({}, {})".format(self.x2, self.y2))
        # print(">>      startAngle = {}".format(self.startAngle))
        # print(">>      endAngle   = {}".format(self.endAngle))
        # print(">>      sweep      = {}".format(self.sweep))
        # print(">>      length     = {}".format(self.length))
        # print(">>      clockwise  = {}".format(self.clockwise))
        # print(">>      major      = {}".format(self.major))
        # print(">>      bounds     = {}".format(self.bounds))
