# coding=utf-8
"""Unit tests for the Position class."""

from __future__ import absolute_import

from octoprint_excluderegion.Position import Position
from octoprint_excluderegion.AxisPosition import AxisPosition
from .utils import TestCase


class PositionTests(TestCase):
    """Unit tests for the Position class."""

    expectedProperties = ["X_AXIS", "Y_AXIS", "Z_AXIS", "E_AXIS"]

    def test_default_constructor(self):
        """Test the constructor when passed no arguments."""
        unit = Position()

        self.assertIsInstance(unit, Position)
        self.assertEqual(
            unit.X_AXIS, AxisPosition(), "X_AXIS should be a default AxisPosition instance"
        )
        self.assertEqual(
            unit.Y_AXIS, AxisPosition(), "Y_AXIS should be a default AxisPosition instance"
        )
        self.assertEqual(
            unit.Z_AXIS, AxisPosition(), "Z_AXIS should be a default AxisPosition instance"
        )
        self.assertEqual(
            unit.E_AXIS, AxisPosition(0),
            "E_AXIS should be a default AxisPosition instance with a known position of 0"
        )
        self.assertProperties(unit, PositionTests.expectedProperties)

    def test_copy_constructor(self):
        """Test the constructor when passed a Position instance."""
        toCopy = Position()
        toCopy.X_AXIS.current = 1
        toCopy.Y_AXIS.current = 2
        toCopy.Z_AXIS.current = 3
        toCopy.E_AXIS.current = 4

        unit = Position(toCopy)

        self.assertEqual(unit, toCopy, "The new instance should equal the original")
        self.assertIsNot(
            unit.X_AXIS, toCopy.X_AXIS, "The X_AXIS property should be a different instance"
        )
        self.assertIsNot(
            unit.Y_AXIS, toCopy.Y_AXIS, "The Y_AXIS property should be a different instance"
        )
        self.assertIsNot(
            unit.Z_AXIS, toCopy.Z_AXIS, "The Z_AXIS property should be a different instance"
        )
        self.assertIsNot(
            unit.E_AXIS, toCopy.E_AXIS, "The E_AXIS property should be a different instance"
        )
        self.assertProperties(unit, PositionTests.expectedProperties)

    def test_constructor_exception(self):
        """Test the constructor when passed a single non-Position parameter."""
        with self.assertRaises(AssertionError):
            Position("invalid")

    def test_setUnitMultiplier(self):
        """Test the setUnitMultiplier method."""
        unit = Position()

        unit.setUnitMultiplier(1234)

        self.assertEqual(
            unit.X_AXIS.unitMultiplier, 1234, "The X_AXIS unitMultiplier should be 1234"
        )
        self.assertEqual(
            unit.Y_AXIS.unitMultiplier, 1234, "The Y_AXIS unitMultiplier should be 1234"
        )
        self.assertEqual(
            unit.Z_AXIS.unitMultiplier, 1234, "The Z_AXIS unitMultiplier should be 1234"
        )
        self.assertEqual(
            unit.E_AXIS.unitMultiplier, 1234, "The E_AXIS unitMultiplier should be 1234"
        )

    def test_setPositionAbsoluteMode(self):
        """Test the setPositionAbsoluteMode method."""
        unit = Position()

        extruderAbsoluteMode = unit.E_AXIS.absoluteMode

        unit.setPositionAbsoluteMode(False)

        self.assertFalse(unit.X_AXIS.absoluteMode, "The X_AXIS absoluteMode should be False")
        self.assertFalse(unit.Y_AXIS.absoluteMode, "The Y_AXIS absoluteMode should be False")
        self.assertFalse(unit.Z_AXIS.absoluteMode, "The Z_AXIS absoluteMode should be False")
        self.assertEqual(
            unit.E_AXIS.absoluteMode, extruderAbsoluteMode,
            "The E_AXIS absoluteMode should be unchanged"
        )

        unit.setPositionAbsoluteMode(True)

        self.assertTrue(unit.X_AXIS.absoluteMode, "The X_AXIS absoluteMode should be True")
        self.assertTrue(unit.Y_AXIS.absoluteMode, "The Y_AXIS absoluteMode should be True")
        self.assertTrue(unit.Z_AXIS.absoluteMode, "The Z_AXIS absoluteMode should be True")
        self.assertEqual(
            unit.E_AXIS.absoluteMode, extruderAbsoluteMode,
            "The E_AXIS absoluteMode should be unchanged"
        )

    def test_setExtruderAbsoluteMode(self):
        """Test the setExtruderAbsoluteMode method."""
        unit = Position()

        unit.setExtruderAbsoluteMode(False)
        self.assertFalse(unit.E_AXIS.absoluteMode, "The E_AXIS absoluteMode should be False")

        unit.setExtruderAbsoluteMode(True)
        self.assertTrue(unit.E_AXIS.absoluteMode, "The E_AXIS absoluteMode should be True")
