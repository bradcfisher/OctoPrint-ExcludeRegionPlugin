# coding=utf-8
"""Unit tests for the GcodeHandlers class."""

from __future__ import absolute_import

import mock

from octoprint_excluderegion.GcodeHandlers import GcodeHandlers, INCH_TO_MM_FACTOR
from octoprint_excluderegion.RetractionState import RetractionState

from .utils import TestCase


class GcodeHandlersTests(TestCase):  # pylint: disable=too-many-public-methods, too-many-lines
    """Unit tests for the GcodeHandlers class."""

    expectedProperties = ["_logger", "state"]

    def test_constructor(self):
        """Test the constructor when passed logger and state instances."""
        # pylint: disable=protected-access
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        unit = GcodeHandlers(mockState, mockLogger)

        self.assertIsInstance(unit, GcodeHandlers)
        self.assertProperties(unit, GcodeHandlersTests.expectedProperties)
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

    def test_handle_G0_noArgs(self):
        """Test the _handle_G0 method when no arguments are provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        expectedResult = ["Command1"]
        mockState.processLinearMoves.return_value = expectedResult

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G0("G0", "G0", None)  # pylint: disable=protected-access

        mockState.processLinearMoves.assert_called_with("G0", None, None, None, None, None)
        self.assertEqual(result, expectedResult, "A list of one command should be returned")

    def test_handle_G0_nonFloatArgValue(self):
        """Test the _handle_G0 method when a non float value is provided for an argument."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        expectedResult = ["Command1"]
        mockState.processLinearMoves.return_value = expectedResult

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G0("G0 X. Y-. Z", "G0", None)  # pylint: disable=protected-access

        mockState.processLinearMoves.assert_called_with("G0 X. Y-. Z", None, None, None, None, None)
        self.assertEqual(result, expectedResult, "A list of one command should be returned")

    def test_handle_G0_noEfxyzArgs(self):
        """Test the _handle_G0 method when arguments are provided, but no E/F/X/Y/Z args."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        expectedResult = ["Command1"]
        mockState.processLinearMoves.return_value = expectedResult

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G0("G0 S1", "G0", None)  # pylint: disable=protected-access

        mockState.processLinearMoves.assert_called_with("G0 S1", None, None, None, None, None)
        self.assertEqual(result, expectedResult, "A list of one command should be returned")

    def test_handle_G0_allEfxyzArgs(self):
        """Test the _handle_G0 method when all E/F/X/Y/Z args are provided."""
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

    def test_handle_G0_argCaseInsensitive(self):
        """Test the _handle_G0 method to ensure arguments are not case-sensitive."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockState.processLinearMoves.return_value = "expected"

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G0("G0 e1 f2", "G0", None)  # pylint: disable=protected-access

        mockState.processLinearMoves.assert_called_with("G0 e1 f2", 1, 2, None, None, None)

        self.assertEqual(result, "expected", "The result of processLinearMoves should be returned")

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

    def test_handle_G2_argCaseInsensitive(self):
        """Test the _handle_G2 method to ensure arguments are not case-sensitive."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (0, 0)

        result = unit._handle_G2("G2 r30 x1 y2", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(1, 2, 30, True)
        self.assertIsNone(result, "The result should be None")

    def test_handle_G2_nonFloatArgValue(self):
        """Test the _handle_G2 method when a non float value is provided for an argument."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockState.position.X_AXIS.nativeToLogical.return_value = 10
        mockState.position.Y_AXIS.nativeToLogical.return_value = 20

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (0, 0)

        result = unit._handle_G2("G2 R30 X Y.", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(10, 20, 30, True)
        self.assertIsNone(result, "The result should be None")

    def test_handle_G0_nonXyzefrijArg(self):
        """Test the _handle_G0 method when a non X/Y/Z/E/F/R/I/J argument is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (0, 0)

        result = unit._handle_G2("G2 R30 s1", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(mock.ANY, mock.ANY, 30, True)

        self.assertIsNone(result, "The result should be None")

    def test_handle_G2_clockwise(self):
        """Test the _handle_G2 method creates clockwise arcs when passed a G2 command."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (0, 0)

        result = unit._handle_G2("G2 R30", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(mock.ANY, mock.ANY, mock.ANY, True)

        self.assertIsNone(result, "The result should be None")

    def test_handle_G2_counterClockwise(self):
        """Test the _handle_G2 method creates counter-clockwise arcs when passed a G3 command."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (0, 0)

        result = unit._handle_G2("G3 R30", "G3", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(mock.ANY, mock.ANY, mock.ANY, False)

        self.assertIsNone(result, "The result should be None")

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

    def test_handle_G2_negativeRadius(self):
        """Test the _handle_G2 method correctly parses a negative radius value."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (0, 0)

        result = unit._handle_G2("G2 R-12 X8 Y0", "G2", None)  # pylint: disable=protected-access

        unit.computeArcCenterOffsets.assert_called_with(8, 0, -12, True)

        self.assertIsNone(result, "The result should be None")

    def test_handle_G2_radiusTrumpsOffsets(self):
        """Test the _handle_G2 method to ensure offsets (I, J) are ignored if a radius is given."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        expectedResult = ["Command1"]
        mockState.processLinearMoves.return_value = expectedResult

        unit = GcodeHandlers(mockState, mockLogger)
        unit.computeArcCenterOffsets = mock.Mock()
        unit.computeArcCenterOffsets.return_value = (12, 13)
        unit.planArc = mock.Mock()
        unit.planArc.return_value = [0, 1, 2, 3]

        result = unit._handle_G2(  # pylint: disable=protected-access
            "G2 R20 I8 J9 X10 Y0",
            "G2",
            None
        )

        unit.computeArcCenterOffsets.assert_called_with(10, 0, 20, True)
        unit.planArc.assert_called_with(10, 0, 12, 13, True)

        self.assertEqual(result, expectedResult, "A list of one command should be returned")

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

    def test_handle_G10_ignoreP(self):
        """Test the _handle_G10 method when a P argument is present."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G10("G10 P", "G10", None)  # pylint: disable=protected-access

        self.assertIsNone(
            result,
            "None should be returned when a P argument is present with no value"
        )
        mockState.recordRetraction.assert_not_called()
        mockState.ignoreGcodeCommand.assert_not_called()

        result = unit._handle_G10("G10 S1 P0", "G10", None)  # pylint: disable=protected-access

        self.assertIsNone(
            result,
            "None should be returned when a P argument is present with a 0 value"
        )
        mockState.recordRetraction.assert_not_called()
        mockState.ignoreGcodeCommand.assert_not_called()

        result = unit._handle_G10("G10 S1 P10", "G10", None)  # pylint: disable=protected-access

        self.assertIsNone(
            result,
            "None should be returned when a P argument with a non-0 value is present"
        )
        mockState.recordRetraction.assert_not_called()
        mockState.ignoreGcodeCommand.assert_not_called()

        result = unit._handle_G10("G10 p", "G10", None)  # pylint: disable=protected-access

        self.assertIsNone(
            result,
            "None should be returned when a P argument is present (case-insensitivity)"
        )
        mockState.recordRetraction.assert_not_called()
        mockState.ignoreGcodeCommand.assert_not_called()

    def test_handle_G10_ignoreL(self):
        """Test the _handle_G10 method when an L argument is present."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G10("G10 L", "G10", None)  # pylint: disable=protected-access

        self.assertIsNone(
            result,
            "None should be returned when an L argument is present with no value"
        )
        mockState.recordRetraction.assert_not_called()
        mockState.ignoreGcodeCommand.assert_not_called()

        result = unit._handle_G10("G10 S1 L0", "G10", None)  # pylint: disable=protected-access

        self.assertIsNone(
            result,
            "None should be returned when an L argument is present with a 0 value"
        )
        mockState.recordRetraction.assert_not_called()
        mockState.ignoreGcodeCommand.assert_not_called()

        result = unit._handle_G10("G10 S1 L10", "G10", None)  # pylint: disable=protected-access

        self.assertIsNone(
            result,
            "None should be returned when an L argument with a non-0 value is present"
        )
        mockState.recordRetraction.assert_not_called()
        mockState.ignoreGcodeCommand.assert_not_called()

        result = unit._handle_G10("G10 l", "G10", None)  # pylint: disable=protected-access

        self.assertIsNone(
            result,
            "None should be returned when a L argument is present (case-insensitivity)"
        )
        mockState.recordRetraction.assert_not_called()
        mockState.ignoreGcodeCommand.assert_not_called()

    def test_handle_G10_recordRetraction_returns_None(self):
        """Test _handle_G10 when the call to recordRetraction returns None."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockState.recordRetraction.return_value = None
        mockState.ignoreGcodeCommand.return_value = "ignore"

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G10("G10", "G10", None)  # pylint: disable=protected-access

        mockState.recordRetraction.assert_called_with(
            RetractionState(firmwareRetract=True, originalCommand="G10"),
            None
        )
        mockState.ignoreGcodeCommand.assert_called()

        self.assertEqual(result, "ignore", "The result of ignoreGcodeCommand should be returned.")

    def test_handle_G10_recordRetraction_returns_value(self):
        """Test _handle_G10 when the call to recordRetraction returns something other than None."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockState.recordRetraction.return_value = "proceed"
        mockState.ignoreGcodeCommand.return_value = "ignore"

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G10("G10", "G10", None)  # pylint: disable=protected-access

        mockState.recordRetraction.assert_called_with(
            RetractionState(firmwareRetract=True, originalCommand="G10"),
            None
        )
        mockState.ignoreGcodeCommand.assert_not_called()

        self.assertEqual(result, "proceed", "The result of recordRetraction should be returned.")

    def test_handle_G11_recoverRetractionIfNeeded_returns_None(self):
        """Test _handle_G11 when the call to recoverRetractionIfNeeded returns None."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockState.recoverRetractionIfNeeded.return_value = None
        mockState.ignoreGcodeCommand.return_value = "ignore"

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G11("G11", "G11", None)  # pylint: disable=protected-access

        mockState.recoverRetractionIfNeeded.assert_called_with(None, "G11", True)
        mockState.ignoreGcodeCommand.assert_called()

        self.assertEqual(result, "ignore", "The result of ignoreGcodeCommand should be returned.")

    def test_handle_G11_recoverRetractionIfNeeded_returns_value(self):
        """Test _handle_G11 when recoverRetractionIfNeeded returns something other than None."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockState.recoverRetractionIfNeeded.return_value = "proceed"
        mockState.ignoreGcodeCommand.return_value = "ignore"

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G11("G11", "G11", None)  # pylint: disable=protected-access

        mockState.recoverRetractionIfNeeded.assert_called_with(None, "G11", True)
        mockState.ignoreGcodeCommand.assert_not_called()

        self.assertEqual(
            result, "proceed",
            "The result of recoverRetractionIfNeeded should be returned."
        )

    def test_handle_G20_noArgs(self):
        """Test _handle_G20 when no arguments are present."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G20("G20", "G20", None)  # pylint: disable=protected-access

        mockState.setUnitMultiplier.assert_called_with(INCH_TO_MM_FACTOR)
        self.assertIsNone(result, "The result should be None")

    def test_handle_G20_withArgs(self):
        """Test _handle_G20 when arguments are present is same as without."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G20("G20 S1", "G20", None)  # pylint: disable=protected-access

        mockState.setUnitMultiplier.assert_called_with(INCH_TO_MM_FACTOR)
        self.assertIsNone(result, "The result should be None")

    def test_handle_G21_noArgs(self):
        """Test _handle_G21 when no arguments are present."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G21("G21", "G21", None)  # pylint: disable=protected-access

        mockState.setUnitMultiplier.assert_called_with(1)
        self.assertIsNone(result, "The result should be None")

    def test_handle_G21_withArgs(self):
        """Test _handle_G21 when arguments are present is same as without."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G21("G21 S1", "G21", None)  # pylint: disable=protected-access

        mockState.setUnitMultiplier.assert_called_with(1)
        self.assertIsNone(result, "The result should be None")

    def test_handle_G28_noArgs(self):
        """Test _handle_G28 when no arguments are provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G28("G28", "G28", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHome.assert_called()
        mockState.position.Y_AXIS.setHome.assert_called()
        mockState.position.Z_AXIS.setHome.assert_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_G28_noXyzArgs(self):
        """Test _handle_G28 when arguments exist, but none of the X/Y/Z arguments are provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G28("G28 S1", "G28", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHome.assert_called()
        mockState.position.Y_AXIS.setHome.assert_called()
        mockState.position.Z_AXIS.setHome.assert_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_G28_argCaseInsensitive(self):
        """Test the _handle_G28 method to ensure arguments are not case-sensitive."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G28("G28 x y", "G0", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHome.assert_called()
        mockState.position.Y_AXIS.setHome.assert_called()
        mockState.position.Z_AXIS.setHome.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handle_G28_allXyzArgs(self):
        """Test _handle_G28 when all of the X/Y/Z arguments are provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G28("G28 X Y0 Z10", "G28", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHome.assert_called()
        mockState.position.Y_AXIS.setHome.assert_called()
        mockState.position.Z_AXIS.setHome.assert_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_G28_xAxis(self):
        """Test _handle_G28 when only the X argument is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G28("G28 X", "G28", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHome.assert_called()
        mockState.position.Y_AXIS.setHome.assert_not_called()
        mockState.position.Z_AXIS.setHome.assert_not_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_G28_yAxis(self):
        """Test _handle_G28 when only the Y argument is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G28("G28 Y", "G28", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHome.assert_not_called()
        mockState.position.Y_AXIS.setHome.assert_called()
        mockState.position.Z_AXIS.setHome.assert_not_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_G28_zAxis(self):
        """Test _handle_G28 when only the Z argument is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G28("G28 Z", "G28", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHome.assert_not_called()
        mockState.position.Y_AXIS.setHome.assert_not_called()
        mockState.position.Z_AXIS.setHome.assert_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_G90_noArgs(self):
        """Test _handle_G90 when no arguments are present."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G90("G90", "G90", None)  # pylint: disable=protected-access

        mockState.setAbsoluteMode.assert_called_with(True)
        self.assertIsNone(result, "The result should be None")

    def test_handle_G90_withArgs(self):
        """Test _handle_G90 when arguments are present is same as without."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G90("G90 S1", "G90", None)  # pylint: disable=protected-access

        mockState.setAbsoluteMode.assert_called_with(True)
        self.assertIsNone(result, "The result should be None")

    def test_handle_G91_noArgs(self):
        """Test _handle_G91 when no arguments are present."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G91("G91", "G91", None)  # pylint: disable=protected-access

        mockState.setAbsoluteMode.assert_called_with(False)
        self.assertIsNone(result, "The result should be None")

    def test_handle_G91_withArgs(self):
        """Test _handle_G91 when arguments are present is same as without."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G91("G91 S1", "G91", None)  # pylint: disable=protected-access

        mockState.setAbsoluteMode.assert_called_with(False)
        self.assertIsNone(result, "The result should be None")

    def test_handle_G92_noArgs(self):
        """Test _handle_G92 when no arguments are provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G92("G92", "G92", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Y_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Z_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.E_AXIS.setLogicalPosition.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handle_G92_noXyzeArgs(self):
        """Test _handle_G92 when arguments are provided, but none are X/Y/Z/E arguments."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G92("G92 S0", "G92", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Y_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Z_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.E_AXIS.setLogicalPosition.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handle_G92_nonFloatArgValue(self):
        """Test the _handle_G92 method when a non float value is provided for an argument."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G92("G92 X Y. Z- E+", "G92", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Y_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Z_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.E_AXIS.setLogicalPosition.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handle_G92_allXyzeArgs(self):
        """Test _handle_G92 when all of the X/Y/Z/E arguments are provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G92(  # pylint: disable=protected-access
            "G92 X1 Y2 Z3 E4",
            "G92",
            None
        )

        mockState.position.X_AXIS.setLogicalOffsetPosition.assert_called_with(1)
        mockState.position.Y_AXIS.setLogicalOffsetPosition.assert_called_with(2)
        mockState.position.Z_AXIS.setLogicalOffsetPosition.assert_called_with(3)
        mockState.position.E_AXIS.setLogicalPosition.assert_called_with(4)

        self.assertIsNone(result, "The result should be None")

    def test_handle_G92_xArg(self):
        """Test _handle_G92 when only the X argument is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G92("G92 X10", "G92", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setLogicalOffsetPosition.assert_called_with(10)
        mockState.position.Y_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Z_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.E_AXIS.setLogicalPosition.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handle_G92_yArg(self):
        """Test _handle_G92 when only the Y argument is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G92("G92 Y-10", "G92", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Y_AXIS.setLogicalOffsetPosition.assert_called_with(-10)
        mockState.position.Z_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.E_AXIS.setLogicalPosition.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handle_G92_zArg(self):
        """Test _handle_G92 when only the Z argument is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G92("G92 Z0", "G92", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Y_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Z_AXIS.setLogicalOffsetPosition.assert_called_with(0)
        mockState.position.E_AXIS.setLogicalPosition.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handle_G92_eArg(self):
        """Test _handle_G92 when only the E argument is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_G92("G92 E42", "G92", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Y_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.Z_AXIS.setLogicalOffsetPosition.assert_not_called()
        mockState.position.E_AXIS.setLogicalPosition.assert_called_with(42)

        self.assertIsNone(result, "The result should be None")

    def test_handle_M206_noArgs(self):
        """Test _handle_M206 when no arguments are provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_M206("M206", "M206", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHomeOffset.assert_not_called()
        mockState.position.Y_AXIS.setHomeOffset.assert_not_called()
        mockState.position.Z_AXIS.setHomeOffset.assert_not_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_M206_nonFloatArgValue(self):
        """Test the _handle_M206 method when a non float value is provided for an argument."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_M206(  # pylint: disable=protected-access
            "M206 X. Y-. Z",
            "M206",
            None
        )

        mockState.position.X_AXIS.setHomeOffset.assert_not_called()
        mockState.position.Y_AXIS.setHomeOffset.assert_not_called()
        mockState.position.Z_AXIS.setHomeOffset.assert_not_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_M206_noXyzArgs(self):
        """Test _handle_M206 when arguments are provided, but no X/Y/Z arguments."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_M206("M206 S0", "M206", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHomeOffset.assert_not_called()
        mockState.position.Y_AXIS.setHomeOffset.assert_not_called()
        mockState.position.Z_AXIS.setHomeOffset.assert_not_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_M206_allXyzArgs(self):
        """Test _handle_M206 when all of the X/Y/Z arguments are provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_M206(  # pylint: disable=protected-access
            "M206 X-1 Y0 Z1",
            "M206",
            None
        )

        mockState.position.X_AXIS.setHomeOffset.assert_called_with(-1)
        mockState.position.Y_AXIS.setHomeOffset.assert_called_with(0)
        mockState.position.Z_AXIS.setHomeOffset.assert_called_with(1)
        self.assertIsNone(result, "The result should be None")

    def test_handle_M206_xArg(self):
        """Test _handle_M206 when only the X argument is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_M206("M206 X12", "M206", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHomeOffset.assert_called_with(12)
        mockState.position.Y_AXIS.setHomeOffset.assert_not_called()
        mockState.position.Z_AXIS.setHomeOffset.assert_not_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_M206_yArg(self):
        """Test _handle_M206 when only the Y argument is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_M206("M206 Y21", "M206", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHomeOffset.assert_not_called()
        mockState.position.Y_AXIS.setHomeOffset.assert_called_with(21)
        mockState.position.Z_AXIS.setHomeOffset.assert_not_called()
        self.assertIsNone(result, "The result should be None")

    def test_handle_M206_zArg(self):
        """Test _handle_M206 when only the Z argument is provided."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit._handle_M206("M206 Z32", "M206", None)  # pylint: disable=protected-access

        mockState.position.X_AXIS.setHomeOffset.assert_not_called()
        mockState.position.Y_AXIS.setHomeOffset.assert_not_called()
        mockState.position.Z_AXIS.setHomeOffset.assert_called_with(32)
        self.assertIsNone(result, "The result should be None")
