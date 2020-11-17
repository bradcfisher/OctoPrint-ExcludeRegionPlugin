# coding=utf-8

"""Unit tests for the CircularRegion class."""

from __future__ import absolute_import

from octoprint_excluderegion.CircularRegion import CircularRegion
from octoprint_excluderegion.RectangularRegion import RectangularRegion
from .utils import TestCase


class CircularRegionTests(TestCase):
    """Unit tests for the CircularRegion class."""

    expectedProperties = ["cx", "cy", "r", "id"]

    def test_default_constructor(self):
        """Test the constructor when passed no arguments."""
        unit = CircularRegion()

        self.assertIsInstance(unit, CircularRegion)
        self.assertEqual(unit.cx, 0, "cx should be 0")
        self.assertEqual(unit.cy, 0, "cy should be 0")
        self.assertEqual(unit.r, 0, "r should be 0")
        self.assertRegex(unit.id, "^[-0-9a-fA-F]{36}$", "id should be a UUID string")
        self.assertProperties(unit, CircularRegionTests.expectedProperties)

    def test_constructor_kwargs(self):
        """Test the constructor when passed keyword arguments."""
        unit = CircularRegion(cx=1, cy=2, r=3, id="myTestId")

        self.assertEqual(unit.cx, 1, "cx should be 1")
        self.assertEqual(unit.cy, 2, "cy should be 2")
        self.assertEqual(unit.r, 3, "r should be 3")
        self.assertEqual(unit.id, "myTestId", "id should be 'myTestId'")
        self.assertProperties(unit, CircularRegionTests.expectedProperties)

    def test_copy_constructor(self):
        """Test the constructor when passed a CircularRegion instance."""
        toCopy = CircularRegion(cx=1, cy=2, r=3, id="myTestId")

        unit = CircularRegion(toCopy)

        self.assertEqual(unit.cx, 1, "cx should be 1")
        self.assertEqual(unit.cy, 2, "cy should be 2")
        self.assertEqual(unit.r, 3, "r should be 3")
        self.assertEqual(unit.id, "myTestId", "id should be 'myTestId'")
        self.assertProperties(unit, CircularRegionTests.expectedProperties)

    def test_constructor_exception(self):
        """Test the constructor when passed a single non-CircularRegion parameter."""
        with self.assertRaises(AssertionError):
            CircularRegion("NotACircularRegionInstance")

    def test_containsPoint(self):
        """Test the containsPoint method."""
        unit = CircularRegion(cx=10, cy=10, r=3)

        self.assertTrue(unit.containsPoint(10, 10), "it should contain [10, 10]")
        self.assertTrue(unit.containsPoint(7, 10), "it should contain [7, 10]")
        self.assertTrue(unit.containsPoint(13, 10), "it should contain [13, 10]")
        self.assertTrue(unit.containsPoint(10, 7), "it should contain [10, 7]")
        self.assertTrue(unit.containsPoint(10, 13), "it should contain [10, 13]")
        self.assertTrue(unit.containsPoint(12, 12), "it should contain [12, 12]")

        self.assertFalse(unit.containsPoint(0, 0), "it should not contain [0, 0]")
        self.assertFalse(unit.containsPoint(6.9, 10), "it should not contain [6.9, 10]")

    def test_containsRegion_Rectangular(self):
        """Test the containsRegion method when passed a RectangularRegion."""
        unit = CircularRegion(cx=10, cy=10, r=3)

        self.assertTrue(
            unit.containsRegion(RectangularRegion(x1=9, y1=9, x2=11, y2=11)),
            "it should contain Rect(9,9-11,11)"
        )

        self.assertFalse(
            unit.containsRegion(RectangularRegion(x1=7.5, y1=7.5, x2=10, y2=10)),
            "it should not contain Rect(7.5,7.5-10,10)"
        )
        self.assertFalse(
            unit.containsRegion(RectangularRegion(x1=7.5, y1=12.5, x2=10, y2=10)),
            "it should not contain Rect(7.5,12.5-10,10)"
        )
        self.assertFalse(
            unit.containsRegion(RectangularRegion(x1=12.5, y1=7.5, x2=10, y2=10)),
            "it should not contain Rect(12.5,7.5-10,10)"
        )
        self.assertFalse(
            unit.containsRegion(RectangularRegion(x1=7.5, y1=12.5, x2=10, y2=10)),
            "it should not contain Rect(7.5,12.5-10,10)"
        )

        self.assertFalse(
            unit.containsRegion(RectangularRegion(x1=0, y1=0, x2=1, y2=1)),
            "it should not contain a RectangularRegion completely outside"
        )
        self.assertFalse(
            unit.containsRegion(RectangularRegion(x1=0, y1=0, x2=20, y2=20)),
            "it should not contain a RectangularRegion containing this region"
        )

    def test_containsRegion_Circular(self):
        """Test the containsRegion method when passed a CircularRegion."""
        unit = CircularRegion(cx=10, cy=10, r=3)

        self.assertTrue(unit.containsRegion(unit), "it should contain itself")
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=10, cy=10, r=3)),
            "it should contain a CircularRegion representing the same geometric region"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=8, cy=10, r=0.5)),
            "it should contain a CircularRegion inside"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=8, cy=10, r=1)),
            "it should contain a CircularRegion inside, but tangent to the circle"
        )

        self.assertFalse(
            unit.containsRegion(CircularRegion(cx=8, cy=10, r=1.1)),
            "it should not contain a CircularRegion that extends outside"
        )
        self.assertFalse(
            unit.containsRegion(CircularRegion(cx=1, cy=1, r=1)),
            "it should not contain a CircularRegion completely outside"
        )
        self.assertFalse(
            unit.containsRegion(CircularRegion(cx=10, cy=10, r=5)),
            "it should not contain a CircularRegion containing this region"
        )

    def test_containsRegion_NotRegion(self):
        """Test the containsRegion method when passed an unsupported type."""
        unit = CircularRegion(cx=10, cy=10, r=3)

        with self.assertRaises(ValueError):
            unit.containsRegion("NotARegionInstance")
