# coding=utf-8
"""Unit tests for the processLinearMoves method of the ExcludeRegionState class."""

from __future__ import absolute_import

import mock

from octoprint_excluderegion.ExcludeRegionState import ExcludeRegionState
from octoprint_excluderegion.GcodeHandlers import INCH_TO_MM_FACTOR

from .utils import TestCase, create_position


class ExcludeRegionStateProcessLinearMovesTests(
        TestCase
):  # pylint: disable=too-many-public-methods
    """Unit tests for the processLinearMoves method of the ExcludeRegionState class."""

    def test_processLinearMoves_unitMultiplier(self):
        """Test processLinearMoves when a non-native unit multiplier is in effect."""
        mockLogger = mock.Mock()
        mockLogger.isEnabledFor.return_value = False  # For coverage

        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(
            x=1, y=2, z=3, extruderPosition=4,
            unitMultiplier=INCH_TO_MM_FACTOR
        )
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = INCH_TO_MM_FACTOR

        originalIsAnyPointExcluded = unit.isAnyPointExcluded

        def is_any_point_excluded_side_effect(self, *args):
            originalIsAnyPointExcluded(self, *args)
            return True

        with mock.patch.multiple(
            unit,
            _processExcludedMove=mock.DEFAULT,
            isAnyPointExcluded=mock.DEFAULT,
            recoverRetractionIfNeeded=mock.DEFAULT
        ) as mocks:
            mocks["isAnyPointExcluded"].side_effect = is_any_point_excluded_side_effect
            mocks["_processExcludedMove"].return_value = ["processExcludedMove"]

            result = unit.processLinearMoves("G1 X1 Y2 Z3 E-1 F100", -1, 100, 3, 1, 2)

            mocks["isAnyPointExcluded"].assert_called_with(1, 2)
            mocks["recoverRetractionIfNeeded"].assert_not_called()
            mocks["_processExcludedMove"].assert_called_with(
                "G1 X1 Y2 Z3 E-1 F100",
                -4 - 1 * INCH_TO_MM_FACTOR
            )
            self.assertEqual(
                unit.feedRate, 100 * INCH_TO_MM_FACTOR,
                "The feedRate should be updated to the expected value."
            )
            self.assertEqual(
                result, ["processExcludedMove"],
                "The expected result should be returned."
            )
            self.assertEqual(
                unit.position.X_AXIS.current, 1 * INCH_TO_MM_FACTOR,
                "The X axis position should be updated from 1 mm to 1 in."
            )
            self.assertEqual(
                unit.position.Y_AXIS.current, 2 * INCH_TO_MM_FACTOR,
                "The Y axis position should be updated from 2 mm to 2 in."
            )
            self.assertEqual(
                unit.position.Z_AXIS.current, 3 * INCH_TO_MM_FACTOR,
                "The Z axis position should be updated from 3 mm to 3 in."
            )
            self.assertEqual(
                unit.position.E_AXIS.current, -1 * INCH_TO_MM_FACTOR,
                "The Z axis position should be updated from 4 mm to -1 in."
            )

    def test_processLinearMoves_extruderPosition_None_nonMove(self):
        """Test processLinearMoves for a non-Move and extruderPosition value of None."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.object(unit, '_processNonMove') as mockProcessNonMove:
            mockProcessNonMove.return_value = []  # Should drop command

            result = unit.processLinearMoves("G1 F1000", None, 1000, None)

            mockProcessNonMove.assert_called_with("G1 F1000", 0)

            self.assertEqual(
                unit.position.E_AXIS.current, 4,
                "The extruder position should be the expected value"
            )
            self.assertEqual(
                result, (None,),
                "The result should indicate to drop/ignore the command"
            )

    def test_processLinearMoves_extruderPosition_None_move(self):
        """Test processLinearMoves for a move and extruderPosition value of None."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        result = unit.processLinearMoves("G1 X2 Y3 F1000", None, 1000, None, 2, 3)

        self.assertEqual(
            unit.position.E_AXIS.current, 4,
            "The extruder position should be the expected value"
        )
        self.assertEqual(
            result, ["G1 X2 Y3 F1000"],
            "It should return a list containing the provided command"
        )

    def test_processLinearMoves_extruderPositionSame_nonMove(self):
        """Test processLinearMoves for non-move and extruderPosition matching the current value."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.object(unit, '_processNonMove') as mockProcessNonMove:
            mockProcessNonMove.return_value = ["expectedResult"]

            result = unit.processLinearMoves("G1 E4", 4, None, None)

            mockProcessNonMove.assert_called_with("G1 E4", 0)

            self.assertEqual(
                unit.position.E_AXIS.current, 4,
                "The extruder position should be the expected value"
            )
            self.assertEqual(
                result, ["expectedResult"],
                "It should return a list containing the expected command(s)"
            )

    def test_processLinearMoves_extruderPositionSame_move(self):
        """Test processLinearMoves for move and extruderPosition matching the current value."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        result = unit.processLinearMoves("G1 X2 Y3 E4", 4, None, None, 2, 3)

        self.assertEqual(
            unit.position.E_AXIS.current, 4,
            "The extruder position should be the expected value"
        )
        self.assertEqual(
            result, ["G1 X2 Y3 E4"],
            "It should return a list containing the provided command"
        )

    def test_processLinearMoves_extruderPositionIncreased_nonMove(self):
        """Test processLinearMoves for non-move and a larger extruderPosition."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.object(unit, '_processNonMove') as mockProcessNonMove:
            mockProcessNonMove.return_value = ["expectedResult"]

            result = unit.processLinearMoves("G1 E40", 40, None, None)

            mockProcessNonMove.assert_called_with("G1 E40", 36)

            self.assertEqual(
                unit.position.E_AXIS.current, 40,
                "The extruder position should be updated to the new value"
            )
            self.assertEqual(
                result, ["expectedResult"],
                "It should return a list containing the expected command(s)"
            )

    def test_processLinearMoves_extruderPositionIncreased_move(self):
        """Test processLinearMoves for move and a larger extruderPosition."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.object(unit, 'recoverRetractionIfNeeded') as mockRecoverRetractionIfNeeded:
            mockRecoverRetractionIfNeeded.return_value = ["expectedResult"]

            result = unit.processLinearMoves("G1 X2 Y3 E40", 40, None, None, 2, 3)

            mockRecoverRetractionIfNeeded.assert_called_with("G1 X2 Y3 E40", False)

            self.assertEqual(
                unit.position.E_AXIS.current, 40,
                "The extruder position should be updated to the new value"
            )
            self.assertEqual(
                result, ["expectedResult"],
                "It should return the result of recoverRetractionIfNeeded"
            )

    def test_processLinearMoves_extruderPositionDecreased_nonMove(self):
        """Test processLinearMoves for non-move and a smaller extruderPosition."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.object(unit, '_processNonMove') as mockProcessNonMove:
            mockProcessNonMove.return_value = ["expectedResult"]

            result = unit.processLinearMoves("G1 E0", 0, None, None)

            mockProcessNonMove.assert_called_with("G1 E0", -4)

            self.assertEqual(
                unit.position.E_AXIS.current, 0,
                "The extruder position should be updated to the new value"
            )
            self.assertEqual(
                result, ["expectedResult"],
                "It should return a list containing the expected command(s)"
            )

    def test_processLinearMoves_extruderPositionDecreased_move(self):
        """Test processLinearMoves for move and a smaller extruderPosition."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.object(unit, 'recoverRetractionIfNeeded') as mockRecoverRetractionIfNeeded:
            mockRecoverRetractionIfNeeded.return_value = ["expectedResult"]

            result = unit.processLinearMoves("G1 X2 Y3 E0", 0, None, None, 2, 3)

            mockRecoverRetractionIfNeeded.assert_called_with("G1 X2 Y3 E0", False)

            self.assertEqual(
                unit.position.E_AXIS.current, 0,
                "The extruder position should be updated to the new value"
            )
            self.assertEqual(
                result, ["expectedResult"],
                "It should return the result of recoverRetractionIfNeeded"
            )

    def test_processLinearMoves_feedRate_None(self):
        """Test processLinearMoves when None is passed for a feedRate value."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        unit.processLinearMoves("G1 Z1", None, None, 1)

        self.assertEqual(
            unit.feedRate, 4000,
            "The feedRate should not be modified"
        )

    def test_processLinearMoves_feedRate_Same(self):
        """Test processLinearMoves when the feedRate parameter value matches the current value."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        unit.processLinearMoves("G1 Z1", None, 4000, 1)

        self.assertEqual(
            unit.feedRate, 4000,
            "The feedRate should be the expected value"
        )

    def test_processLinearMoves_feedRate_Different(self):
        """Test processLinearMoves when the feedRate parameter doesn't match the current value."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        unit.processLinearMoves("G1 Z1", None, 1000, 1)

        self.assertEqual(
            unit.feedRate, 1000,
            "The feedRate should be updated to the new value"
        )

    def test_processLinearMoves_finalZ_None(self):
        """Test processLinearMoves when the finalZ is None."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.object(unit, '_processNonMove') as mockProcessNonMove:
            mockProcessNonMove.return_value = ["expectedResult"]

            result = unit.processLinearMoves("G1 F10", None, 10, None)

            mockProcessNonMove.assert_called_with("G1 F10", 0)

            self.assertEqual(
                unit.position.Z_AXIS.current, 3,
                "The Z axis position should not be updated"
            )
            self.assertEqual(
                result, ["expectedResult"],
                "The result of _processNonMove should be returned."
            )

    def test_processLinearMoves_finalZ_Same(self):
        """Test processLinearMoves when the finalZ is the same as the current Z axis position."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        result = unit.processLinearMoves("G1 Z3", None, None, 3)

        self.assertEqual(
            unit.position.Z_AXIS.current, 3,
            "The Z axis position should be the expected value."
        )
        self.assertEqual(
            result, ["G1 Z3"],
            "A list containing the provided command should be returned."
        )

    def test_processLinearMoves_finalZ_Increased(self):
        """Test processLinearMoves when the finalZ is more than the current Z axis position."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        result = unit.processLinearMoves("G1 Z30", None, None, 30)

        self.assertEqual(
            unit.position.Z_AXIS.current, 30,
            "The Z axis position should be the expected value."
        )
        self.assertEqual(
            result, ["G1 Z30"],
            "A list containing the provided command should be returned."
        )

    def test_processLinearMoves_finalZ_Decreased(self):
        """Test processLinearMoves when the finalZ is less than the current Z axis position."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        result = unit.processLinearMoves("G1 Z0", None, None, 0)

        self.assertEqual(
            unit.position.Z_AXIS.current, 0,
            "The Z axis position should be the expected value."
        )
        self.assertEqual(
            result, ["G1 Z0"],
            "A list containing the provided command should be returned."
        )

    def test_processLinearMoves_pointInExcludedRegion(self):
        """Test processLinearMoves with a point in excluded region."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = True
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.multiple(
            unit,
            isAnyPointExcluded=mock.DEFAULT,
            _processExcludedMove=mock.DEFAULT
        ) as mocks:
            mocks["isAnyPointExcluded"].return_value = True
            mocks["_processExcludedMove"].return_value = ["processExcludedMove"]

            result = unit.processLinearMoves("G1 X10 Y20", 3, None, None, 10, 20)

            mocks["isAnyPointExcluded"].assert_called_with(10, 20)
            mocks["_processExcludedMove"].assert_called_with("G1 X10 Y20", -1)
            self.assertEqual(
                result, ["processExcludedMove"],
                "The result should be the commands returned by _processExcludedMove"
            )

    def test_processLinearMoves_excluding_noPointInExcludedRegion(self):
        """Test processLinearMoves when points not in an excluded region and currently excluding."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = True
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.multiple(
            unit,
            isAnyPointExcluded=mock.DEFAULT,
            exitExcludedRegion=mock.DEFAULT,
            _processNonMove=mock.DEFAULT
        ) as mocks:
            mocks["isAnyPointExcluded"].return_value = False
            mocks["exitExcludedRegion"].return_value = ["expectedResult"]

            result = unit.processLinearMoves("G1 X10 Y20", None, None, None, 10, 20)

            mocks["isAnyPointExcluded"].assert_called_with(10, 20)
            mocks["exitExcludedRegion"].assert_called_with("G1 X10 Y20")
            mocks["_processNonMove"].assert_not_called()
            self.assertEqual(
                result, ["expectedResult"],
                "The result of exitExcludedRegion should be returned."
            )

    def test_processLinearMoves_notExcluding_noPointInExcludedRegion(self):
        """Test processLinearMoves with point not in an excluded region and excluding=False."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.object(unit, 'isAnyPointExcluded') as mockIsAnyPointExcluded:
            mockIsAnyPointExcluded.return_value = False

            result = unit.processLinearMoves("G1 X10 Y20", None, None, None, 10, 20)

            mockIsAnyPointExcluded.assert_called_with(10, 20)
            self.assertEqual(
                result, ["G1 X10 Y20"],
                "A list containing the provided command should be returned."
            )

    def test_processLinearMoves_xyListNones_noMove(self):
        """Test processLinearMoves when None values are used in the x,y pairs for a non-move."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.object(unit, '_processNonMove') as mockProcessNonMove:
            mockProcessNonMove.return_value = ["expectedResult"]

            result = unit.processLinearMoves("G0 E4", 4, None, None, None, None)

            mockProcessNonMove.assert_called_with("G0 E4", 0)
            self.assertEqual(
                unit.position.X_AXIS.current, 1,
                "The X axis position should be unchanged."
            )
            self.assertEqual(
                unit.position.Y_AXIS.current, 2,
                "The Y axis position should be unchanged."
            )
            self.assertEqual(
                result, ["expectedResult"],
                "The result of _processNonMove should be returned."
            )

    def test_processLinearMoves_xyListNones_move(self):
        """Test processLinearMoves when None values are used in the x,y pairs for a move."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.position = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.feedRate = 4000
        unit.feedRateUnitMultiplier = 1

        with mock.patch.object(unit, 'isAnyPointExcluded') as mockIsAnyPointExcluded:
            mockIsAnyPointExcluded.return_value = False

            result = unit.processLinearMoves("G0 Z10", None, None, 10, None, None)

            mockIsAnyPointExcluded.assert_called_with(None, None)
            self.assertEqual(
                unit.position.X_AXIS.current, 1,
                "The X axis position should be unchanged."
            )
            self.assertEqual(
                unit.position.Y_AXIS.current, 2,
                "The Y axis position should be unchanged."
            )
            self.assertEqual(
                result, ["G0 Z10"],
                "A list containing the provided command should be returned."
            )
