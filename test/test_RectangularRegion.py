# coding=utf-8
"""Unit tests for the RectangularRegion class."""

from __future__ import absolute_import

from octoprint_excluderegion.CircularRegion import CircularRegion
from octoprint_excluderegion.RectangularRegion import RectangularRegion
from .utils import TestCase


class RectangularRegionTests(TestCase):
    """Unit tests for the RectangularRegion class."""

    expectedProperties = ["x1", "y1", "x2", "y2", "id"]

    def test_default_constructor(self):
        """Test the constructor when passed no arguments."""
        unit = RectangularRegion()

        self.assertIsInstance(unit, RectangularRegion)
        self.assertEqual(unit.x1, 0, "x1 should be 0")
        self.assertEqual(unit.y1, 0, "y1 should be 0")
        self.assertEqual(unit.x2, 0, "x2 should be 0")
        self.assertEqual(unit.y2, 0, "y2 should be 0")
        if sys.version_info[0] < 3:
            self.assertRegexpMatches(unit.id, "^[-0-9a-fA-F]{36}$", "id should be a UUID string")
        else:
            self.AssertRegEx(unit.id, "^[-0-9a-fA-F]{36}$", "id should be a UUID string")
        self.assertProperties(unit, RectangularRegionTests.expectedProperties)

    def test_constructor_kwargs(self):
        """Test the constructor when passed keyword arguments."""
        unit = RectangularRegion(x1=3, y1=4, x2=1, y2=2, id="myTestId")

        self.assertIsInstance(unit, RectangularRegion)
        self.assertEqual(unit.x1, 1, "x1 should be 1")
        self.assertEqual(unit.y1, 2, "y1 should be 2")
        self.assertEqual(unit.x2, 3, "x2 should be 3")
        self.assertEqual(unit.y2, 4, "y2 should be 2")
        self.assertEqual(unit.id, "myTestId", "id should be 'myTestId'")
        self.assertProperties(unit, RectangularRegionTests.expectedProperties)

    def test_copy_constructor(self):
        """Test the constructor when passed a RectangularRegion instance."""
        toCopy = RectangularRegion(x1=1, y1=2, x2=3, y2=4, id="myTestId")

        unit = RectangularRegion(toCopy)

        self.assertEqual(unit.x1, 1, "x1 should be 1")
        self.assertEqual(unit.y1, 2, "y1 should be 2")
        self.assertEqual(unit.x2, 3, "x2 should be 3")
        self.assertEqual(unit.y2, 4, "y2 should be 2")
        self.assertEqual(unit.id, "myTestId", "id should be 'myTestId'")
        self.assertProperties(unit, RectangularRegionTests.expectedProperties)

    def test_constructor_exception(self):
        """Test the constructor when passed a single non-RectangularRegion parameter."""
        with self.assertRaises(AssertionError):
            RectangularRegion("NotARectangularRegionInstance")

    def test_containsPoint(self):
        """Test the containsPoint method."""
        unit = RectangularRegion(x1=0, y1=0, x2=10, y2=10)

        self.assertTrue(unit.containsPoint(0, 0), "it should contain [0, 0]")
        self.assertTrue(unit.containsPoint(10, 10), "it should contain [10, 10]")
        self.assertTrue(unit.containsPoint(0, 10), "it should contain [0, 10]")
        self.assertTrue(unit.containsPoint(10, 0), "it should contain [10, 0]")

        self.assertTrue(unit.containsPoint(5, 5), "it should contain [5, 5]")

        self.assertFalse(unit.containsPoint(-1, 5), "it should not contain [-1, 5]")
        self.assertFalse(unit.containsPoint(5, -1), "it should not contain [5, -1]")
        self.assertFalse(unit.containsPoint(5, 11), "it should not contain [5, 11]")
        self.assertFalse(unit.containsPoint(11, 5), "it should not contain [11, 5]")

    def test_containsRegion_Rectangular(self):
        """Test the containsRegion method when passed a RectangularRegion."""
        unit = RectangularRegion(x1=0, y1=0, x2=10, y2=10)

        self.assertTrue(unit.containsRegion(unit), "it should contain itself")

        self.assertTrue(
            unit.containsRegion(RectangularRegion(x1=0, y1=0, x2=10, y2=10)),
            "it should contain a RectangularRegion representing the same geometric region"
        )
        self.assertTrue(
            unit.containsRegion(RectangularRegion(x1=2, y1=2, x2=8, y2=8)),
            "it should contain a RectangularRegion inside"
        )

        self.assertTrue(
            unit.containsRegion(RectangularRegion(x1=0, y1=4, x2=5, y2=6)),
            "it should contain a RectangularRegion inside, but tangent to the left edge"
        )
        self.assertTrue(
            unit.containsRegion(RectangularRegion(x1=5, y1=4, x2=10, y2=6)),
            "it should contain a RectangularRegion inside, but tangent to the right edge"
        )
        self.assertTrue(
            unit.containsRegion(RectangularRegion(x1=4, y1=0, x2=6, y2=5)),
            "it should contain a RectangularRegion inside, but tangent to the bottom edge"
        )
        self.assertTrue(
            unit.containsRegion(RectangularRegion(x1=4, y1=5, x2=6, y2=10)),
            "it should contain a RectangularRegion inside, but tangent to the top edge"
        )

        self.assertFalse(
            unit.containsRegion(RectangularRegion(x1=-1, y1=0, x2=5, y2=5)),
            "it should not contain a RectangularRegion that extends outside"
        )
        self.assertFalse(
            unit.containsRegion(RectangularRegion(x1=-1, y1=0, x2=5, y2=5)),
            "it should not contain a RectangularRegion that extends outside"
        )

    def test_containsRegion_Circular(self):
        """Test the containsRegion method when passed a CircularRegion."""
        unit = RectangularRegion(x1=0, y1=0, x2=10, y2=10)

        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=5, cy=5, r=1)),
            "it should contain a CircularRegion inside"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=1, cy=5, r=1)),
            "it should contain a CircularRegion inside, but tangent to the left edge"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=9, cy=5, r=1)),
            "it should contain a CircularRegion inside, but tangent to the right edge"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=5, cy=1, r=1)),
            "it should contain a CircularRegion inside, but tangent to the bottom edge"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=5, cy=9, r=1)),
            "it should contain a CircularRegion inside, but tangent to the top edge"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=5, cy=5, r=5)),
            "it should contain a CircularRegion inside, but tangent to all edges"
        )

        self.assertFalse(
            unit.containsRegion(CircularRegion(cx=5, cy=5, r=5.1)),
            "it should not contain a CircularRegion that extends outside"
        )
        self.assertFalse(
            unit.containsRegion(CircularRegion(cx=5, cy=5, r=10)),
            "it should not contain a CircularRegion containing this region"
        )
        self.assertFalse(
            unit.containsRegion(CircularRegion(cx=20, cy=20, r=1)),
            "it should not contain a CircularRegion completely outside"
        )

    def test_containsRegion_NotRegion(self):
        """Test the containsRegion method when passed an unsupported type."""
        unit = RectangularRegion(x1=0, y1=0, x2=10, y2=10)

        with self.assertRaises(ValueError):
            unit.containsRegion("NotARegionInstance")
