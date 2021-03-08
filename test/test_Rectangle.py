# coding=utf-8
"""Unit tests for the Rectangle class."""

from __future__ import absolute_import

import math

from octoprint_excluderegion.Arc import Arc
from octoprint_excluderegion.Rectangle import Rectangle
from octoprint_excluderegion.LineSegment import LineSegment
from .utils import TestCase


class RectangleTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for the Rectangle class."""

    expectedProperties = ["x1", "y1", "x2", "y2"]

    def test_default_constructor(self):
        """Test the constructor when passed no arguments."""
        unit = Rectangle()

        self.assertIsInstance(unit, Rectangle)
        self.assertEqual(unit.x1, 0, "x1 should be 0")
        self.assertEqual(unit.y1, 0, "y1 should be 0")
        self.assertEqual(unit.x2, 0, "x2 should be 0")
        self.assertEqual(unit.y2, 0, "y2 should be 0")
        self.assertProperties(unit, RectangleTests.expectedProperties)

    def test_constructor_kwargs(self):
        """Test the constructor when passed keyword arguments."""
        unit = Rectangle(x1=3, y1=4, x2=1, y2=2)

        self.assertIsInstance(unit, Rectangle)
        self.assertEqual(unit.x1, 1, "x1 should be 1")
        self.assertEqual(unit.y1, 2, "y1 should be 2")
        self.assertEqual(unit.x2, 3, "x2 should be 3")
        self.assertEqual(unit.y2, 4, "y2 should be 2")
        self.assertProperties(unit, RectangleTests.expectedProperties)

    def test_constructor_args(self):
        """Test the constructor when passed non-keyword arguments."""
        with self.assertRaises(TypeError):
            Rectangle(1, 2, 3, 4)  # pylint: disable=too-many-function-args

    def test_equal(self):
        """Test the __eq__ method."""
        # pylint: disable=invalid-name
        a = Rectangle(x1=1, y1=2, x2=3, y2=4)
        b = Rectangle(x1=1, y1=2, x2=3, y2=4)
        c = Rectangle(x1=1, y1=2, x2=3, y2=0)
        d = Rectangle(x1=1, y1=2, x2=0, y2=4)
        e = Rectangle(x1=1, y1=0, x2=3, y2=4)
        f = Rectangle(x1=0, y1=2, x2=3, y2=4)

        self.assertTrue(a == b)
        self.assertTrue(b == a)
        self.assertFalse(a == c)
        self.assertFalse(a == d)
        self.assertFalse(a == e)
        self.assertFalse(a == f)
        self.assertFalse(a == None)
        self.assertFalse(None == a)

    def test_roundValues(self):
        """Test roundValues to ensure the values are rounded as expected."""
        unit = Rectangle(x1=1.123456789, y1=2.123456789, x2=3.123456789, y2=4.123456789)

        unit.roundValues(6)

        self.assertEqual(1.123457, unit.x1)
        self.assertEqual(2.123457, unit.y1)
        self.assertEqual(3.123457, unit.x2)
        self.assertEqual(4.123457, unit.y2)

    def test_computeSegmentOutCode(self):
        """Test computeSegmentOutCode scenarios."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)

        self.assertEqual(0, unit.computeSegmentOutCode(0, 0))
        self.assertEqual(0, unit.computeSegmentOutCode(10, 10))

        self.assertEqual(1, unit.computeSegmentOutCode(-1, 5))    # Left
        self.assertEqual(5, unit.computeSegmentOutCode(-1, -1))   # Below-Left
        self.assertEqual(9, unit.computeSegmentOutCode(-1, 11))   # Above-Left

        self.assertEqual(2, unit.computeSegmentOutCode(11, 5))    # Right
        self.assertEqual(6, unit.computeSegmentOutCode(11, -1))   # Below-Right
        self.assertEqual(10, unit.computeSegmentOutCode(11, 11))  # Above-Right

        self.assertEqual(4, unit.computeSegmentOutCode(5, -1))    # Below
        self.assertEqual(8, unit.computeSegmentOutCode(5, 11))    # Above

    def test_lineSegmentDifference_contained(self):
        """Test lineSegmentDifference when fully contained."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        lineSeg = LineSegment(x1=0, y1=0, x2=10, y2=10)

        result = unit.lineSegmentDifference(lineSeg)

        self.assertEqual([lineSeg], result, "It should return the original geometry")

        self.assertEqual(
            [True],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_inside_p2_right(self):
        """Test lineSegmentDifference when the p1 is contained and p2 is right."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        lineSeg = LineSegment(x1=5, y1=5, x2=20, y2=5)

        result = unit.lineSegmentDifference(lineSeg)

        self.assertEqual(
            [
                LineSegment(x1=5, y1=5, x2=10, y2=5),
                LineSegment(x1=10, y1=5, x2=20, y2=5)
            ],
            result,
            "It should return the expected segments"
        )

        self.assertEqual(
            [True, False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_inside_p2_left(self):
        """Test lineSegmentDifference when the p1 is contained and p2 is left."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        lineSeg = LineSegment(x1=5, y1=5, x2=-20, y2=5)

        result = unit.lineSegmentDifference(lineSeg)

        self.assertEqual(
            [
                LineSegment(x1=5, y1=5, x2=0, y2=5),
                LineSegment(x1=0, y1=5, x2=-20, y2=5)
            ],
            result,
            "It should return the expected segments"
        )

        self.assertEqual(
            [True, False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_right_p2_inside(self):
        """Test lineSegmentDifference when p1 is right and p2 is contained."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        lineSeg = LineSegment(x1=20, y1=5, x2=5, y2=5)

        result = unit.lineSegmentDifference(lineSeg)

        self.assertEqual(
            [
                LineSegment(x1=20, y1=5, x2=10, y2=5),
                LineSegment(x1=10, y1=5, x2=5, y2=5)
            ],
            result,
            "It should return the expected segments"
        )

        self.assertEqual(
            [False, True],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_left_p2_inside(self):
        """Test lineSegmentDifference when p1 is left and p2 is contained."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        lineSeg = LineSegment(x1=-10, y1=5, x2=5, y2=5)

        result = unit.lineSegmentDifference(lineSeg)

        self.assertEqual(
            [
                LineSegment(x1=-10, y1=5, x2=0, y2=5),
                LineSegment(x1=0, y1=5, x2=5, y2=5)
            ],
            result,
            "It should return the expected segments"
        )

        self.assertEqual(
            [False, True],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_p2_outside_no_intersection(self):
        """Test lineSegmentDifference when no intersection."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        lineSeg = LineSegment(x1=0, y1=20, x2=10, y2=20)

        result = unit.lineSegmentDifference(lineSeg)

        self.assertEqual([lineSeg], result, "It should return (0,20)-(10,20)")

        self.assertEqual(
            [False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_p2_outside_intersects_ltr(self):
        """Test lineSegmentDifference when both points outside and intersects left to right."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        lineSeg = LineSegment(x1=-10, y1=5, x2=20, y2=5)

        result = unit.lineSegmentDifference(lineSeg)

        self.assertEqual(
            [
                LineSegment(x1=-10, y1=5, x2=0, y2=5),
                LineSegment(x1=0, y1=5, x2=10, y2=5),
                LineSegment(x1=10, y1=5, x2=20, y2=5)
            ],
            result, "It should return the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_p2_outside_intersects_rtl(self):
        """Test lineSegmentDifference when both points outside and intersects right to left."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        lineSeg = LineSegment(x1=20, y1=5, x2=-10, y2=5)

        result = unit.lineSegmentDifference(lineSeg)

        self.assertEqual(
            [
                LineSegment(x1=20, y1=5, x2=10, y2=5),
                LineSegment(x1=10, y1=5, x2=0, y2=5),
                LineSegment(x1=0, y1=5, x2=-10, y2=5)
            ],
            result, "It should return the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_p2_outside_intersects_btt(self):
        """Test lineSegmentDifference when both points outside and intersects bottom to top."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        lineSeg = LineSegment(x1=5, y1=-10, x2=5, y2=20)

        result = unit.lineSegmentDifference(lineSeg)

        self.assertEqual(
            [
                LineSegment(x1=5, y1=-10, x2=5, y2=0),
                LineSegment(x1=5, y1=0, x2=5, y2=10),
                LineSegment(x1=5, y1=10, x2=5, y2=20)
            ],
            result, "It should return the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_p2_outside_intersects_ttb(self):
        """Test lineSegmentDifference when both points outside and intersects top to bottom."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        lineSeg = LineSegment(x1=5, y1=20, x2=5, y2=-10)

        result = unit.lineSegmentDifference(lineSeg)

        self.assertEqual(
            [
                LineSegment(x1=5, y1=20, x2=5, y2=10),
                LineSegment(x1=5, y1=10, x2=5, y2=0),
                LineSegment(x1=5, y1=0, x2=5, y2=-10)
            ],
            result, "It should return the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_intersectsRect(self):
        """Test the intersectsRect method."""
        sharesRight = Rectangle(x1=10, y1=0, x2=20, y2=10)
        sharesLeft = Rectangle(x1=-10, y1=0, x2=0, y2=10)
        sharesTop = Rectangle(x1=0, y1=20, x2=10, y2=10)
        sharesBottom = Rectangle(x1=0, y1=0, x2=10, y2=-10)

        inside = Rectangle(x1=1, y1=1, x2=9, y2=9)
        coversLarger = Rectangle(x1=-1, y1=-1, x2=11, y2=11)

        outRight = Rectangle(x1=1, y1=1, x2=11, y2=9)
        outLeft = Rectangle(x1=-1, y1=1, x2=9, y2=9)
        outTop = Rectangle(x1=1, y1=1, x2=9, y2=11)
        outBottom = Rectangle(x1=1, y1=-1, x2=9, y2=9)

        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)

        self.assertTrue(unit.intersectsRect(unit), "self")
        self.assertTrue(unit.intersectsRect(inside))
        self.assertTrue(unit.intersectsRect(coversLarger))
        self.assertTrue(unit.intersectsRect(outRight))
        self.assertTrue(unit.intersectsRect(outLeft))
        self.assertTrue(unit.intersectsRect(outTop))
        self.assertTrue(unit.intersectsRect(outBottom))

        self.assertFalse(unit.intersectsRect(sharesRight))
        self.assertFalse(unit.intersectsRect(sharesLeft))
        self.assertFalse(unit.intersectsRect(sharesTop))
        self.assertFalse(unit.intersectsRect(sharesBottom))

    def test_computeArcVertIntAngles_circle_dx_gt_radius(self):
        """Test computeArcVertIntAngles when the radius is less than the distance to the line."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=5, radius=4, startAngle=0, sweep=math.pi * 2)

        result = unit.computeArcVertIntAngles(0, arc)

        self.assertEqual([], result, "no intersection")

    def test_computeArcVertIntAngles_circle_dx_eq_radius(self):
        """Test computeArcVertIntAngles when the radius is equal to the distance to the line."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=5, radius=5, startAngle=0, sweep=math.pi * 2)

        result = unit.computeArcVertIntAngles(0, arc)

        self.assertEqual([math.pi], result, "single angle of intersection")

    def test_computeArcVertIntAngles_circle_dx_eq_cx(self):
        """Test computeArcVertIntAngles when the center point is on the line."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=0, cy=5, radius=5, startAngle=0, sweep=math.pi * 2)

        result = unit.computeArcVertIntAngles(0, arc)

        self.assertEqual([math.pi/2, math.pi * 1.5], result, "two angles of intersection")

    def test_computeArcVertIntAngles_circle_x_outside_range(self):
        """Test computeArcVertIntAngles when intersections are beyond the rectangle's range."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=5, radius=10, startAngle=0, sweep=math.pi * 2)

        result = unit.computeArcVertIntAngles(0, arc)

        self.assertEqual([], result, "no intersection, outside rect")

    def test_computeArcVertIntAngles_arc_first_int_only(self):
        """Test computeArcVertIntAngles if only the first angle is in the arc's range."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=0, cy=5, radius=1, startAngle=0, sweep=math.pi)

        result = unit.computeArcVertIntAngles(0, arc)

        self.assertEqual([math.pi/2], result, "one intersection at pi/2")

    def test_computeArcVertIntAngles_arc_second_int_only(self):
        """Test computeArcVertIntAngles if only the second angle is in the arc's range."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=0, cy=5, radius=1, startAngle=0, sweep=-math.pi)

        result = unit.computeArcVertIntAngles(0, arc)

        self.assertEqual([-math.pi/2], result, "one intersection at -pi/2")

    def test_computeArcHorizIntAngles_circle_dy_gt_radius(self):
        """Test computeArcHorizIntAngles when the radius is less than the distance to the line."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=5, radius=4, startAngle=0, sweep=math.pi * 2)

        result = unit.computeArcHorizIntAngles(0, arc)

        self.assertEqual([], result, "no intersection")

    def test_computeArcHorizIntAngles_circle_dy_eq_radius(self):
        """Test computeArcHorizIntAngles when the radius is equal to the distance to the line."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=5, radius=5, startAngle=0, sweep=math.pi * 2)

        result = unit.computeArcHorizIntAngles(0, arc)

        self.assertEqual([math.pi * 1.5], result, "single angle of intersection")

    def test_computeArcHorizIntAngles_circle_dy_eq_cx(self):
        """Test computeArcHorizIntAngles when the center point is on the line."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=0, radius=5, startAngle=0, sweep=math.pi * 2)

        result = unit.computeArcHorizIntAngles(0, arc)

        self.assertEqual([0, math.pi], result, "two angles of intersection")

    def test_computeArcHorizIntAngles_circle_y_outside_range(self):
        """Test computeArcHorizIntAngles when intersections are beyond the rectangle's range."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=5, radius=10, startAngle=0, sweep=math.pi * 2)

        result = unit.computeArcHorizIntAngles(0, arc)

        self.assertEqual([], result, "no intersection, outside rect")

    def test_computeArcHorizIntAngles_arc_first_int_only(self):
        """Test computeArcHorizIntAngles if only the first angle is in the arc's range."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=0, radius=1, startAngle=math.pi/2, sweep=math.pi)

        result = unit.computeArcHorizIntAngles(0, arc)

        self.assertEqual([math.pi/2], result, "one intersection at pi/2")

    def test_computeArcHorizIntAngles_arc_second_int_only(self):
        """Test computeArcHorizIntAngles if only the second angle is in the arc's range."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=0, radius=1, startAngle=math.pi/2, sweep=-math.pi)

        result = unit.computeArcHorizIntAngles(0, arc)

        self.assertEqual([-math.pi/2], result, "one intersection at -pi/2")

    def test_arcDifference_contained(self):
        """Test arcDifference when the arc is fully contained."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=5, radius=5, startAngle=0, sweep=math.pi * 2)

        result = unit.arcDifference(arc)

        self.assertEqual([arc], result, "It should return the original arc")

        self.assertEqual(
            [True],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_arcDifference_outside(self):
        """Test arcDifference when the arc is fully outside."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=15, cy=5, radius=5, startAngle=0, sweep=math.pi * 2)

        result = unit.arcDifference(arc)

        self.assertEqual([arc], result, "It should return the original arc")

        self.assertEqual(
            [False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_arcDifference_intersects_left_once(self):
        """Test arcDifference when the arc intersects the left side one time."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=0, cy=0, radius=5, startAngle=math.pi / 4, sweep=math.pi)
        expected = [
            Arc(cx=0, cy=0, radius=5, startAngle=math.pi / 4, sweep=math.pi / 4),
            Arc(cx=0, cy=0, radius=5, startAngle=math.pi / 2, sweep=math.pi * 0.75)
        ]

        result = unit.arcDifference(arc)

        self.assertEqual(expected, result, "It should return the expected arc")

        self.assertEqual(
            [True, False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_arcDifference_intersects_top_once(self):
        """Test arcDifference when the arc intersects the top side one time."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=0, cy=10, radius=5, startAngle=math.pi * 0.75, sweep=-math.pi)
        expected = [
            Arc(cx=0, cy=10, radius=5, startAngle=math.pi * 0.75, sweep=-math.pi * 0.75),
            Arc(cx=0, cy=10, radius=5, startAngle=0, sweep=-math.pi / 4)
        ]

        result = unit.arcDifference(arc)

        self.assertEqual(expected, result, "It should return the expected arc")

        self.assertEqual(
            [False, True],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_arcDifference_intersects_right_once(self):
        """Test arcDifference when the arc intersects the right side one time."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=10, cy=0, radius=5, startAngle=0, sweep=math.pi * 0.75)
        expected = [
            Arc(cx=10, cy=0, radius=5, startAngle=0, sweep=math.pi / 2),
            Arc(cx=10, cy=0, radius=5, startAngle=math.pi / 2, sweep=math.pi / 4)
        ]

        result = unit.arcDifference(arc)

        self.assertEqual(expected, result, "It should return the expected arc")

        self.assertEqual(
            [False, True],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_arcDifference_intersects_bottom_once(self):
        """Test arcDifference when the arc intersects the bottom side one time."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=10, cy=0, radius=5, startAngle=math.pi * 0.75, sweep=math.pi)
        expected = [
            Arc(cx=10, cy=0, radius=5, startAngle=math.pi * 0.75, sweep=math.pi / 4),
            Arc(cx=10, cy=0, radius=5, startAngle=math.pi, sweep=math.pi * 0.75)
        ]

        result = unit.arcDifference(arc)

        self.assertEqual(expected, result, "It should return the expected arc")

        self.assertEqual(
            [True, False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_arcDifference_intersects_left_twice(self):
        """Test arcDifference when the arc intersects the left side twice."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=0, cy=5, radius=1, startAngle=0, sweep=math.pi * 2)
        expected = [
            Arc(cx=0, cy=5, radius=1, startAngle=0, sweep=math.pi / 2),
            Arc(cx=0, cy=5, radius=1, startAngle=math.pi / 2, sweep=math.pi),
            Arc(cx=0, cy=5, radius=1, startAngle=math.pi * 1.5, sweep=math.pi / 2)
        ]

        result = unit.arcDifference(arc)

        self.assertEqual(expected, result, "It should return the expected arc")

        self.assertEqual(
            [True, False, True],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_arcDifference_intersects_top_twice(self):
        """Test arcDifference when the arc intersects the top side twice."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=10, radius=1, startAngle=0, sweep=math.pi * 2)

        expected = [
            Arc(cx=5, cy=10, radius=1, startAngle=0, sweep=math.pi),
            Arc(cx=5, cy=10, radius=1, startAngle=math.pi, sweep=math.pi)
        ]

        result = unit.arcDifference(arc)

        self.assertEqual(expected, result, "It should return the expected arc")
        
        self.assertEqual(
            [False, True],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_arcDifference_intersects_right_twice(self):
        """Test arcDifference when the arc intersects the right side twice."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=10, cy=5, radius=1, startAngle=0, sweep=math.pi * 2)

        expected = [
            Arc(cx=10, cy=5, radius=1, startAngle=0, sweep=math.pi / 2),
            Arc(cx=10, cy=5, radius=1, startAngle=math.pi / 2, sweep=math.pi),
            Arc(cx=10, cy=5, radius=1, startAngle=math.pi * 1.5, sweep=math.pi / 2)
        ]

        result = unit.arcDifference(arc)

        self.assertEqual(expected, result, "It should return the expected arcs")

        self.assertEqual(
            [False, True, False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_arcDifference_intersects_bottom_twice(self):
        """Test arcDifference when the arc intersects the bottom side twice."""
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=0, radius=1, startAngle=math.pi / 2, sweep=-math.pi * 2)

        expected = [
            Arc(cx=5, cy=0, radius=1, startAngle=math.pi / 2, sweep=-math.pi / 2),
            Arc(cx=5, cy=0, radius=1, startAngle=0, sweep=-math.pi),
            Arc(cx=5, cy=0, radius=1, startAngle=math.pi, sweep=-math.pi / 2)
        ]

        result = unit.arcDifference(arc)

        self.assertEqual(expected, result, "It should return the expected arc")

        self.assertEqual(
            [True, False, True],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    # intersects the all edges two times
    def test_arcDifference_intersects_max(self):
        """Test arcDifference when the arc intersects the max number of times."""
        numPlaces = 9

        sr65 = math.sqrt(6 * 6 - 5 * 5)
        sweep1 = math.atan2(sr65, 5)
        sweep2 = 2 * sweep1
        exsweep = math.atan2(5, sr65) - sweep1

        expected = [
            Arc(cx=5, cy=5, radius=6, startAngle=0, sweep=sweep1),
            Arc(cx=5, cy=5, radius=6, startAngle=sweep1, sweep=exsweep),
            Arc(cx=5, cy=5, radius=6, startAngle=math.atan2(5, sr65), sweep=sweep2),
            Arc(cx=5, cy=5, radius=6, startAngle=sweep1 + exsweep + sweep2, sweep=exsweep),
            Arc(cx=5, cy=5, radius=6, startAngle=math.atan2(sr65, -5), sweep=sweep2),
            Arc(cx=5, cy=5, radius=6, startAngle=sweep1 + 2 * (exsweep + sweep2), sweep=exsweep),
            Arc(cx=5, cy=5, radius=6, startAngle=math.atan2(-5, -sr65), sweep=sweep2),
            Arc(cx=5, cy=5, radius=6, startAngle=sweep1 + 3 * (exsweep + sweep2), sweep=exsweep),
            Arc(cx=5, cy=5, radius=6, startAngle=math.atan2(-sr65, 5), sweep=sweep1)
        ]

        # --
        unit = Rectangle(x1=0, y1=0, x2=10, y2=10)
        arc = Arc(cx=5, cy=5, radius=6, startAngle=0, sweep=math.pi * 2)

        result = unit.arcDifference(arc)

        self.assertEqual(expected, result, "It should return 5 arcs")

        self.assertEqual(
            [False, True, False, True, False, True, False, True, False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_geometryDifference_LineSegment(self):
        """Test geometryDifference when passed a LineSegment."""
        unit = Rectangle(x1=0, y1=0, x2=1, y2=1)

        geometry = LineSegment(x1=1, y1=2, x2=3, y2=4)

        result = unit.geometryDifference(geometry)

        self.assertEqual([geometry], result, "It should return the original geometry")

        self.assertEqual(
            [False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_geometryDifference_Arc(self):
        """Test geometryDifference when passed an Arc."""
        unit = Rectangle(x1=0, y1=0, x2=1, y2=1)

        geometry = Arc(cx=10, cy=10, radius=1, startAngle=0, sweep=math.pi)

        result = unit.geometryDifference(geometry)

        self.assertEqual([geometry], result, "It should return the original geometry")

        self.assertEqual(
            [False],
            list(map(lambda a : a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_geometryDifference_other(self):
        """Test geometryDifference when passed an unsupported type."""
        unit = Rectangle(x1=0, y1=0, x2=1, y2=1)

        with self.assertRaises(TypeError):
            unit.geometryDifference(1234)
