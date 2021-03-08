# coding=utf-8
"""Unit tests for the Circle class."""

from __future__ import absolute_import

import math

from octoprint_excluderegion.Circle import Circle
from octoprint_excluderegion.Rectangle import Rectangle
from octoprint_excluderegion.Arc import Arc
from octoprint_excluderegion.LineSegment import LineSegment
from .utils import TestCase


class CircleTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for the Circle class."""

    expectedProperties = ["cx", "cy", "radius"]

    def test_default_constructor(self):
        """Test the constructor when passed no arguments."""
        unit = Circle()

        self.assertIsInstance(unit, Circle)
        self.assertEqual(unit.cx, 0, "cx should be 0")
        self.assertEqual(unit.cy, 0, "cy should be 0")
        self.assertEqual(unit.radius, 1, "radius should be 1")
        self.assertProperties(unit, CircleTests.expectedProperties)

    def test_constructor_kwargs(self):
        """Test the constructor when passed keyword arguments."""
        unit = Circle(cx=1, cy=2, radius=3)

        self.assertIsInstance(unit, Circle)
        self.assertEqual(unit.cx, 1, "cx should be 1")
        self.assertEqual(unit.cy, 2, "cy should be 2")
        self.assertEqual(unit.radius, 3, "radius should be 3")
        self.assertProperties(unit, CircleTests.expectedProperties)

    def test_constructor_args(self):
        """Test the constructor when passed non-keyword arguments."""
        with self.assertRaises(TypeError):
            Circle(1, 2, 3)  # pylint: disable=too-many-function-args

    def test_constructor_invalid_radius(self):
        """Test the constructor when passed an invalid radius value."""
        with self.assertRaises(ValueError):
            Circle(cx=1, cy=2, radius=0)

        with self.assertRaises(ValueError):
            Circle(cx=1, cy=2, radius=-1)

    def test_equal(self):
        """Test the __eq__ method."""
        # pylint: disable=invalid-name
        a = Circle(cx=1, cy=2, radius=3)
        b = Circle(cx=1, cy=2, radius=3)
        c = Circle(cx=1, cy=2, radius=9)
        d = Circle(cx=1, cy=9, radius=3)
        e = Circle(cx=9, cy=2, radius=3)

        self.assertTrue(a == b)
        self.assertTrue(b == a)
        self.assertFalse(a == c)
        self.assertFalse(a == d)
        self.assertFalse(a == e)
        self.assertFalse(a == None)
        self.assertFalse(None == a)

    def test_roundValues(self):
        """Test roundValues to ensure the values are rounded as expected."""
        unit = Circle(cx=1.123456789, cy=2.123456789, radius=3.123456789)

        unit.roundValues(6)

        self.assertEqual(1.123457, unit.cx)
        self.assertEqual(2.123457, unit.cy)
        self.assertEqual(3.123457, unit.radius)

    def test_containsPoint(self):
        """Test the containsPoint method."""
        unit = Circle(cx=10, cy=10, radius=3)

        self.assertTrue(unit.containsPoint(10, 10), "it should contain [10, 10]")
        self.assertTrue(unit.containsPoint(7, 10), "it should contain [7, 10]")
        self.assertTrue(unit.containsPoint(13, 10), "it should contain [13, 10]")
        self.assertTrue(unit.containsPoint(10, 7), "it should contain [10, 7]")
        self.assertTrue(unit.containsPoint(10, 13), "it should contain [10, 13]")
        self.assertTrue(unit.containsPoint(12, 12), "it should contain [12, 12]")
        self.assertFalse(unit.containsPoint(0, 0), "it should not contain [0, 0]")
        self.assertFalse(unit.containsPoint(6.9, 10), "it should not contain [6.9, 10]")

    def test_containsRect_no_intersection(self):
        """Test containsRect when the rectangle does not intersect."""
        rect = Rectangle(x1=0, y1=0, x2=5, y2=5)

        unit = Circle(cx=10, cy=10, radius=3)

        self.assertFalse(
            unit.containsRect(rect),
            "it should not contain a rect that does not intersect"
        )

    def test_containsRect_partial_intersection(self):
        """Test containsRect when the rectangle partially intersects."""
        rect = Rectangle(x1=9, y1=9, x2=13, y2=13)

        unit = Circle(cx=10, cy=10, radius=3)

        self.assertFalse(
            unit.containsRect(rect),
            "it should not contain a rect that partially intersects"
        )

    def test_containsRect_contained(self):
        """Test containsRect when the rectangle is fully contained."""
        rect = Rectangle(x1=9, y1=9, x2=11, y2=11)

        unit = Circle(cx=10, cy=10, radius=3)

        self.assertTrue(unit.containsRect(rect), "it should contain a rect that is fully contained")

    def test_lineSegmentDifference_outside(self):
        """Test lineSegmentDifference when fully outside (no line intersection)."""
        segment = LineSegment(x1=5, y1=6, x2=5, y2=6)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual([segment], result, "It should return the original segment")

        self.assertEqual(
            [False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_outside_vert(self):
        """Test lineSegmentDifference when fully outside (vertical line intersection)."""
        segment = LineSegment(x1=0, y1=3, x2=0, y2=2)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual([segment], result, "It should return the original segment")

        self.assertEqual(
            [False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_outside_perimiter_vert(self):
        """Test lineSegmentDifference when fully outside but touches the perimiter (vertical)."""
        segment = LineSegment(x1=0, y1=3, x2=0, y2=1)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual([segment], result, "It should return the original segment")

        self.assertEqual(
            [False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_outside_horiz(self):
        """Test lineSegmentDifference when fully outside (horizontal line intersection)."""
        segment = LineSegment(x1=3, y1=0, x2=2, y2=0)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual([segment], result, "It should return the original segment")

        self.assertEqual(
            [False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_outside_perimiter_horiz(self):
        """Test lineSegmentDifference when fully outside but touches the perimiter (vertical)."""
        segment = LineSegment(x1=3, y1=0, x2=1, y2=0)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual([segment], result, "It should return the original segment")

        self.assertEqual(
            [False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_contained_horiz_left_right(self):
        """Test lineSegmentDifference when fully contained (horizontal left to right)."""
        segment = LineSegment(x1=-1, y1=0, x2=1, y2=0)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual([segment], result, "It should return the original segment")

        self.assertEqual(
            [True],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_contained_horiz_right_left(self):
        """Test lineSegmentDifference when fully contained (horizontal right to left)."""
        segment = LineSegment(x1=1, y1=0, x2=-1, y2=0)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual([segment], result, "It should return a single item list")

        self.assertEqual(
            [True],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_contained_vert_bottom_top(self):
        """Test lineSegmentDifference when fully contained (vertical bottom to top)."""
        segment = LineSegment(x1=0, y1=-1, x2=0, y2=1)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual([segment], result, "It should return an single item list")

        self.assertEqual(
            [True],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_contained_vert_top_bottom(self):
        """Test lineSegmentDifference when fully contained (vertical top to bottom)."""
        segment = LineSegment(x1=0, y1=1, x2=0, y2=-1)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual([segment], result, "It should return a single item list")

        self.assertEqual(
            [True],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_inside_p2_right(self):
        """Test lineSegmentDifference when the p1 is contained and p2 is right."""
        segment = LineSegment(x1=0, y1=0, x2=2, y2=0)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual(
            [
                LineSegment(x1=0, y1=0, x2=1, y2=0),
                LineSegment(x1=1, y1=0, x2=2, y2=0)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [True, False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_left_p2_inside(self):
        """Test lineSegmentDifference when the p1 is left and p2 is contained."""
        segment = LineSegment(x1=-2, y1=0, x2=0, y2=0)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual(
            [
                LineSegment(x1=-2, y1=0, x2=-1, y2=0),
                LineSegment(x1=-1, y1=0, x2=0, y2=0)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [False, True],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_right_p2_inside(self):
        """Test lineSegmentDifference when p1 is right and p2 is contained."""
        segment = LineSegment(x1=2, y1=0, x2=0, y2=0)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual(
            [
                LineSegment(x1=2, y1=0, x2=1, y2=0),
                LineSegment(x1=1, y1=0, x2=0, y2=0)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [False, True],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_inside_p2_left(self):
        """Test lineSegmentDifference when p1 is contained and p2 is left."""
        segment = LineSegment(x1=0, y1=0, x2=-2, y2=0)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual(
            [
                LineSegment(x1=0, y1=0, x2=-1, y2=0),
                LineSegment(x1=-1, y1=0, x2=-2, y2=0)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [True, False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_left_p2_right_horiz(self):
        """Test lineSegmentDifference when p1 is left and p2 is right (horizontal)."""
        segment = LineSegment(x1=-2, y1=0, x2=2, y2=0)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual(
            [
                LineSegment(x1=-2, y1=0, x2=-1, y2=0),
                LineSegment(x1=-1, y1=0, x2=1, y2=0),
                LineSegment(x1=1, y1=0, x2=2, y2=0)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_right_p2_left_horiz(self):
        """Test lineSegmentDifference when p1 is right and p2 is left (horizontal)."""
        segment = LineSegment(x1=2, y1=0, x2=-2, y2=0)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual(
            [
                LineSegment(x1=2, y1=0, x2=1, y2=0),
                LineSegment(x1=1, y1=0, x2=-1, y2=0),
                LineSegment(x1=-1, y1=0, x2=-2, y2=0)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_above_p2_below_vert(self):
        """Test lineSegmentDifference when p1 is above and p2 is below (vertical)."""
        segment = LineSegment(x1=0, y1=2, x2=0, y2=-2)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual(
            [
                LineSegment(x1=0, y1=2, x2=0, y2=1),
                LineSegment(x1=0, y1=1, x2=0, y2=-1),
                LineSegment(x1=0, y1=-1, x2=0, y2=-2)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_below_p2_above_vert(self):
        """Test lineSegmentDifference when p1 is below and p2 is above (vertical)."""
        segment = LineSegment(x1=0, y1=2, x2=0, y2=-2)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        self.assertEqual(
            [
                LineSegment(x1=0, y1=2, x2=0, y2=1),
                LineSegment(x1=0, y1=1, x2=0, y2=-1),
                LineSegment(x1=0, y1=-1, x2=0, y2=-2)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_top_left_p2_bottom_right(self):
        """Test lineSegmentDifference when p1 is top-left and p2 is bottom-right."""
        segment = LineSegment(x1=-2, y1=2, x2=2, y2=-2)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        cosPi4 = math.cos(math.pi / 4)

        self.assertEqual(
            [
                LineSegment(x1=-2, y1=2, x2=-cosPi4, y2=cosPi4),
                LineSegment(x1=-cosPi4, y1=cosPi4, x2=cosPi4, y2=-cosPi4),
                LineSegment(x1=cosPi4, y1=-cosPi4, x2=2, y2=-2)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_bottom_left_p2_top_right(self):
        """Test lineSegmentDifference when p1 is bottom-left and p2 is top-right."""
        segment = LineSegment(x1=-2, y1=-2, x2=2, y2=2)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        cosPi4 = math.cos(math.pi / 4)

        self.assertEqual(
            [
                LineSegment(x1=-2, y1=-2, x2=-cosPi4, y2=-cosPi4),
                LineSegment(x1=-cosPi4, y1=-cosPi4, x2=cosPi4, y2=cosPi4),
                LineSegment(x1=cosPi4, y1=cosPi4, x2=2, y2=2)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_top_right_p2_bottom_left(self):
        """Test lineSegmentDifference when p1 is top-right and p2 is bottom-left."""
        segment = LineSegment(x1=2, y1=2, x2=-2, y2=-2)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        cosPi4 = math.cos(math.pi / 4)

        self.assertEqual(
            [
                LineSegment(x1=2, y1=2, x2=cosPi4, y2=cosPi4),
                LineSegment(x1=cosPi4, y1=cosPi4, x2=-cosPi4, y2=-cosPi4),
                LineSegment(x1=-cosPi4, y1=-cosPi4, x2=-2, y2=-2)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_lineSegmentDifference_p1_bottom_right_p2_top_left(self):
        """Test lineSegmentDifference when p1 is bottom-right and p2 is top-left."""
        segment = LineSegment(x1=2, y1=-2, x2=-2, y2=2)
        unit = Circle(cx=0, cy=0, radius=1)

        result = unit.lineSegmentDifference(segment)

        cosPi4 = math.cos(math.pi / 4)

        self.assertEqual(
            [
                LineSegment(x1=2, y1=-2, x2=cosPi4, y2=-cosPi4),
                LineSegment(x1=cosPi4, y1=-cosPi4, x2=-cosPi4, y2=cosPi4),
                LineSegment(x1=-cosPi4, y1=cosPi4, x2=-2, y2=2)
            ],
            result,
            "It should return a list containing the expected segments"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda l: l.intersects, result)),
            "Each segment should have the expected intersects value"
        )

    def test_arcDifference_p1_in_p2_out_CCW(self):
        """Test arcDifference when p1 is inside and p2 is outside (CCW)."""
        x = 10 * math.sin(math.acos(0.1))
        arc = Arc(cx=x, cy=0, radius=1, startAngle=math.pi, sweep=math.pi)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual(
            [
                Arc(cx=x, cy=0, radius=1, startAngle=math.pi, sweep=math.pi / 2),
                Arc(cx=x, cy=0, radius=1, startAngle=math.pi * 1.5, sweep=math.pi / 2)
            ],
            result,
            "It should return a list containing the expected arcs"
        )

        self.assertEqual(
            [True, False],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_p1_out_p2_in_CCW(self):
        """Test arcDifference when p1 is outside and p2 is inside (CCW)."""
        x = 10 * math.sin(math.acos(0.1))
        arc = Arc(cx=x, cy=0, radius=1, startAngle=0, sweep=math.pi)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual(
            [
                Arc(cx=x, cy=0, radius=1, startAngle=0, sweep=math.pi / 2),
                Arc(cx=x, cy=0, radius=1, startAngle=math.pi / 2, sweep=math.pi / 2)
            ],
            result,
            "It should return a list containing the expected arcs"
        )

        self.assertEqual(
            [False, True],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_p1_out_p2_out_CCW(self):
        """Test arcDifference when both p1 and p2 are outside (CCW)."""
        x = 10 * math.sin(math.acos(0.1))
        arc = Arc(cx=x, cy=0, radius=1, startAngle=0, sweep=math.pi * 2)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual(
            [
                Arc(cx=x, cy=0, radius=1, startAngle=0, sweep=math.pi / 2),
                Arc(cx=x, cy=0, radius=1, startAngle=math.pi / 2, sweep=math.pi),
                Arc(cx=x, cy=0, radius=1, startAngle=1.5 * math.pi, sweep=math.pi / 2),
            ],
            result,
            "It should return a list containing the expected arcs"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_p1_in_p2_in_CCW(self):
        """Test arcDifference when both p1 and p2 are inside (CCW)."""
        x = 10 * math.sin(math.acos(0.1))
        arc = Arc(cx=x, cy=0, radius=1, startAngle=math.pi, sweep=math.pi * 2)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual(
            [
                Arc(cx=x, cy=0, radius=1, startAngle=math.pi, sweep=math.pi / 2),
                Arc(cx=x, cy=0, radius=1, startAngle=1.5 * math.pi, sweep=math.pi),
                Arc(cx=x, cy=0, radius=1, startAngle=math.pi / 2, sweep=math.pi / 2)
            ],
            result,
            "It should return a list containing the expected arcs"
        )

        self.assertEqual(
            [True, False, True],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_p1_in_p2_out_CW(self):
        """Test arcDifference when p1 is inside and p2 is outside (CW)."""
        x = 10 * math.sin(math.acos(0.1))
        arc = Arc(cx=x, cy=0, radius=1, startAngle=math.pi, sweep=-math.pi)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual(
            [
                Arc(cx=x, cy=0, radius=1, startAngle=math.pi, sweep=-math.pi / 2),
                Arc(cx=x, cy=0, radius=1, startAngle=math.pi / 2, sweep=-math.pi / 2)
            ],
            result,
            "It should return a list containing the expected arcs"
        )

        self.assertEqual(
            [True, False],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_p1_out_p2_in_CW(self):
        """Test arcDifference when p1 is outside and p2 is inside (CW)."""
        x = 10 * math.sin(math.acos(0.1))
        arc = Arc(cx=x, cy=0, radius=1, startAngle=0, sweep=-math.pi)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual(
            [
                Arc(cx=x, cy=0, radius=1, startAngle=0, sweep=-math.pi / 2),
                Arc(cx=x, cy=0, radius=1, startAngle=-math.pi / 2, sweep=-math.pi / 2)
            ],
            result,
            "It should return a list containing the expected arcs"
        )

        self.assertEqual(
            [False, True],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_p1_out_p2_out_CW(self):
        """Test arcDifference when both p1 and p2 are outside (CW)."""
        x = 10 * math.sin(math.acos(0.1))
        arc = Arc(cx=x, cy=0, radius=1, startAngle=0, sweep=-math.pi * 2)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual(
            [
                Arc(cx=x, cy=0, radius=1, startAngle=0, sweep=-math.pi / 2),
                Arc(cx=x, cy=0, radius=1, startAngle=-math.pi / 2, sweep=-math.pi),
                Arc(cx=x, cy=0, radius=1, startAngle=math.pi / 2, sweep=-math.pi / 2)
            ],
            result,
            "It should return a list containing the expected arcs"
        )

        self.assertEqual(
            [False, True, False],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_p1_in_p2_in_C(self):
        """Test arcDifference when both p1 and p2 are inside (CW)."""
        x = 10 * math.sin(math.acos(0.1))
        arc = Arc(cx=x, cy=0, radius=1, startAngle=math.pi, sweep=-math.pi * 2)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual(
            [
                Arc(cx=x, cy=0, radius=1, startAngle=math.pi, sweep=-math.pi / 2),
                Arc(cx=x, cy=0, radius=1, startAngle=math.pi / 2, sweep=-math.pi),
                Arc(cx=x, cy=0, radius=1, startAngle=-math.pi / 2, sweep=-math.pi / 2)
            ],
            result,
            "It should return a list containing the expected arcs"
        )

        self.assertEqual(
            [True, False, True],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_non_intersecting_outside_1(self):
        """Test arcDifference if the circle containing the arc intersects, but the arc doesn't."""
        arc = Arc(cx=10, cy=0, radius=1, startAngle=-math.pi / 2, sweep=math.pi)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual([arc], result, "It should return a list containing the original arc")

        self.assertEqual(
            [False],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_non_intersecting_outside_2(self):
        """Test arcDifference when the circle containing the arc does not intersect."""
        arc = Arc(cx=20, cy=0, radius=1, startAngle=0, sweep=math.pi * 2)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual([arc], result, "It should return a list containing the original arc")

        self.assertEqual(
            [False],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_non_intersecting_outside_touching(self):
        """Test arcDifference when the arc touches the circle at one point."""
        arc = Arc(cx=11, cy=0, radius=1, startAngle=0, sweep=math.pi * 2)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual([arc], result, "It should return the original arc")

        self.assertEqual(
            [False],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_contains_bounding_box(self):
        """Test arcDifference when the arc's bounding box is contained."""
        arc = Arc(cx=5, cy=5, radius=1, startAngle=0, sweep=math.pi * 2)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual([arc], result, "It should return the original arc")

        self.assertEqual(
            [True],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_arcDifference_contains_no_bounding_box(self):
        """Test arcDifference when the arc is contained, but the bounding box is not."""
        sqrt2 = math.sqrt(2)
        arc = Arc(cx=1, cy=1, radius=10 - sqrt2, startAngle=0, sweep=math.pi * 2)
        unit = Circle(cx=0, cy=0, radius=10)

        result = unit.arcDifference(arc)

        self.assertEqual([arc], result, "It should return the original arc")

        self.assertEqual(
            [True],
            list(map(lambda a: a.intersects, result)),
            "Each arc should have the expected intersects value"
        )

    def test_geometryDifference_LineSegment(self):
        """Test geometryDifference when passed a LineSegment."""
        unit = Circle(cx=0, cy=0, radius=1)

        geometry = LineSegment(x1=1, y1=2, x2=3, y2=4)

        result = unit.geometryDifference(geometry)

        self.assertEqual([geometry], result, "It should return the original geometry")

        self.assertEqual(
            [False],
            list(map(lambda a: a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_geometryDifference_Arc(self):
        """Test geometryDifference when passed an Arc."""
        unit = Circle(cx=10, cy=0, radius=10)

        geometry = Arc(cx=0, cy=10, radius=10, startAngle=0, sweep=math.pi * 2)

        result = unit.geometryDifference(geometry)

        self.assertEqual(
            [
                Arc(cx=0, cy=10, radius=10, startAngle=0, sweep=math.pi * 1.5),
                Arc(cx=0, cy=10, radius=10, startAngle=math.pi * 1.5, sweep=math.pi / 2)
            ],
            result, "It should return the original geometry"
        )

        self.assertEqual(
            [False, True],
            list(map(lambda a: a.intersects, result)),
            "Each geometry should have the expected intersects value"
        )

    def test_geometryDifference_other(self):
        """Test geometryDifference when passed an unsupported type."""
        unit = Circle(cx=0, cy=0, radius=1)

        with self.assertRaises(TypeError):
            unit.geometryDifference(1234)
