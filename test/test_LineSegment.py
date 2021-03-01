# coding=utf-8
"""Unit tests for the LineSegment class."""

from __future__ import absolute_import

import math

from octoprint_excluderegion.LineSegment import LineSegment
from octoprint_excluderegion.Rectangle import Rectangle
from .utils import TestCase


class LineSegmentTests(TestCase):
    """Unit tests for the LineSegment class."""

    expectedProperties = ["x1", "y1", "x2", "y2", "length", "bounds"]

    def test_default_constructor(self):
        """Test the constructor when passed no arguments."""
        unit = LineSegment()

        self.assertIsInstance(unit, LineSegment)
        self.assertEqual(unit.x1, 0, "x1 should be 0")
        self.assertEqual(unit.y1, 0, "y1 should be 0")
        self.assertEqual(unit.x2, 0, "x2 should be 0")
        self.assertEqual(unit.y2, 0, "y2 should be 0")
        self.assertEqual(unit.length, 0, "length should be 0")
        self.assertEqual(
            unit.bounds,
            Rectangle(x1=0, y1=0, x2=0, y2=0),
            "bounds should be (0,0)-(0,0)"
        )
        self.assertProperties(unit, LineSegmentTests.expectedProperties)

    def test_constructor_kwargs(self):
        """Test the constructor when passed keyword arguments."""
        unit = LineSegment(x1=3, y1=4, x2=1, y2=2)

        self.assertIsInstance(unit, LineSegment)
        self.assertEqual(unit.x1, 3, "x1 should be 1")
        self.assertEqual(unit.y1, 4, "y1 should be 2")
        self.assertEqual(unit.x2, 1, "x2 should be 3")
        self.assertEqual(unit.y2, 2, "y2 should be 2")
        self.assertEqual(unit.length, math.sqrt(8), "length should be sqrt(8)")
        self.assertEqual(
            unit.bounds,
            Rectangle(x1=1, y1=2, x2=3, y2=4),
            "bounds should be (1,2)-(3,4)"
        )
        self.assertProperties(unit, LineSegmentTests.expectedProperties)

    def test_constructor_args(self):
        """Test the constructor when passed non-keyword arguments."""
        with self.assertRaises(TypeError):
            LineSegment(1, 2, 3, 4)  # pylint: disable=too-many-function-args

    def test_equal(self):
        """Test the __eq__ method."""
        # pylint: disable=invalid-name
        a = LineSegment(x1=1, y1=2, x2=3, y2=4)
        b = LineSegment(x1=1, y1=2, x2=3, y2=4)
        c = LineSegment(x1=1, y1=2, x2=3, y2=0)
        d = LineSegment(x1=1, y1=2, x2=0, y2=4)
        e = LineSegment(x1=1, y1=0, x2=3, y2=4)
        f = LineSegment(x1=0, y1=2, x2=3, y2=4)

        self.assertTrue(a == b)
        self.assertTrue(b == a)
        self.assertFalse(a == c)
        self.assertFalse(a == d)
        self.assertFalse(a == e)
        self.assertFalse(a == f)

    def test_roundValues(self):
        """Test the roundValues method."""
        unit = LineSegment(x1=0.123456789, y1=1.123456789, x2=2.123456789, y2=3.123456789)

        unit.roundValues(6)

        self.assertEqual(
            LineSegment(x1=0.123457, y1=1.123457, x2=2.123457, y2=3.123457),
            unit,
            "It should round the values"
        )

    def test_pointInSegment(self):
        """Test pointInSegment when the point is to the left."""
        unit = LineSegment(x1=0, y1=0, x2=1, y2=1)
        
        self.assertTrue(unit.pointInSegment(0, 0))       # p1
        self.assertTrue(unit.pointInSegment(1, 1))       # p2
        self.assertTrue(unit.pointInSegment(0.5, 0.5))   # inside

        self.assertFalse(unit.pointInSegment(-1, -1))    # left
        self.assertFalse(unit.pointInSegment(2, 2))      # right
        self.assertFalse(unit.pointInSegment(0.5, 0.25)) # not colinear
