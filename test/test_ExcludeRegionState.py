# coding=utf-8
"""Unit tests for the more advanced functionality of the ExcludeRegionState class."""

from __future__ import absolute_import, division
from collections import OrderedDict

import time
import mock
from callee.operators import In as AnyIn

from octoprint_excluderegion.ExcludeRegionState import ExcludeRegionState
from octoprint_excluderegion.RetractionState import RetractionState
from octoprint_excluderegion.GcodeHandlers import INCH_TO_MM_FACTOR

from .utils import TestCase, create_position


class ExcludeRegionStateTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for the more advanced functionality of the ExcludeRegionState class."""

    def test_recordRetraction_noLastRetraction_excluding(self):
        """Test recordRetraction when there is no lastRetraction and isExcluding is True."""
        expectedReturnCommands = ["addedCommand"]

        mockRetractionState = mock.Mock()
        mockRetractionState.generateRetractCommands.return_value = expectedReturnCommands

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = True
        unit.lastRetraction = None

        returnCommands = unit.recordRetraction(mockRetractionState)

        mockRetractionState.generateRetractCommands.assert_called_with(unit.position)
        self.assertEqual(
            returnCommands, expectedReturnCommands,
            "The expected command(s) should be returned"
        )

    def test_recordRetraction_noLastRetraction_notExcluding(self):
        """Test recordRetraction with no lastRetraction and not excluding."""
        mockRetractionState = mock.Mock()
        mockRetractionState.originalCommand = "retractionCommand"

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False
        unit.lastRetraction = None

        returnCommands = unit.recordRetraction(mockRetractionState)

        mockRetractionState.generateRetractCommands.assert_not_called()
        self.assertEqual(
            returnCommands, ["retractionCommand"],
            "The original retraction command should be returned"
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

            returnCommands = unit.recordRetraction(mockRetractionState)

            self.assertFalse(
                unit.lastRetraction.recoverExcluded,
                "lastRetraction.recoverExcluded should be set to False"
            )

            self.assertEqual(
                unit.lastRetraction.feedRate, 20,
                "The retraction feedRate should be updated."
            )

            self.assertEqual(
                returnCommands, [],
                "The result should be an empty list."
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

            returnCommands = unit.recordRetraction(mockRetractionState)

            self.assertFalse(
                unit.lastRetraction.recoverExcluded,
                "lastRetraction.recoverExcluded should be set to False"
            )

            self.assertIsNone(
                unit.lastRetraction.feedRate,
                "The retraction feedRate should not be modified."
            )

            self.assertEqual(
                returnCommands, [],
                "The result should be an empty list."
            )

    def test_recordRetraction_noRecoverExcluded_allowCombine_excluding(self):
        """Test recordRetraction with recoverExcluded=False, allowCombine=True and excluding."""
        expectedReturnCommands = ["addedCommand"]

        mockRetractionState = mock.Mock()
        mockRetractionState.generateRetractCommands.return_value = expectedReturnCommands

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction'):
            unit.lastRetraction.recoverExcluded = False
            unit.lastRetraction.allowCombine = True
            unit.excluding = True

            returnCommands = unit.recordRetraction(mockRetractionState)

            unit.lastRetraction.combine.assert_called_with(mockRetractionState, mockLogger)
            mockRetractionState.generateRetractCommands.assert_called_with(unit.position)
            self.assertEqual(
                returnCommands, expectedReturnCommands,
                "The result from generateRetractCommands should be returned."
            )

    def test_recordRetraction_noRecoverExcluded_allowCombine_notExcluding(self):
        """Test recordRetraction with recoverExcluded=False, allowCombine=True and not excluding."""
        expectedReturnCommands = ["retractionCommand"]

        mockRetractionState = mock.Mock()
        mockRetractionState.originalCommand = "retractionCommand"

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction'):
            unit.lastRetraction.recoverExcluded = False
            unit.lastRetraction.allowCombine = True
            unit.excluding = False

            returnCommands = unit.recordRetraction(mockRetractionState)

            self.assertEqual(
                returnCommands, expectedReturnCommands,
                "The original command should be returned"
            )

    def test_recordRetraction_noRecoverExcluded_noCombine_excluding(self):
        """Test recordRetraction with recoverExcluded=False and excluding."""
        mockRetractionState = mock.Mock()

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction'):
            unit.lastRetraction.recoverExcluded = False
            unit.lastRetraction.allowCombine = False
            unit.excluding = True

            returnCommands = unit.recordRetraction(mockRetractionState)

            self.assertEqual(
                returnCommands, [],
                "The result should be an empty list."
            )

    def test_recordRetraction_noRecoverExcluded_noCombine_notExcluding(self):
        """Test recordRetraction with recoverExcluded=False and not excluding."""
        mockRetractionState = mock.Mock()
        mockRetractionState.originalCommand = "retractionCommand"

        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction'):
            unit.lastRetraction.recoverExcluded = False
            unit.lastRetraction.allowCombine = False
            unit.excluding = False

            returnCommands = unit.recordRetraction(mockRetractionState)

            mockRetractionState.generateRetractCommands.assert_not_called()
            self.assertEqual(
                returnCommands, ["retractionCommand"],
                "The original command should be returned"
            )

    def test_recoverRetraction_recoverExcluded(self):
        """Test _recoverRetraction with recoverExcluded=True."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction') as lastRetractionMock:
            unit.lastRetraction.recoverExcluded = True
            unit.lastRetraction.generateRecoverCommands.return_value = ["recoverCommand"]

            result = unit._recoverRetraction("G11", True)  # pylint: disable=protected-access

            # The test against this mock covers both cases where returnCommands None and when it is
            # a list of commands since the final result is built from the generateRecoverCommands
            # result which is mocked anyway
            lastRetractionMock.generateRecoverCommands.assert_called_with(unit.position)
            self.assertIsNone(unit.lastRetraction, "The lastRetraction should be set to None")
            self.assertEqual(
                result, ["recoverCommand", "G11"],
                "The result should contain two items"
            )

    def test_recoverRetraction_noRecoverExcluded(self):
        """Test _recoverRetraction with recoverExcluded=False."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, 'lastRetraction') as lastRetractionMock:
            unit.lastRetraction.recoverExcluded = False

            result = unit._recoverRetraction("G11", True)  # pylint: disable=protected-access

            lastRetractionMock.generateRecoverCommands.assert_not_called()
            self.assertIsNone(unit.lastRetraction, "The lastRetraction should be set to None")
            self.assertEqual(result, ["G11"], "The result should contain one item")

    def test_recoverRetractionIfNeeded_lastRetraction_excluding_isRecoveryCommand(self):
        """Test recoverRetractionIfNeeded with lastRetraction, isRecoveryCommand and excluding."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.multiple(
            unit,
            _recoverRetraction=mock.DEFAULT,
            lastRetraction=mock.DEFAULT
        ) as mocks:
            unit.excluding = True
            unit.lastRetraction.recoverExcluded = False
            unit.lastRetraction.allowCombine = True

            result = unit.recoverRetractionIfNeeded("G11", True)

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
            self.assertFalse(
                unit.lastRetraction.allowCombine,
                "allowCombine should be set to False"
            )
            self.assertEqual(
                result, [],
                "The result should be an empty list."
            )

    def test_recoverRetractionIfNeeded_lastRetraction_excluding_notRecoveryCommand(self):
        """Test recoverRetractionIfNeeded with lastRetraction, excluding and NO recoveryCommand."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.multiple(
            unit,
            _recoverRetraction=mock.DEFAULT,
            lastRetraction=mock.DEFAULT
        ) as mocks:
            unit.excluding = True
            unit.lastRetraction.recoverExcluded = False
            unit.lastRetraction.allowCombine = True

            result = unit.recoverRetractionIfNeeded("G1 X1 Y2 E3", False)

            # The test against this mock covers both cases where returnCommands None and when it is
            # a list of commands since the final result is built from the _recoverRetraction result
            # which is mocked anyway
            mocks["_recoverRetraction"].assert_not_called()
            self.assertEqual(
                unit.lastRetraction, mocks["lastRetraction"],
                "The lastRetraction should not be updated"
            )
            self.assertFalse(
                unit.lastRetraction.allowCombine,
                "allowCombine should be set to False"
            )
            self.assertFalse(
                unit.lastRetraction.recoverExcluded,
                "recoverExcluded should not be updated"
            )
            self.assertEqual(
                result, [],
                "The result should be an empty list."
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
            unit.lastRetraction.allowCombine = True
            mocks["_recoverRetraction"].return_value = ["expectedCommand"]

            result = unit.recoverRetractionIfNeeded("G11", True)

            mocks["_recoverRetraction"].assert_called_with("G11", True)
            self.assertEqual(
                unit.lastRetraction, mocks["lastRetraction"],
                "The lastRetraction should not be updated"
            )
            self.assertFalse(
                unit.lastRetraction.allowCombine,
                "allowCombine should be set to False"
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

            result = unit.recoverRetractionIfNeeded("G11", True)

            recoverRetractionMock.assert_not_called()
            self.assertIsNone(unit.lastRetraction, "The lastRetraction should not be updated")
            self.assertEqual(
                result, [],
                "The result should be an empty list."
            )

    def test_recoverRetractionIfNeeded_noLastRetraction_notExcluding_notRecoveryCommand(self):
        """Test recoverRetractionIfNeeded with NO lastRetraction, not excluding, not recovery."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, '_recoverRetraction') as recoverRetractionMock:
            unit.lastRetraction = None
            unit.excluding = False

            result = unit.recoverRetractionIfNeeded("G1 X1 Y1", False)

            recoverRetractionMock.assert_not_called()
            self.assertIsNone(unit.lastRetraction, "The lastRetraction should not be updated")
            self.assertEqual(
                result, ["G1 X1 Y1"],
                "The result should contain only the provided command"
            )

    def test_recoverRetractionIfNeeded_noLastRetraction_notExcluding_isRecoveryCommand(self):
        """Test recoverRetractionIfNeeded with NO lastRetraction, not excluding, is recovery."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        with mock.patch.object(unit, '_recoverRetraction') as recoverRetractionMock:
            unit.lastRetraction = None
            unit.excluding = False

            result = unit.recoverRetractionIfNeeded("G1 E1", True)

            recoverRetractionMock.assert_not_called()
            self.assertIsNone(unit.lastRetraction, "The lastRetraction should not be updated")
            self.assertEqual(
                result, ["G1 E1"],
                "The result should contain only the provided command"
            )

    def test_processNonMove_deltaE_negative(self):
        """Test _processNonMove when deltaE < 0."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.object(unit, 'recordRetraction') as mockRecordRetraction:
            mockRecordRetraction.return_value = ["returnedCommand"]
            unit.feedRate = 100

            result = unit._processNonMove(  # pylint: disable=protected-access
                "G0 E-1 F100",
                -1
            )

            mockRecordRetraction.assert_called_with(
                RetractionState(
                    originalCommand="G0 E-1 F100",
                    firmwareRetract=False,
                    extrusionAmount=1,
                    feedRate=100
                )
            )
            self.assertEqual(
                result, ["returnedCommand"],
                "The result should match the value returned by recordRetraction"
            )

    def test_processNonMove_deltaE_positive(self):
        """Test _processNonMove when deltaE > 0."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.object(unit, 'recoverRetractionIfNeeded') as mockRecoverRetractionIfNeeded:
            mockRecoverRetractionIfNeeded.return_value = ["returnedCommand"]
            unit.feedRate = 100

            result = unit._processNonMove("G0 E1 F100", 1)  # pylint: disable=protected-access

            mockRecoverRetractionIfNeeded.assert_called_with("G0 E1 F100", True)
            self.assertEqual(
                result, ["returnedCommand"],
                "The result should match the value returned by recoverRetractionIfNeeded"
            )

    def test_processNonMove_deltaE_zero_excluding(self):
        """Test _processNonMove when deltaE is 0 and excluding."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.multiple(
            unit,
            recordRetraction=mock.DEFAULT,
            recoverRetractionIfNeeded=mock.DEFAULT
        ) as mocks:
            unit.excluding = True
            unit.feedRate = 100

            result = unit._processNonMove("G0 E0 F100", 0)  # pylint: disable=protected-access

            mocks["recordRetraction"].assert_not_called()
            mocks["recoverRetractionIfNeeded"].assert_not_called()
            self.assertEqual(result, [], "The result should be an empty list")

    def test_processNonMove_deltaE_zero_notExcluding(self):
        """Test _processNonMove when deltaE is 0 and not excluding."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.multiple(
            unit,
            recordRetraction=mock.DEFAULT,
            recoverRetractionIfNeeded=mock.DEFAULT
        ) as mocks:
            unit.excluding = False
            unit.feedRate = 100

            result = unit._processNonMove("G0 E0 F100", 0)  # pylint: disable=protected-access

            mocks["recordRetraction"].assert_not_called()
            mocks["recoverRetractionIfNeeded"].assert_not_called()
            self.assertEqual(
                result, ["G0 E0 F100"],
                "The result should be a list containing the command"
            )

    def test_processExcludedMove_excluding_retract(self):
        """Test _processExcludedMove with a retraction while moving and excluding=True."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = True

        with mock.patch.multiple(
            unit,
            enterExcludedRegion=mock.DEFAULT,
            _processNonMove=mock.DEFAULT
        ) as mocks:
            mocks["_processNonMove"].return_value = ["processNonMove"]

            result = unit._processExcludedMove("G1 X10 Y20", -1)  # pylint: disable=protected-access

            mocks["enterExcludedRegion"].assert_not_called()
            mocks["_processNonMove"].assert_called_with("G1 X10 Y20", -1)
            self.assertEqual(
                result, ["processNonMove"],
                "The result should be the commands returned by _processNonMove"
            )

    def test_processExcludedMove_excluding_nonRetract(self):
        """Test _processExcludedMove with a non-retraction move and excluding=True."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = True

        with mock.patch.multiple(
            unit,
            enterExcludedRegion=mock.DEFAULT,
            _processNonMove=mock.DEFAULT
        ) as mocks:
            result = unit._processExcludedMove("G1 X10 Y20", 0)  # pylint: disable=protected-access

            mocks["enterExcludedRegion"].assert_not_called()
            mocks["_processNonMove"].assert_not_called()
            self.assertEqual(result, [], "The result should be an empty list")

    def test_processExcludedMove_notExcluding_retract(self):
        """Test _processExcludedMove with a retraction while moving and excluding=False."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False

        with mock.patch.multiple(
            unit,
            enterExcludedRegion=mock.DEFAULT,
            _processNonMove=mock.DEFAULT
        ) as mocks:
            mocks["enterExcludedRegion"].return_value = ["enterExcludedRegion"]
            mocks["_processNonMove"].return_value = ["processNonMove"]

            result = unit._processExcludedMove("G1 X10 Y20", -1)  # pylint: disable=protected-access

            mocks["enterExcludedRegion"].assert_called_with("G1 X10 Y20")
            mocks["_processNonMove"].assert_called_with("G1 X10 Y20", -1)
            self.assertEqual(
                result, ["enterExcludedRegion", "processNonMove"],
                "The result should contain the expected commands"
            )

    def test_processExcludedMove_notExcluding_nonRetract(self):
        """Test _processExcludedMove with a non-retraction move and excluding=False."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = False

        with mock.patch.multiple(
            unit,
            enterExcludedRegion=mock.DEFAULT,
            _processNonMove=mock.DEFAULT
        ) as mocks:
            mocks["enterExcludedRegion"].return_value = ["enterExcludedRegion"]

            result = unit._processExcludedMove("G1 X10 Y20", 0)  # pylint: disable=protected-access

            mocks["enterExcludedRegion"].assert_called_with("G1 X10 Y20")
            mocks["_processNonMove"].assert_not_called()
            self.assertEqual(
                result,
                ["enterExcludedRegion"],
                "The result should be the commands returned by enterExcludedRegion"
            )

    def test_enterExcludedRegion_exclusionDisabled(self):
        """Test enterExcludedRegion when exclusion is disabled should raise an AssertionError."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.disableExclusion("Disable for test")

        with self.assertRaises(AssertionError):
            unit.enterExcludedRegion("G1 X1 Y2")

    def test_enterExcludedRegion_excluding(self):
        """Test enterExcludedRegion when already excluding."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.excluding = True
        unit.numCommands = 10

        result = unit.enterExcludedRegion("G1 X1 Y2")

        self.assertEqual(unit.numCommands, 10, "The numCommands should not be updated.")
        self.assertEqual(result, [], "An empty list should be returned.")

    def _test_enterExcludedRegion_common(self, enteringExcludedRegionGcode):
        """Test common functionality of enterExcludedRegion when exclusion is enabled."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.excluding = False
        unit.excludeStartTime = "oldStartTime"
        unit.numExcludedCommands = 42
        unit.numCommands = 84
        unit.lastPosition = "oldPosition"

        unit.enteringExcludedRegionGcode = enteringExcludedRegionGcode

        result = unit.enterExcludedRegion("G1 X1 Y2")

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

    def test_enterExcludedRegion_noEnteringExcludeRegionGcode(self):
        """Test enterExcludedRegion with no enter region script."""
        result = self._test_enterExcludedRegion_common(None)
        self.assertEqual(result, [], "The result should be an empty list")

    def test_enterExcludedRegion_withEnteringExcludeRegionGcode(self):
        """Test enterExcludedRegion with an enter region script."""
        result = self._test_enterExcludedRegion_common(["scriptCommand"])
        self.assertEqual(
            result, ["scriptCommand"],
            "The result should match the enteringExcludeRegionGcode"
        )

    def test_processPendingCommands_noPendingCommands_noExitScript(self):
        """Test _processPendingCommands if no pending commands and no exit script."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = OrderedDict()
        unit.exitingExcludedRegionGcode = None

        result = unit._processPendingCommands()  # pylint: disable=protected-access

        self.assertEqual(
            unit.pendingCommands, OrderedDict(),
            "The pendingCommands should be an empty dict"
        )
        self.assertEqual(result, [], "The result should be an empty list.")

    def test_processPendingCommands_noPendingCommands_withExitScript(self):
        """Test _processPendingCommands if no pending commands and exit script is provided."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = OrderedDict()
        unit.exitingExcludedRegionGcode = ["exitCommand"]

        result = unit._processPendingCommands()  # pylint: disable=protected-access

        self.assertEqual(
            unit.pendingCommands, OrderedDict(),
            "The pendingCommands should be an empty dict"
        )
        self.assertEqual(
            result, ["exitCommand"],
            "The result should be the list of exit script commands"
        )

    def test_processPendingCommands_withPendingCommands_noExitScript(self):
        """Test _processPendingCommands if pending commands exist and no exit script."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands["G1"] = {"X": 1.0, "Y": 2.0}      # Ensure dict is processed correctly
        unit.pendingCommands["G11"] = "G11 S1"             # Ensure string is processed correctly
        unit.exitingExcludedRegionGcode = None

        result = unit._processPendingCommands()  # pylint: disable=protected-access

        self.assertEqual(
            unit.pendingCommands,
            OrderedDict(),
            "The pendingCommands should be an empty dict"
        )
        self.assertEqual(
            result,
            [
                AnyIn([
                    "G1 X%s Y%s" % (1.0, 2.0),
                    "G1 Y%s X%s" % (2.0, 1.0)
                ]),
                "G11 S1"
            ],
            "The result should contain the expected pending commands"
        )

    def test_processPendingCommands_withPendingCommands_withExitScript(self):
        """Test _processPendingCommands if pending commands exist and exit script is provided."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands["G1"] = {"X": 1.0, "Y": 2.0}      # Ensure dict is processed correctly
        unit.pendingCommands["G11"] = "G11 S1"             # Ensure string is processed correctly

        unit.exitingExcludedRegionGcode = ["exitCommand"]

        result = unit._processPendingCommands()  # pylint: disable=protected-access

        self.assertEqual(
            unit.pendingCommands,
            OrderedDict(),
            "The pendingCommands should be an empty dict"
        )
        self.assertEqual(
            result,
            [
                AnyIn([
                    "G1 X%s Y%s" % (1.0, 2.0),
                    "G1 Y%s X%s" % (2.0, 1.0)
                ]),
                "G11 S1",
                "exitCommand"
            ],
            "The result should contain the expected pending commands plus the exit script"
        )

    def test_exitExcludedRegion_notExcluding(self):
        """Test exitExcludedRegion when not currently excluding."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.excluding = False

        with mock.patch.object(unit, '_processPendingCommands') as mockProcessPendingCommands:
            result = unit.exitExcludedRegion("G1 X1 Y2")

            mockProcessPendingCommands.assert_not_called()
            self.assertEqual(result, [], "An empty list should be returned.")

    def test_exitExcludedRegion_unitMultiplier(self):
        """Test exitExcludedRegion when a non-native unit multiplier is in effect."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.excluding = True
        unit.excludeStartTime = time.time()
        unit.feedRate = 1000
        unit.feedRateUnitMultiplier = INCH_TO_MM_FACTOR
        unit.lastPosition = create_position(
            x=1, y=2, z=3, extruderPosition=4,
            unitMultiplier=INCH_TO_MM_FACTOR
        )
        unit.position = create_position(
            x=10, y=20, z=30, extruderPosition=40,
            unitMultiplier=INCH_TO_MM_FACTOR
        )

        with mock.patch.object(unit, '_processPendingCommands') as mockProcessPendingCommands:
            mockProcessPendingCommands.return_value = []

            result = unit.exitExcludedRegion("G1 X1 Y2")

            mockProcessPendingCommands.assert_called_with()
            self.assertEqual(
                result,
                [
                    "G92 E%s" % (40 / INCH_TO_MM_FACTOR),
                    "G0 F%s Z%s" % (
                        1000 / INCH_TO_MM_FACTOR,
                        30 / INCH_TO_MM_FACTOR
                    ),
                    "G0 F%s X%s Y%s" % (
                        1000 / INCH_TO_MM_FACTOR,
                        10 / INCH_TO_MM_FACTOR,
                        20 / INCH_TO_MM_FACTOR
                    )
                ],
                "The result should be a list of the expected commands."
            )
            self.assertFalse(unit.excluding, "The excluding flag should be cleared.")

    def test_exitExcludedRegion_zUnchanged(self):
        """Test exitExcludedRegion when the final Z matches the initial Z."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.excluding = True
        unit.excludeStartTime = time.time()
        unit.feedRate = 1000.0
        unit.feedRateUnitMultiplier = 1.0
        unit.lastPosition = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.position = create_position(x=10, y=20, z=3, extruderPosition=40)

        with mock.patch.object(unit, '_processPendingCommands') as mockProcessPendingCommands:
            mockProcessPendingCommands.return_value = ["pendingCommand"]

            result = unit.exitExcludedRegion("G1 X1 Y2")

            mockProcessPendingCommands.assert_called_with()
            self.assertEqual(
                result,
                [
                    "pendingCommand",
                    "G92 E{e}".format(e=40.0),
                    "G0 F{f} X{x} Y{y}".format(f=1000.0, x=10.0, y=20.0)
                ],
                "The result should be a list of the expected commands."
            )
            self.assertFalse(unit.excluding, "The excluding flag should be cleared.")

    def test_exitExcludedRegion_zDecreased(self):
        """Test exitExcludedRegion when the final Z is less than the initial Z."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.excluding = True
        unit.excludeStartTime = time.time()
        unit.feedRate = 1000
        unit.feedRateUnitMultiplier = 1
        unit.lastPosition = create_position(x=1, y=2, z=30, extruderPosition=4)
        unit.position = create_position(x=10, y=20, z=3, extruderPosition=40)

        with mock.patch.object(unit, '_processPendingCommands') as mockProcessPendingCommands:
            mockProcessPendingCommands.return_value = ["pendingCommand"]

            result = unit.exitExcludedRegion("G1 X1 Y2")

            mockProcessPendingCommands.assert_called_with()
            self.assertEqual(
                result,
                [
                    "pendingCommand",
                    "G92 E%s" % (40.0),
                    "G0 F%s X%s Y%s" % (1000.0, 10.0, 20.0),
                    "G0 F%s Z%s" % (1000.0, 3.0)
                ],
                "The result should be a list of the expected commands."
            )
            self.assertFalse(unit.excluding, "The excluding flag should be cleared.")

    def test_exitExcludedRegion_zIncreased(self):
        """Test exitExcludedRegion when the final Z is greater than the initial Z."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.excluding = True
        unit.excludeStartTime = time.time()
        unit.feedRate = 1000
        unit.feedRateUnitMultiplier = 1
        unit.lastPosition = create_position(x=1, y=2, z=3, extruderPosition=4)
        unit.position = create_position(x=10, y=20, z=30, extruderPosition=40)

        with mock.patch.object(unit, '_processPendingCommands') as mockProcessPendingCommands:
            mockProcessPendingCommands.return_value = ["pendingCommand"]

            result = unit.exitExcludedRegion("G1 X1 Y2")

            mockProcessPendingCommands.assert_called_with()
            self.assertEqual(
                result,
                [
                    "pendingCommand",
                    "G92 E%s" % (40.0),
                    "G0 F%s Z%s" % (1000.0, 30.0),
                    "G0 F%s X%s Y%s" % (1000.0, 10.0, 20.0)
                ],
                "The result should be a list of the expected commands."
            )
            self.assertFalse(unit.excluding, "The excluding flag should be cleared.")
