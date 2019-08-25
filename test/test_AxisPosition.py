# coding=utf-8
# pylint: disable=too-many-public-methods
"""Unit tests for the AxisPosition class."""

from __future__ import absolute_import

from octoprint_excluderegion.AxisPosition import AxisPosition
from .utils import TestCase


class AxisPositionTests(TestCase):
    """Unit tests for the AxisPosition class."""

    expectedProperties = ["current", "homeOffset", "offset", "absoluteMode", "unitMultiplier"]

    def test_default_constructor(self):
        """Test the constructor when passed no arguments."""
        unit = AxisPosition()

        self.assertIsInstance(unit, AxisPosition)
        self.assertEqual(unit.current, None, "current should be None")
        self.assertEqual(unit.homeOffset, 0, "homeOffset should be 0")
        self.assertEqual(unit.offset, 0, "offset should be 0")
        self.assertEqual(unit.absoluteMode, True, "absoluteMode should be True")
        self.assertEqual(unit.unitMultiplier, 1, "unitMultiplier should be 1")
        self.assertProperties(unit, AxisPositionTests.expectedProperties)

    def test_constructor_args(self):
        """Test the constructor when the first argument passed is not an AxisPosition."""
        unit = AxisPosition(1, 2, 3, False, 4)

        self.assertEqual(unit.current, 1, "current should be 1")
        self.assertEqual(unit.homeOffset, 2, "homeOffset should be 2")
        self.assertEqual(unit.offset, 3, "offset should be 3")
        self.assertEqual(unit.absoluteMode, False, "absoluteMode should be False")
        self.assertEqual(unit.unitMultiplier, 4, "unitMultiplier should be 4")
        self.assertProperties(unit, AxisPositionTests.expectedProperties)

    def test_copy_constructor(self):
        """Test the constructor when the first argument is an AxisPosition instance."""
        toCopy = AxisPosition(1, 2, 3, False, 4)
        unit = AxisPosition(toCopy)

        self.assertEqual(unit.current, 1, "current should be 1")
        self.assertEqual(unit.homeOffset, 2, "homeOffset should be 2")
        self.assertEqual(unit.offset, 3, "offset should be 3")
        self.assertEqual(unit.absoluteMode, False, "absoluteMode should be False")
        self.assertEqual(unit.unitMultiplier, 4, "unitMultiplier should be 4")
        self.assertProperties(unit, AxisPositionTests.expectedProperties)

    def test_setAbsoluteMode_True(self):
        """Test the setAbsoluteMode method when passed True."""
        unit = AxisPosition(1, 2, 3, False, 4)
        unit.setAbsoluteMode(True)
        self.assertTrue(unit.absoluteMode, "absoluteMode should be True")

    def test_setAbsoluteMode_False(self):
        """Test the setAbsoluteMode method when passed False."""
        unit = AxisPosition(1, 2, 3, True, 4)
        unit.setAbsoluteMode(False)
        self.assertFalse(unit.absoluteMode, "absoluteMode should be False")

    def test_setLogicalOffsetPosition_Absolute(self):
        """Test the setLogicalOffsetPosition method when in absolute mode."""
        unit = AxisPosition(100, 20, 50, True, 10)
        unit.setLogicalOffsetPosition(20)

        # 200 + 50 + 20 - 100 = 170, 50 + 170 = 220
        self.assertEqual(unit.offset, 220, "offset should be 220")
        self.assertEqual(unit.current, 100, "current should be 100")
        self.assertEqual(unit.homeOffset, 20, "homeOffset should be 20")

    def test_setLogicalOffsetPosition_Relative(self):
        """Test the setLogicalOffsetPosition method when in relative mode."""
        unit = AxisPosition(100, 20, 50, False, 10)
        unit.setLogicalOffsetPosition(20)

        # 200 + 100 - 100 = 200, 50 + 200 = 250
        self.assertEqual(unit.offset, 250, "offset should be 250")
        self.assertEqual(unit.current, 100, "current should be 100")
        self.assertEqual(unit.homeOffset, 20, "homeOffset should be 20")

    def test_setHomeOffset(self):
        """Test the setHomeOffset method."""
        unit = AxisPosition(0, 0, 0, True, 10)
        unit.setHomeOffset(20)

        self.assertEqual(unit.offset, 0, "offset should be 0")
        self.assertEqual(unit.current, -200, "current should be -200")
        self.assertEqual(unit.homeOffset, 200, "homeOffset should be 200")

    def test_setHome(self):
        """Test the setHome method."""
        unit = AxisPosition(1, 2, 3, False, 4)
        unit.setHome()

        self.assertEqual(unit.current, 0, "current should be 0")
        self.assertEqual(unit.offset, 0, "offset should be 0")
        self.assertEqual(unit.homeOffset, 2, "homeOffset should be 2")

    def test_setUnitMultiplier(self):
        """Test the setUnitMultiplier method."""
        unit = AxisPosition(1, 2, 3, False, 4)
        unit.setUnitMultiplier(20)
        self.assertEqual(unit.unitMultiplier, 20, "unitMultiplier should be 20")

    def test_setLogicalPosition_None(self):
        """Test the setLogicalPosition method when passed None."""
        unit = AxisPosition(1, 2, 3, False, 4)
        rval = unit.setLogicalPosition(None)

        self.assertEqual(rval, 1, "The result should be 1")
        self.assertEqual(unit.current, 1, "current should be 1")

    def test_setLogicalPosition_Absolute(self):
        """Test the setLogicalPosition method in absolute mode."""
        unit = AxisPosition(1, 2, 3, True, 4)
        unit.setLogicalPosition(20)
        self.assertEqual(unit.current, 85, "current should be 85")

    def test_setLogicalPosition_Relative(self):
        """Test the setLogicalPosition method in relative mode."""
        unit = AxisPosition(1, 2, 3, False, 4)
        unit.setLogicalPosition(20)
        self.assertEqual(unit.current, 81, "current should be 81")

    def test_logicalToNative_None_Absolute(self):
        """Test passing None to logicalToNative method in absolute mode."""
        unit = AxisPosition(1, 2, 3, True, 4)
        result = unit.logicalToNative(None)
        self.assertEqual(result, 1, "The result should be 1")

    def test_logicalToNative_None_Relative(self):
        """Test passing None to logicalToNative method in relative mode."""
        unit = AxisPosition(1, 2, 3, False, 4)
        result = unit.logicalToNative(None)
        self.assertEqual(result, 1, "The result should be 1")

    def test_logicalToNative_None_AbsoluteParam(self):
        """Test passing None to logicalToNative method and overriding relative mode."""
        unit = AxisPosition(1, 2, 3, False, 4)
        result = unit.logicalToNative(None, True)
        self.assertEqual(result, 1, "The result should be 1")

    def test_logicalToNative_None_RelativeParam(self):
        """Test passing None to logicalToNative method and overriding absolute mode."""
        unit = AxisPosition(1, 2, 3, True, 4)
        result = unit.logicalToNative(None, False)
        self.assertEqual(result, 1, "The result should be 1")

    def test_logicalToNative_AbsoluteParam(self):
        """Test the logicalToNative method overriding relative mode."""
        unit = AxisPosition(1, 2, 3, False, 4)
        result = unit.logicalToNative(10, True)
        self.assertEqual(result, 45, "The result should be 45")

    def test_logicalToNative_RelativeParam(self):
        """Test the logicalToNative method overriding absolute mode."""
        unit = AxisPosition(1, 2, 3, True, 4)
        result = unit.logicalToNative(10, False)
        self.assertEqual(result, 41, "The result should be 41")

    def test_logicalToNative_Absolute(self):
        """Test the logicalToNative method when in absolute mode."""
        unit = AxisPosition(1, 2, 3, True, 4)
        result = unit.logicalToNative(10)
        self.assertEqual(result, 45, "The result should be 45")

    def test_logicalToNative_Relative(self):
        """Test the logicalToNative method when in relative mode."""
        unit = AxisPosition(1, 2, 3, False, 4)
        result = unit.logicalToNative(10)
        self.assertEqual(result, 41, "The result should be 41")

    def test_nativeToLogical_None(self):
        """Test passing None to the nativeToLogical method."""
        unit = AxisPosition(1, 2, 3, True, 4)

        # 1 - (2 + 3) = -4 ; -4 / 4 = -1

        result = unit.nativeToLogical(None)
        self.assertEqual(result, -1, "The result should be -1")

        unit.setAbsoluteMode(False)
        result = unit.nativeToLogical(None)
        self.assertEqual(result, -1, "The result should be -1")

        result = unit.nativeToLogical(None, True)
        self.assertEqual(result, -1, "The result should be -1")

        result = unit.nativeToLogical(None, False)
        self.assertEqual(result, -1, "The result should be -1")

    def test_nativeToLogical_AbsoluteParam(self):
        """Test the nativeToLogical method overriding relative mode."""
        unit = AxisPosition(1, 2, 3, False, 4)
        result = unit.nativeToLogical(45, True)
        self.assertEqual(result, 10, "The result should be 10")

    def test_nativeToLogical_RelativeParam(self):
        """Test the nativeToLogical method overriding absolute mode."""
        unit = AxisPosition(1, 2, 3, True, 4)
        result = unit.nativeToLogical(41, False)
        self.assertEqual(result, 10, "The result should be 10")

    def test_nativeToLogical_Absolute(self):
        """Test the nativeToLogical method when in absolute mode."""
        unit = AxisPosition(1, 2, 3, True, 4)
        result = unit.nativeToLogical(45)
        self.assertEqual(result, 10, "The result should be 10")

    def test_nativeToLogical_Relative(self):
        """Test the nativeToLogical method when in relative mode."""
        unit = AxisPosition(1, 2, 3, False, 4)
        result = unit.nativeToLogical(41)
        self.assertEqual(result, 10, "The result should be 10")
