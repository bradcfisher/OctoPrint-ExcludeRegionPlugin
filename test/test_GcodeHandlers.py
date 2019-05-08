# coding=utf-8
"""Unit tests for the GcodeHandlers class."""

from __future__ import absolute_import

import mock

from octoprint_excluderegion.GcodeHandlers import GcodeHandlers
from octoprint_excluderegion.AtCommandAction import ENABLE_EXCLUSION, DISABLE_EXCLUSION

from .utils import TestCase


class GcodeHandlersTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for the GcodeHandlers class."""

    expectedProperties = ["_logger", "state"]

    def test_constructor(self):
        """Test the constructor when passed logger and state instances."""
        # pylint: disable=protected-access
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        unit = GcodeHandlers(mockState, mockLogger)

        self.assertIsInstance(unit, GcodeHandlers)
        self.assertIs(unit._logger, mockLogger, "The logger should match the instance passed in")
        self.assertIs(unit.state, mockState, "The state should match the instance passed in")

    def test_constructor_missingState(self):
        """Test the constructor when passed a logger, but no state."""
        mockLogger = mock.Mock()

        with self.assertRaises(AssertionError):
            GcodeHandlers(None, mockLogger)

    def test_constructor_missingLogger(self):
        """Test the constructor when passed a state, but no logger."""
        mockState = mock.Mock()

        with self.assertRaises(AssertionError):
            GcodeHandlers(mockState, None)

    def test_handleAtCommand_noHandler(self):  # pylint: disable=no-self-use
        """Test handleAtCommand when no matching command handler is defined."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockCommInstance = mock.Mock()
        mockEntry = mock.Mock()

        mockState.atCommandActions = mock.Mock(wraps={"NoMatch": [mockEntry]})

        unit = GcodeHandlers(mockState, mockLogger)

        unit.handleAtCommand(mockCommInstance, "NotDefined", "params")

        mockState.atCommandActions.get.assert_called_with("NotDefined")
        mockEntry.matches.assert_not_called()
        mockState.enableExclusion.assert_not_called()
        mockState.disableExclusion.assert_not_called()
        mockCommInstance.sendCommand.assert_not_called()

    def test_handleAtCommand_oneHandler_noParamMatch(self):  # pylint: disable=no-self-use
        """Test handleAtCommand when one command handler is defined, but the params don't match."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockCommInstance = mock.Mock()
        mockEntry = mock.Mock()
        mockEntry.matches.return_value = None

        mockState.atCommandActions = mock.Mock(wraps={"DefinedCommand": [mockEntry]})

        unit = GcodeHandlers(mockState, mockLogger)

        unit.handleAtCommand(mockCommInstance, "DefinedCommand", "params")

        mockState.atCommandActions.get.assert_called_with("DefinedCommand")
        mockEntry.matches.assert_called_with("DefinedCommand", "params")
        mockState.enableExclusion.assert_not_called()
        mockState.disableExclusion.assert_not_called()
        mockCommInstance.sendCommand.assert_not_called()

    def test_handleAtCommand_multipleHandlers_noParamMatch(self):  # pylint: disable=no-self-use
        """Test handleAtCommand when multiple command handlers defined, but no param matches."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockCommInstance = mock.Mock()

        mockEntry1 = mock.Mock()
        mockEntry1.matches.return_value = None

        mockEntry2 = mock.Mock()
        mockEntry2.matches.return_value = None

        mockState.atCommandActions = mock.Mock(wraps={"DefinedCommand": [mockEntry1, mockEntry2]})

        unit = GcodeHandlers(mockState, mockLogger)

        unit.handleAtCommand(mockCommInstance, "DefinedCommand", "params")

        mockState.atCommandActions.get.assert_called_with("DefinedCommand")
        mockEntry1.matches.assert_called_with("DefinedCommand", "params")
        mockEntry2.matches.assert_called_with("DefinedCommand", "params")
        mockState.enableExclusion.assert_not_called()
        mockState.disableExclusion.assert_not_called()
        mockCommInstance.sendCommand.assert_not_called()

    def test_handleAtCommand_oneHandler_match_ENABLE_EXCLUSION(self):  # pylint: disable=no-self-use
        """Test handleAtCommand when one matching handler that enables exclusion is matched."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockCommInstance = mock.Mock()
        mockEntry = mock.Mock()
        mockEntry.action = ENABLE_EXCLUSION
        mockEntry.matches.return_value = True

        mockState.atCommandActions = mock.Mock(wraps={"DefinedCommand": [mockEntry]})

        unit = GcodeHandlers(mockState, mockLogger)

        unit.handleAtCommand(mockCommInstance, "DefinedCommand", "params")

        mockState.atCommandActions.get.assert_called_with("DefinedCommand")
        mockEntry.matches.assert_called_with("DefinedCommand", "params")
        mockState.enableExclusion.assert_called_once()
        mockState.disableExclusion.assert_not_called()
        mockCommInstance.sendCommand.assert_not_called()

    def test_handleAtCommand_oneHandler_match_DISABLE_EXCLUSION(
            self
    ):  # pylint: disable=no-self-use
        """Test handleAtCommand when one matching handler that disables exclusion is matched."""
        mockLogger = mock.Mock()

        mockState = mock.Mock()
        mockState.disableExclusion.return_value = ["Command1", "Command2"]

        mockCommInstance = mock.Mock()

        mockEntry = mock.Mock()
        mockEntry.action = DISABLE_EXCLUSION
        mockEntry.matches.return_value = True

        mockState.atCommandActions = mock.Mock(wraps={"DefinedCommand": [mockEntry]})

        unit = GcodeHandlers(mockState, mockLogger)

        unit.handleAtCommand(mockCommInstance, "DefinedCommand", "params")

        mockState.atCommandActions.get.assert_called_with("DefinedCommand")
        mockEntry.matches.assert_called_with("DefinedCommand", "params")
        mockState.enableExclusion.assert_not_called()
        mockState.disableExclusion.assert_called_once()
        mockCommInstance.sendCommand.assert_has_calls(
            [mock.call("Command1"), mock.call("Command2")]
        )

    def test_handleAtCommand_multipleHandlers_match(self):
        """Test handleAtCommand when multiple command handlers are defined and match."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockCommInstance = mock.Mock()

        mockEntry1 = mock.Mock()
        mockEntry1.action = ENABLE_EXCLUSION
        mockEntry1.matches.return_value = True

        mockEntry2 = mock.Mock()
        mockEntry2.action = ENABLE_EXCLUSION
        mockEntry2.matches.return_value = True

        mockState.atCommandActions = mock.Mock(wraps={"DefinedCommand": [mockEntry1, mockEntry2]})

        unit = GcodeHandlers(mockState, mockLogger)

        unit.handleAtCommand(mockCommInstance, "DefinedCommand", "params")

        mockState.atCommandActions.get.assert_called_with("DefinedCommand")
        mockEntry1.matches.assert_called_with("DefinedCommand", "params")
        mockEntry2.matches.assert_called_with("DefinedCommand", "params")
        self.assertEqual(
            mockState.enableExclusion.call_count, 2,
            "enableExclusion should be called twice"
        )
        mockState.disableExclusion.assert_not_called()
        mockCommInstance.sendCommand.assert_not_called()

    def test_handleGcode_noHandler(self):
        """Test handleGcode when no specific handler is defined."""
        mockLogger = mock.Mock()

        mockState = mock.Mock()
        mockState.numCommands = 0

        unit = GcodeHandlers(mockState, mockLogger)

        unit.handleGcode("NoHandler some args", "NoHandler")

        self.assertEqual(mockState.numCommands, 1, "state.numCommands should be incremented")
        unit.state.processExtendedGcode.assert_called_with("NoHandler some args", "NoHandler", None)

    def test_handleGcode_matchingHandler(self):
        """Test handleGcode when a matching handler is defined."""
        mockLogger = mock.Mock()

        mockState = mock.Mock()
        mockState.numCommands = 0

        expectedResult = ["Command1", "Command2"]
        mockHandler = mock.Mock()
        mockHandler.return_value = expectedResult

        unit = GcodeHandlers(mockState, mockLogger)
        unit._handle_TestHandler = mockHandler  # pylint: disable=protected-access

        result = unit.handleGcode("TestHandler some args", "TestHandler")

        self.assertEqual(mockState.numCommands, 1, "state.numCommands should be incremented")
        unit.state.processExtendedGcode.assert_not_called()
        mockHandler.assert_called_with("TestHandler some args", "TestHandler", None)
        self.assertEqual(result, expectedResult, "A list of two commands should be returned")

    def test_handle_G0(self):
        """Test the _handle_G0 method."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        expectedResult = ["Command1", "Command2"]
        mockState.processLinearMoves.return_value = expectedResult

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G0(  # pylint: disable=protected-access
            "G0 E1 F2 X3 Y4 Z5",
            "G0",
            None
        )

        mockState.processLinearMoves.assert_called_with(
            "G0 E1 F2 X3 Y4 Z5",
            1, 2, 5, 3, 4
        )
        self.assertEqual(result, expectedResult, "A list of two commands should be returned")

    def test_handle_G1(self):
        """Test the _handle_G1 method."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        expectedResult = ["Command1", "Command2"]
        mockG0Handler = mock.Mock()
        mockG0Handler.return_value = expectedResult

        unit = GcodeHandlers(mockState, mockLogger)
        unit._handle_G0 = mockG0Handler  # pylint: disable=protected-access

        result = unit._handle_G1(  # pylint: disable=protected-access
            "G1 E1 F2 X3 Y4 Z5",
            "G1",
            None
        )

        mockG0Handler.assert_called_with(
            "G1 E1 F2 X3 Y4 Z5", "G1", None
        )
        self.assertEqual(result, expectedResult, "A list of two commands should be returned")

    def test_handle_G2_clockwise(self):  # pylint: disable=no-self-use
        """Test the _handle_G2 method creates clockwise arcs when passed a G2 command."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (0, 0)

        unit._handle_G2("G2 R30", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(mock.ANY, mock.ANY, mock.ANY, True)

    def test_handle_G2_counterClockwise(self):  # pylint: disable=no-self-use
        """Test the _handle_G2 method creates counter-clockwise arcs when passed a G3 command."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (0, 0)

        unit._handle_G2("G3 R30", "G3", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(mock.ANY, mock.ANY, mock.ANY, False)

    def test_handle_G2_zeroRadius(self):
        """Test the _handle_G2 method ignores the command when passed a zero radius."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock(wraps=unit.computeArcCenterOffsets)
        unit.planArc = mock.Mock(wraps=unit.planArc)

        result = unit._handle_G2("G2 R0 X10 Y20", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(10, 20, 0, True)
        unit.planArc.assert_not_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_G2_radius_invalidEndPoint(self):
        """Test _handle_G2 ignores the command when passed a non-zero radius, but no end point."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockState.position.X_AXIS.nativeToLogical.return_value = 10
        mockState.position.Y_AXIS.nativeToLogical.return_value = 20

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock(wraps=unit.computeArcCenterOffsets)
        unit.planArc = mock.Mock(wraps=unit.planArc)

        result = unit._handle_G2("G2 R30", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(10, 20, 30, True)
        unit.planArc.assert_not_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_G2_negativeRadius(self):  # pylint: disable=no-self-use
        """Test the _handle_G2 method correctly parses a negative radius value."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (0, 0)

        unit._handle_G2("G2 R-12 X8 Y0", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(8, 0, -12, True)

    def test_handle_G2_radiusTrumpsOffsets(self):  # pylint: disable=no-self-use
        """Test the _handle_G2 method to ensure offsets (I, J) are ignored if a radius is given."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (12, 13)
        unit.planArc = mock.Mock()
        unit.planArc.return_value = [0, 1, 2, 3]

        unit._handle_G2("G2 R20 I8 J9 X10 Y0", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(10, 0, 20, True)
        unit.planArc.assert_called_with(10, 0, 12, 13, True)

    def test_handle_G2_noRadiusOrCenterOffset(self):
        """Test the _handle_G2 method when no radius or center offsets are passed."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.planArc = mock.Mock()

        result = unit._handle_G2("G2 X10 Y0", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_not_called()
        unit.planArc.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handle_G2_invalidCenterOffset(self):
        """Test the _handle_G2 method when passed an invalid center point offset (I=0, J=0)."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.planArc = mock.Mock()

        result = unit._handle_G2("G2 I0 J0 X10 Y0", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_not_called()
        unit.planArc.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handle_G2_radiusMode_paramParsing(self):
        """Test _handle_G2 parameter parsing when a radius is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        mockState.position.X_AXIS.nativeToLogical.return_value = 0
        mockState.position.X_AXIS.nativeToLogical.return_value = 1

        expectedResult = ["Command1", "Command2"]
        mockState.processLinearMoves.return_value = expectedResult

        unit = GcodeHandlers(mockState, mockLogger)

        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (2, 3)
        unit.planArc = mock.Mock()
        unit.planArc.return_value = [4, 5]

        cmd = "G2 R6 X7 Y8 Z9 E10 F11"
        result = unit._handle_G2(cmd, "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(7, 8, 6, True)
        unit.planArc.assert_called_with(7, 8, 2, 3, True)
        mockState.processLinearMoves.assert_called_with(cmd, 10, 11, 9, 4, 5)

        self.assertEqual(result, expectedResult, "A list of two commands should be returned")

    def test_handle_G2_offsetMode_paramParsing(self):
        """Test _handle_G2 parameter parsing when center point offsets are provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        mockState.position.X_AXIS.nativeToLogical.return_value = 0
        mockState.position.X_AXIS.nativeToLogical.return_value = 1

        expectedResult = ["Command1", "Command2"]
        mockState.processLinearMoves.return_value = expectedResult

        unit = GcodeHandlers(mockState, mockLogger)

        unit.computeArcCenterOffsets = mock.Mock()
        unit.planArc = mock.Mock()
        unit.planArc.return_value = [4, 5]

        cmd = "G2 I6.1 J6.2 X7 Y8 Z9 E10 F11"
        result = unit._handle_G2(cmd, "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_not_called()
        unit.planArc.assert_called_with(7, 8, 6.1, 6.2, True)
        mockState.processLinearMoves.assert_called_with(cmd, 10, 11, 9, 4, 5)

        self.assertEqual(result, expectedResult, "A list of two commands should be returned")

    def test_handle_G3(self):
        """Test the _handle_G3 method."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        expectedResult = ["Command1", "Command2"]
        mockG2Handler = mock.Mock()
        mockG2Handler.return_value = expectedResult

        unit = GcodeHandlers(mockState, mockLogger)
        unit._handle_G2 = mockG2Handler  # pylint: disable=protected-access

        result = unit._handle_G3("G3 some args", "G3", None)  # pylint: disable=protected-access

        mockG2Handler.assert_called_with("G3 some args", "G3", None)
        self.assertEqual(result, expectedResult, "A list of two commands should be returned")



# TODO: Complete the remaining test methods

# _handle_G10

# _handle_G11

# _handle_G20

# _handle_G20

# _handle_G28

# _handle_G90

# _handle_G91

# _handle_G92

# _handle_G206

