# coding=utf-8
"""Unit tests for the RectangularRegion class."""

from __future__ import absolute_import

from octoprint_excluderegion.CircularRegion import CircularRegion
from octoprint_excluderegion.RectangularRegion import RectangularRegion
from octoprint_excluderegion.Layer import Layer
from .utils import TestCase


class RectangularRegionTests(TestCase):
    """Unit tests for the RectangularRegion class."""

    expectedProperties = ["x1", "y1", "x2", "y2", "id", "minLayer", "maxLayer"]

    def test_default_constructor(self):
        """Test the constructor when passed no arguments."""
        unit = RectangularRegion()

        self.assertIsInstance(unit, RectangularRegion)
        self.assertEqual(unit.x1, 0, "x1 should be 0")
        self.assertEqual(unit.y1, 0, "y1 should be 0")
        self.assertEqual(unit.x2, 0, "x2 should be 0")
        self.assertEqual(unit.y2, 0, "y2 should be 0")
        self.assertRegex(unit.id, "^[-0-9a-fA-F]{36}$", "id should be a UUID string")
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

    def test_containsPoint3d(self):
        """Test the containsPoint3d method."""
        unit = RectangularRegion(x1=0, y1=0, x2=10, y2=10, maxLayer=Layer(height=1, number=2))

        self.assertTrue(unit.containsPoint3d(0, 0, 0), "it should contain [0, 0, 0]")
        self.assertTrue(unit.containsPoint3d(10, 10, 0), "it should contain [10, 10, 0]")
        self.assertTrue(unit.containsPoint3d(0, 10, 0), "it should contain [0, 10, 0]")
        self.assertTrue(unit.containsPoint3d(10, 0, 0), "it should contain [10, 0, 0]")

        self.assertTrue(unit.containsPoint3d(5, 5, 0), "it should contain [5, 5, 0]")

        self.assertFalse(unit.containsPoint3d(-1, 5, 0), "it should not contain [-1, 5, 0]")
        self.assertFalse(unit.containsPoint3d(5, -1, 0), "it should not contain [5, -1, 0]")
        self.assertFalse(unit.containsPoint3d(5, 11, 0), "it should not contain [5, 11, 0]")
        self.assertFalse(unit.containsPoint3d(11, 5, 0), "it should not contain [11, 5, 0]")

        self.assertFalse(unit.containsPoint3d(0, 0, 10), "it should not contain [0, 0, 10]")
        self.assertFalse(unit.containsPoint3d(10, 10, 10), "it should not contain [10, 10, 10]")
        self.assertFalse(unit.containsPoint3d(0, 10, 10), "it should not contain [0, 10, 10]")
        self.assertFalse(unit.containsPoint3d(10, 0, 10), "it should not contain [10, 0, 10]")

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
            unit.containsRegion(CircularRegion(cx=5, cy=5, radius=1)),
            "it should contain a CircularRegion inside"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=1, cy=5, radius=1)),
            "it should contain a CircularRegion inside, but tangent to the left edge"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=9, cy=5, radius=1)),
            "it should contain a CircularRegion inside, but tangent to the right edge"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=5, cy=1, radius=1)),
            "it should contain a CircularRegion inside, but tangent to the bottom edge"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=5, cy=9, radius=1)),
            "it should contain a CircularRegion inside, but tangent to the top edge"
        )
        self.assertTrue(
            unit.containsRegion(CircularRegion(cx=5, cy=5, radius=5)),
            "it should contain a CircularRegion inside, but tangent to all edges"
        )

        self.assertFalse(
            unit.containsRegion(CircularRegion(cx=5, cy=5, radius=5.1)),
            "it should not contain a CircularRegion that extends outside"
        )
        self.assertFalse(
            unit.containsRegion(CircularRegion(cx=5, cy=5, radius=10)),
            "it should not contain a CircularRegion containing this region"
        )
        self.assertFalse(
            unit.containsRegion(CircularRegion(cx=20, cy=20, radius=1)),
            "it should not contain a CircularRegion completely outside"
        )

    def test_containsRegion_NotRegion(self):
        """Test the containsRegion method when passed an unsupported type."""
        unit = RectangularRegion(x1=0, y1=0, x2=10, y2=10)

        with self.assertRaises(ValueError):
            unit.containsRegion("NotARegionInstance")
