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
