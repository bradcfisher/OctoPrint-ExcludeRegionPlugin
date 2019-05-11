# coding=utf-8
"""Unit tests for the more advanced functionality of the ExcludeRegionState class."""

from __future__ import absolute_import

import mock

from octoprint_excluderegion.ExcludeRegionState import ExcludeRegionState

from .utils import TestCase


class ExcludeRegionStateTests(TestCase):
    """Unit tests for the more advanced functionality of the ExcludeRegionState class."""

    def test_recordRetraction_noLastRetraction_excluding(self):
        """Test recordRetraction when there is no lastRetraction and isExcluding is True."""
        expectedReturnCommands = ["initialCommand", "addedCommand"]

        mockRetractionState = mock.Mock()
        mockRetractionState.addRetractCommands.return_value = expectedReturnCommands

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = True

        returnCommands = unit.recordRetraction(mockRetractionState, ["initialCommand"])

        mockRetractionState.addRetractCommands.assert_called_with(unit.position, ["initialCommand"])
        self.assertEqual(
            returnCommands, expectedReturnCommands,
            "A list of two commands should be returned"
        )

    def test_recordRetraction_noLastRetraction_notExcluding_noReturnCommands(self):
        """Test recordRetraction with no lastRetraction, not excluding and returnCommands=None."""
        mockRetractionState = mock.Mock()
        mockRetractionState.originalCommand = "retractionCommand"

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False

        returnCommands = unit.recordRetraction(mockRetractionState, None)

        mockRetractionState.addRetractCommands.assert_not_called()
        self.assertEqual(
            returnCommands, ["retractionCommand"],
            "The original retraction command should be returned"
        )

    def test_recordRetraction_noLastRetraction_notExcluding_withReturnCommands(self):
        """Test recordRetraction with no lastRetraction, not excluding and returnCommands!=None."""
        mockRetractionState = mock.Mock()
        mockRetractionState.originalCommand = "retractionCommand"

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False

        returnCommands = unit.recordRetraction(mockRetractionState, ["initialCommand"])

        mockRetractionState.addRetractCommands.assert_not_called()
        self.assertEqual(
            returnCommands, ["initialCommand", "retractionCommand"],
            "The original retraction command should be appended to the command list passed in."
        )

    def test_recordRetraction_recoverExcluded_notFirmware(self):
        """Test recordRetraction with recoverExcluded=True and a non-firmware retract."""
        mockRetractionState = mock.Mock()
        mockRetractionState.originalCommand = "retractionCommand"

        mockLogger = mock.Mock()

        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction'):
            unit.feedRate = 20
            unit.lastRetraction.recoverExcluded = True
            unit.lastRetraction.firmwareRetract = False
            unit.lastRetraction.feedRate = None

            returnCommands = unit.recordRetraction(mockRetractionState, ["initialCommand"])

            self.assertFalse(
                unit.lastRetraction.recoverExcluded,
                "lastRetraction.recoverExcluded should be set to False"
            )

            self.assertEqual(
                unit.lastRetraction.feedRate, 20,
                "The retraction feedRate should be updated."
            )

            self.assertEqual(
                returnCommands, ["initialCommand"],
                "The command list passed in should be returned unmodified."
            )

    def test_recordRetraction_recoverExcluded_firmwareRetract(self):
        """Test recordRetraction with recoverExcluded=True and a firmware retract."""
        mockRetractionState = mock.Mock()
        mockRetractionState.originalCommand = "retractionCommand"

        mockLogger = mock.Mock()

        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction'):
            unit.feedRate = 20
            unit.lastRetraction.recoverExcluded = True
            unit.lastRetraction.firmwareRetract = True
            unit.lastRetraction.feedRate = None

            returnCommands = unit.recordRetraction(mockRetractionState, ["initialCommand"])

            self.assertFalse(
                unit.lastRetraction.recoverExcluded,
                "lastRetraction.recoverExcluded should be set to False"
            )

            self.assertIsNone(
                unit.lastRetraction.feedRate,
                "The retraction feedRate should not be modified."
            )

            self.assertEqual(
                returnCommands, ["initialCommand"],
                "The command list passed in should be returned unmodified."
            )

    def test_recordRetraction_noRecoverExcluded_excluding(self):
        """Test recordRetraction with recoverExcluded=False and excluding."""
        expectedReturnCommands = ["initialCommand", "addedCommand"]

        mockRetractionState = mock.Mock()
        mockRetractionState.addRetractCommands.return_value = expectedReturnCommands

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction'):
            unit.lastRetraction.recoverExcluded = False
            unit.excluding = True

            returnCommands = unit.recordRetraction(mockRetractionState, ["initialCommand"])

            mockRetractionState.addRetractCommands.assert_called_with(
                unit.position,
                ["initialCommand"]
            )
            self.assertEqual(
                returnCommands, expectedReturnCommands,
                "A list of two commands should be returned"
            )

    def test_recordRetraction_noRecoverExcluded_notExcluding_noReturnCommands(self):
        """Test recordRetraction with recoverExcluded=False, not excluding and no returnCommands."""
        mockRetractionState = mock.Mock()
        mockRetractionState.originalCommand = "retractionCommand"

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction'):
            unit.lastRetraction.recoverExcluded = False
            unit.excluding = False

            returnCommands = unit.recordRetraction(mockRetractionState, None)

            mockRetractionState.addRetractCommands.assert_not_called()
            self.assertEqual(
                returnCommands, ["retractionCommand"],
                "The original retraction command should be appended to the command list passed in."
            )

    def test_recordRetraction_noRecoverExcluded_notExcluding_withReturnCommands(self):
        """Test recordRetraction with recoverExcluded=False, not excluding and returnCommands."""
        mockRetractionState = mock.Mock()
        mockRetractionState.originalCommand = "retractionCommand"

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction'):
            unit.lastRetraction.recoverExcluded = False
            unit.excluding = False

            returnCommands = unit.recordRetraction(mockRetractionState, ["initialCommand"])

            mockRetractionState.addRetractCommands.assert_not_called()
            self.assertEqual(
                returnCommands, ["initialCommand", "retractionCommand"],
                "The original retraction command should be returned"
            )

    def test_recoverRetraction_recoverExcluded(self):
        """Test _recoverRetraction with recoverExcluded=True."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction') as lastRetractionMock:
            unit.lastRetraction.recoverExcluded = True
            unit.lastRetraction.addRecoverCommands.return_value = ["recoverCommand"]

            result = unit._recoverRetraction("G11", True, None)  # pylint: disable=protected-access

            # The test against this mock covers both cases where returnCommands None and when it is
            # a list of commands since the final result is built from the addRecoverCommands result
            # which is mocked anyway
            lastRetractionMock.addRecoverCommands.assert_called_with(unit.position, None)
            self.assertIsNone(unit.lastRetraction, "The lastRetraction should be set to None")
            self.assertEqual(
                result, ["recoverCommand", "G11"],
                "The result should contain two items"
            )

    def test_recoverRetraction_noRecoverExcluded_noReturnCommands(self):
        """Test _recoverRetraction with recoverExcluded=False and no returnCommands provided."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction') as lastRetractionMock:
            unit.lastRetraction.recoverExcluded = False

            result = unit._recoverRetraction("G11", True, None)  # pylint: disable=protected-access

            lastRetractionMock.addRecoverCommands.assert_not_called()
            self.assertIsNone(unit.lastRetraction, "The lastRetraction should be set to None")
            self.assertEqual(result, ["G11"], "The result should contain one item")

    def test_recoverRetraction_noRecoverExcluded_withReturnCommands(self):
        """Test _recoverRetraction with recoverExcluded=False and returnCommands provided."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction') as lastRetractionMock:
            unit.lastRetraction.recoverExcluded = False

            result = unit._recoverRetraction(  # pylint: disable=protected-access
                "G11",
                True,
                ["initialCommand"]
            )

            lastRetractionMock.addRecoverCommands.assert_not_called()
            self.assertIsNone(unit.lastRetraction, "The lastRetraction should be set to None")
            self.assertEqual(
                result, ["initialCommand", "G11"],
                "The result should contain two items"
            )

# TODO: Test recoverRetractionIfNeeded

# TODO: Test processLinearMoves

# TODO: Test enterExcludedRegion

# TODO: Test exitExcludedRegion

# TODO: Test _processExtendedGcodeEntry

# TODO: Test processExtendedGcode
