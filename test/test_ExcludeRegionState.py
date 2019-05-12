# coding=utf-8
"""Unit tests for the more advanced functionality of the ExcludeRegionState class."""

from __future__ import absolute_import

import mock

from octoprint_excluderegion.ExcludeRegionState import ExcludeRegionState
from octoprint_excluderegion.ExcludedGcode \
    import EXCLUDE_ALL, EXCLUDE_EXCEPT_FIRST, EXCLUDE_EXCEPT_LAST, EXCLUDE_MERGE

from .utils import TestCase


class ExcludeRegionStateTests(TestCase):  # pylint: disable=too-many-public-methods
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

    def test_recoverRetractionIfNeeded_lastRetraction_excluding_isRecoverCommand(self):
        """Test recoverRetractionIfNeeded with a lastRetraction, recoverCommand and excluding."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.multiple(
            unit,
            _recoverRetraction=mock.DEFAULT,
            lastRetraction=mock.DEFAULT
        ) as mocks:
            unit.excluding = True
            unit.lastRetraction.recoverExcluded = False

            result = unit.recoverRetractionIfNeeded("G11", True, ["initialCommand"])

            # The test against this mock covers both cases where returnCommands None and when it is
            # a list of commands since the final result is built from the _recoverRetraction result
            # which is mocked anyway
            mocks["_recoverRetraction"].assert_not_called()
            self.assertEqual(
                unit.lastRetraction, mocks["lastRetraction"],
                "The lastRetraction should not be updated"
            )
            self.assertTrue(
                unit.lastRetraction.recoverExcluded,
                "recoverExcluded should be set to True"
            )
            self.assertEqual(
                result, ["initialCommand"],
                "The result should match the list of commands provided"
            )

    def test_recoverRetractionIfNeeded_lastRetraction_excluding_notRecoverCommand(self):
        """Test recoverRetractionIfNeeded with lastRetraction, excluding and NO recoverCommand."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.multiple(
            unit,
            _recoverRetraction=mock.DEFAULT,
            lastRetraction=mock.DEFAULT
        ) as mocks:
            unit.excluding = True
            unit.lastRetraction.recoverExcluded = False

            result = unit.recoverRetractionIfNeeded("G1 X1 Y2 E3", False, ["initialCommand"])

            # The test against this mock covers both cases where returnCommands None and when it is
            # a list of commands since the final result is built from the _recoverRetraction result
            # which is mocked anyway
            mocks["_recoverRetraction"].assert_not_called()
            self.assertEqual(
                unit.lastRetraction, mocks["lastRetraction"],
                "The lastRetraction should not be updated"
            )
            self.assertFalse(
                unit.lastRetraction.recoverExcluded,
                "recoverExcluded should not be updated"
            )
            self.assertEqual(
                result, ["initialCommand"],
                "The result should match the list of commands provided"
            )

    def test_recoverRetractionIfNeeded_lastRetraction_notExcluding(self):
        """Test recoverRetractionIfNeeded with a lastRetraction and NOT excluding."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.multiple(
            unit,
            _recoverRetraction=mock.DEFAULT,
            lastRetraction=mock.DEFAULT
        ) as mocks:
            unit.excluding = False
            unit.lastRetraction.recoverExcluded = False
            mocks["_recoverRetraction"].return_value = ["expectedCommand"]

            result = unit.recoverRetractionIfNeeded("G11", True, ["initialCommand"])

            mocks["_recoverRetraction"].assert_called_with("G11", True, ["initialCommand"])
            self.assertEqual(
                unit.lastRetraction, mocks["lastRetraction"],
                "The lastRetraction should not be updated"
            )
            self.assertFalse(
                unit.lastRetraction.recoverExcluded,
                "recoverExcluded should not be updated"
            )
            self.assertEqual(
                result, ["expectedCommand"],
                "The result should match the list of commands returned by _recoverRetraction"
            )

    def test_recoverRetractionIfNeeded_noLastRetraction_excluding(self):
        """Test recoverRetractionIfNeeded with NO lastRetraction and excluding (do nothing)."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, '_recoverRetraction') as recoverRetractionMock:
            unit.lastRetraction = None
            unit.excluding = True

            result = unit.recoverRetractionIfNeeded("G11", True, ["initialCommand"])

            recoverRetractionMock.assert_not_called()
            self.assertIsNone(unit.lastRetraction, "The lastRetraction should not be updated")
            self.assertEqual(
                result, ["initialCommand"],
                "The result should match the list of commands provided"
            )

    def test_recoverRetractionIfNeeded_noLastRetraction_notExcluding_noReturnCommands(self):
        """Test recoverRetractionIfNeeded with NO lastRetraction and NO returnCommands."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, '_recoverRetraction') as recoverRetractionMock:
            unit.lastRetraction = None
            unit.excluding = False

            result = unit.recoverRetractionIfNeeded("G1 X1 Y1", False, None)

            recoverRetractionMock.assert_not_called()
            self.assertIsNone(unit.lastRetraction, "The lastRetraction should not be updated")
            self.assertEqual(
                result, ["G1 X1 Y1"],
                "The result should contain only the provided command"
            )

    def test_recoverRetractionIfNeeded_noLastRetraction_notExcluding_withReturnCommands(self):
        """Test recoverRetractionIfNeeded with NO lastRetraction and returnCommands."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, '_recoverRetraction') as recoverRetractionMock:
            unit.lastRetraction = None
            unit.excluding = False

            result = unit.recoverRetractionIfNeeded("G11", True, ["initialCommand"])

            recoverRetractionMock.assert_not_called()
            self.assertIsNone(unit.lastRetraction, "The lastRetraction should not be updated")
            self.assertEqual(
                result, ["initialCommand", "G11"],
                "The result should contain two items"
            )

# TODO: Test _processNonMove

# TODO: Test processLinearMoves
# - Test it properly handles non-native units

    def test_enterExcludedRegion_exclusionDisabled(self):
        """Test enterExcludedRegion when exclusion is disabled should raise an AssertionError."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.disableExclusion("Disable for test")

        with self.assertRaises(AssertionError):
            unit.enterExcludedRegion("G1 X1 Y2", None)

    def _test_enterExcludedRegion_common(self, enteringExcludedRegionGcode, returnCommands):
        """Test common functionality of enterExcludedRegion when exclusion is enabled."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.excluding = False
        unit.excludeStartTime = "oldStartTime"
        unit.numExcludedCommands = 42
        unit.numCommands = 84
        unit.lastPosition = "oldPosition"

        unit.enteringExcludedRegionGcode = enteringExcludedRegionGcode

        result = unit.enterExcludedRegion("G1 X1 Y2", returnCommands)

        self.assertTrue(unit.excluding, "The excluding flag should be True")
        self.assertNotEqual(
            unit.excludeStartTime, "oldStartTime",
            "The excludeStartTime should be updated"
        )
        self.assertEqual(
            unit.numExcludedCommands, 0,
            "The numExcludedCommands should be reset to 0"
        )
        self.assertEqual(unit.numCommands, 0, "The numCommands should be reset to 0")
        self.assertNotEqual(unit.lastPosition, "oldPosition", "The position should be updated")

        return result

    def test_enterExcludedRegion_noEnteringExcludeRegionGcode_noReturnCommands(self):
        """Test enterExcludedRegion with no enter region script and no returnCommands."""
        result = self._test_enterExcludedRegion_common(None, None)
        self.assertIsNone(result, "The result should be None")

    def test_enterExcludedRegion_noEnteringExcludeRegionGcode_withReturnCommands(self):
        """Test enterExcludedRegion with no enter region script and returnCommands are provided."""
        result = self._test_enterExcludedRegion_common(None, ["someCommand"])
        self.assertEqual(
            result, ["someCommand"],
            "The result should match the provided returnCommands list"
        )

    def test_enterExcludedRegion_withEnteringExcludeRegionGcode_noReturnCommands(self):
        """Test enterExcludedRegion with an enter region script and no returnCommands."""
        result = self._test_enterExcludedRegion_common(["scriptCommand"], None)
        self.assertEqual(
            result, ["scriptCommand"],
            "The result should match the enteringExcludeRegionGcode"
        )

    def test_enterExcludedRegion_withEnteringExcludeRegionGcode_withReturnCommands(self):
        """Test enterExcludedRegion with an enter region script and returnCommands are provided."""
        result = self._test_enterExcludedRegion_common(["scriptCommand"], ["someCommand"])
        self.assertEqual(
            result, ["someCommand", "scriptCommand"],
            "The result should be the returnCommands plus the enteringExcludeRegionGcode"
        )

# TODO: Test _appendPendingCommands

# TODO: Test exitExcludedRegion

    def test_processExtendedGcodeEntry_EXCLUDE_ALL(self):
        """Test processExtendedGcodeEntry when the mode is EXCLUDE_ALL."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = {}

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_ALL,
            "G1 X1 Y2", "G1"
        )

        self.assertEqual(unit.pendingCommands, {}, "pendingCommands should not be updated.")
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_MERGE_noPendingArgs_noCmdArgs(self):
        """Test processExtendedGcodeEntry / EXCLUDE_MERGE if no pending args and no command args."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = {}

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_MERGE,
            "G1", "G1"
        )

        self.assertEqual(
            unit.pendingCommands, {"G1": {}},
            "pendingCommands should be updated."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_MERGE_noPendingArgs_cmdHasArgs(self):
        """Test processExtendedGcodeEntry / EXCLUDE_MERGE if no pending args, and cmd with args."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = {}

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_MERGE,
            "G1 X1 Y2", "G1"
        )

        self.assertEqual(
            unit.pendingCommands, {"G1": {"X": "1", "Y": "2"}},
            "pendingCommands should be updated with the command arguments."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_MERGE_hasPendingArgs_noCmdArgs(self):
        """Test processExtendedGcodeEntry / EXCLUDE_MERGE if pending args and no command args."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = {"G1": {"X": "10"}}

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_MERGE,
            "G1", "G1"
        )

        self.assertEqual(
            unit.pendingCommands, {"G1": {"X": "10"}},
            "pendingCommands should be updated with new argument values."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_MERGE_hasPendingArgs_cmdHasArgs(self):
        """Test processExtendedGcodeEntry / EXCLUDE_MERGE if pending args and command with args."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = {"G1": {"X": "10", "Z": "20"}}

        # Use upper and lower case args to test case-sensitivity
        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_MERGE,
            "G1 x1 Y2", "G1"
        )

        self.assertEqual(
            unit.pendingCommands, {"G1": {"X": "1", "Y": "2", "Z": "20"}},
            "pendingCommands should be updated with new argument values."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_EXCEPT_FIRST_noYetSeen(self):
        """Test processExtendedGcodeEntry / EXCLUDE_EXCEPT_FIRST for a Gcode not yet seen."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = {}

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_EXCEPT_FIRST,
            "G1 X1 Y2", "G1"
        )

        self.assertEqual(
            unit.pendingCommands, {"G1": "G1 X1 Y2"},
            "pendingCommands should be updated with new command string."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_EXCEPT_FIRST_alreadySeen(self):
        """Test processExtendedGcodeEntry / EXCLUDE_EXCEPT_FIRST for a Gcode already seen."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = {"G1": "G1 E3 Z4"}

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_EXCEPT_FIRST,
            "G1 X1 Y2", "G1"
        )

        self.assertEqual(
            unit.pendingCommands, {"G1": "G1 E3 Z4"},
            "pendingCommands should not be updated."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_EXCEPT_LAST_notYetSeen(self):
        """Test processExtendedGcodeEntry / EXCLUDE_EXCEPT_LAST for a Gcode not yet seen."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = {}

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_EXCEPT_LAST,
            "G1 X1 Y2", "G1"
        )

        self.assertEqual(
            unit.pendingCommands, {"G1": "G1 X1 Y2"},
            "pendingCommands should be updated with new command string."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_EXCEPT_LAST_alreadySeen(self):
        """Test processExtendedGcodeEntry / EXCLUDE_EXCEPT_LAST for a Gcode already seen."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = {"G1": "G1 E3 Z4"}

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_EXCEPT_LAST,
            "G1 X1 Y2", "G1"
        )

        self.assertEqual(
            unit.pendingCommands, {"G1": "G1 X1 Y2"},
            "pendingCommands should be updated with new command string."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcode_noGcode_excluding(self):
        """Test processExtendedGcode when excluding and no gcode provided."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.object(unit, 'extendedExcludeGcodes') as mockExtendedExcludeGcodes:
            unit.excluding = True

            result = unit.processExtendedGcode("someCommand", None, None)

            mockExtendedExcludeGcodes.get.assert_not_called()
            self.assertIsNone(result, "The return value should be None")

    def test_processExtendedGcode_noGcode_notExcluding(self):
        """Test processExtendedGcode when not excluding and no gcode provided."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.object(unit, 'extendedExcludeGcodes') as mockExtendedExcludeGcodes:
            unit.excluding = False

            result = unit.processExtendedGcode("someCommand", None, None)

            mockExtendedExcludeGcodes.get.assert_not_called()
            self.assertIsNone(result, "The return value should be None")

    def test_processExtendedGcode_excluding_noMatch(self):
        """Test processExtendedGcode when excluding and no entry matches."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.multiple(
            unit,
            extendedExcludeGcodes=mock.DEFAULT,
            _processExtendedGcodeEntry=mock.DEFAULT
        ) as mocks:
            unit.excluding = True
            mocks["extendedExcludeGcodes"].get.return_value = None

            result = unit.processExtendedGcode("G1 X1 Y2", "G1", None)

            mocks["extendedExcludeGcodes"].get.assert_called_with("G1")
            mocks["_processExtendedGcodeEntry"].assert_not_called()
            self.assertIsNone(result, "The return value should be None")

    def test_processExtendedGcode_excluding_matchExists(self):
        """Test processExtendedGcode when excluding and a matching entry exists."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.multiple(
            unit,
            extendedExcludeGcodes=mock.DEFAULT,
            _processExtendedGcodeEntry=mock.DEFAULT
        ) as mocks:
            unit.excluding = True
            mockEntry = mock.Mock(name="entry")
            mockEntry.mode = "expectedMode"
            mocks["extendedExcludeGcodes"].get.return_value = mockEntry
            mocks["_processExtendedGcodeEntry"].return_value = "expectedResult"

            result = unit.processExtendedGcode("G1 X1 Y2", "G1", None)

            mocks["extendedExcludeGcodes"].get.assert_called_with("G1")
            mocks["_processExtendedGcodeEntry"].assert_called_with("expectedMode", "G1 X1 Y2", "G1")
            self.assertEqual(
                result, "expectedResult",
                "The expected result of _processExtendedGcodeEntry should be returned"
            )

    def test_processExtendedGcode_notExcluding_matchExists(self):
        """Test processExtendedGcode when not excluding and a matching entry exists."""
        mockLogger = mock.Mock()
        mockLogger.isEnabledFor.return_value = False  # For coverage of logging condition
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.multiple(
            unit,
            extendedExcludeGcodes=mock.DEFAULT,
            _processExtendedGcodeEntry=mock.DEFAULT
        ) as mocks:
            unit.excluding = False
            mockEntry = mock.Mock(name="entry")
            mockEntry.mode = "expectedMode"
            mocks["extendedExcludeGcodes"].get.return_value = mockEntry

            result = unit.processExtendedGcode("G1 X1 Y2", "G1", None)

            mocks["extendedExcludeGcodes"].get.assert_not_called()
            mocks["_processExtendedGcodeEntry"].assert_not_called()
            self.assertIsNone(result, "The return value should be None")
