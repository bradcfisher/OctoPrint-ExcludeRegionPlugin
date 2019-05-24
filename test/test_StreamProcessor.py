# coding=utf-8
"""Unit tests for the StreamProcessor class."""

from __future__ import absolute_import

import mock

from octoprint_excluderegion.StreamProcessor import StreamProcessor, StreamProcessorComm
from octoprint_excluderegion.GcodeHandlers import GcodeHandlers

from .utils import TestCase


class StreamProcessorTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for the StreamProcessor class."""

    def test_initializer(self):
        """Test the class __init__ method."""
        mockInputStream = mock.Mock(name="input_stream")
        mockInputStream.readable.return_value = True
        mockGcodeHandlers = mock.Mock(name="gcodeHandlers")

        unit = StreamProcessor(mockInputStream, mockGcodeHandlers)

        self.assertIsNotNone(
            unit.input_stream,
            "The input_stream should not be none."
        )
        self.assertIsInstance(
            unit.gcodeHandlers, GcodeHandlers,
            "The gcodeHandlers should be a GcodeHandlers instance."
        )
        self.assertNotEqual(
            unit.gcodeHandlers, mockGcodeHandlers,
            "The gcodeHandlers should NOT match the instance provided."
        )
        self.assertNotEqual(
            unit.gcodeHandlers.state, mockGcodeHandlers.state,
            "The gcodeHandlers state should NOT match the state of the original gcodeHandlers."
        )
        self.assertIsInstance(
            unit.commInstance, StreamProcessorComm,
            "The commInstance should be a StreamProcessorComm instance."
        )
        self.assertIsNone(unit._eol, "The _eol should be None")  # pylint: disable=protected-access

    @staticmethod
    def _createUnit():
        """Create a new StreamProcessor instance for executing tests against."""
        mockInputStream = mock.Mock(name="input_stream")
        mockInputStream.readable.return_value = True
        mockGcodeHandlers = mock.Mock(name="gcodeHandlers")

        unit = StreamProcessor(mockInputStream, mockGcodeHandlers)

        return unit

    def test_eol_getter_unknown(self):
        """Test the eol getter when an eol is not yet known."""
        unit = self._createUnit()

        eol = unit.eol

        self.assertEqual(
            unit._eol, "\n",  # pylint: disable=protected-access
            "The eol getter should update the _eol property if no eol value is known."
        )
        self.assertEqual(eol, "\n", "The eol getter should return '\\n' by default.")

    def test_eol_getter_setter_notNone(self):
        """Test the eol setter and getter when an eol value is passed to the setter."""
        unit = self._createUnit()

        unit.eol = "\r"

        self.assertEqual(
            unit._eol, "\r",  # pylint: disable=protected-access
            "The eol setter should update the _eol property."
        )

        eol = unit.eol

        self.assertEqual(
            unit._eol, "\r",  # pylint: disable=protected-access
            "The eol getter should not update the _eol property if an eol value is already known."
        )
        self.assertEqual(eol, "\r", "The eol getter should return the known eol value.")

    def test_eol_getter_setter_none(self):
        """Test the eol setter and getter when None is passed to the setter."""
        unit = self._createUnit()
        unit.eol = "\r"

        unit.eol = None

        self.assertIsNone(
            unit._eol,  # pylint: disable=protected-access
            "The eol setter should update the _eol property."
        )

        eol = unit.eol

        self.assertEqual(
            unit._eol, "\n",  # pylint: disable=protected-access
            "The eol getter should update the _eol property if no eol value is known."
        )
        self.assertEqual(eol, "\n", "The eol getter should return '\\n' by default.")

    def test_process_line_gcode(self):
        """Test process_line when a gcode command is encountered."""
        unit = self._createUnit()

        with mock.patch.object(unit.gcodeHandlers, "gcodeParser") as mockParser:
            mockParser.parse.return_value = mockParser
            mockParser.type = "G"
            mockParser.code = 28
            mockParser.gcode = "G28"
            mockParser.text = "G28"
            mockParser.eol = ""

            with mock.patch.multiple(
                unit,
                _handleGcode=mock.DEFAULT,
                _handleAtCommand=mock.DEFAULT
            ) as mocks:
                mocks['_handleGcode'].return_value = "expectedResult"

                result = unit.process_line("G28")

                mockParser.parse.assert_called_with("G28")
                mocks['_handleGcode'].assert_called_with(mockParser)
                mocks['_handleAtCommand'].assert_not_called()

                self.assertEqual(
                    result, "expectedResult",
                    "The expected result should be returned."
                )
                self.assertIsNone(
                    unit._eol,  # pylint: disable=protected-access
                    "The _eol should be None when no eol is parsed."
                )

    def test_process_line_atCommand(self):
        """Test process_line when an @-command is encountered."""
        unit = self._createUnit()

        with mock.patch.object(unit.gcodeHandlers, "gcodeParser") as mockParser:
            mockParser.parse.return_value = mockParser
            mockParser.type = None
            mockParser.code = None
            mockParser.gcode = None
            mockParser.text = "@command"
            mockParser.eol = ""

            with mock.patch.multiple(
                unit,
                _handleGcode=mock.DEFAULT,
                _handleAtCommand=mock.DEFAULT
            ) as mocks:
                mocks['_handleAtCommand'].return_value = "expectedResult"

                result = unit.process_line("@command")

                mockParser.parse.assert_called_with("@command")
                mocks['_handleGcode'].assert_not_called()
                mocks['_handleAtCommand'].assert_called_with(mockParser)

                self.assertEqual(
                    result, "expectedResult",
                    "The expected result should be returned."
                )
                self.assertIsNone(
                    unit._eol,  # pylint: disable=protected-access
                    "The _eol should be None when no eol is parsed."
                )

    def test_process_line_notGcodeOrAtCommand(self):
        """Test process_line when the line is not a recognizable gcode or @-command."""
        unit = self._createUnit()

        with mock.patch.object(unit.gcodeHandlers, "gcodeParser") as mockParser:
            mockParser.parse.return_value = mockParser
            mockParser.type = None
            mockParser.code = None
            mockParser.gcode = None
            mockParser.text = "Something\r"
            mockParser.eol = "\r"

            with mock.patch.multiple(
                unit,
                _handleGcode=mock.DEFAULT,
                _handleAtCommand=mock.DEFAULT
            ) as mocks:
                result = unit.process_line("Something\r")

                mockParser.parse.assert_called_with("Something\r")
                mocks['_handleGcode'].assert_not_called()
                mocks['_handleAtCommand'].assert_not_called()

                self.assertEqual(
                    result, "Something\r",
                    "The line passed in should be returned."
                )
                self.assertEqual(
                    unit._eol,  # pylint: disable=protected-access
                    "\r",
                    "The _eol should match the parsed eol."
                )

    def test_handleGcode_handlerReturnsNone(self):
        """Test _handleGcode when the handler returns None."""
        unit = self._createUnit()

        with mock.patch.object(unit.gcodeHandlers, "handleGcode") as mockHandleGcode:
            mockHandleGcode.return_value = None
            mockParser = mock.Mock()
            mockParser.stringify.return_value = "stringified"
            mockParser.gcode = "G28"
            mockParser.subCode = None
            mockParser.source = "expectedResult"

            result = unit._handleGcode(mockParser)  # pylint: disable=protected-access

            mockHandleGcode.assert_called_with("stringified", "G28", None)
            self.assertEqual(result, "expectedResult", "The expected result should be returned.")

    def test_handleGcode_handlerReturnsString(self):
        """Test _handleGcode when the handler returns a string."""
        unit = self._createUnit()

        with mock.patch.object(unit.gcodeHandlers, "handleGcode") as mockHandleGcode:
            mockHandleGcode.return_value = "string"
            mockParser = mock.Mock()
            mockParser.stringify.return_value = "stringified"
            mockParser.gcode = "G28"
            mockParser.subCode = None

            result = unit._handleGcode(mockParser)  # pylint: disable=protected-access

            mockHandleGcode.assert_called_with("stringified", "G28", None)
            self.assertEqual(result, "string\n", "The expected result should be returned.")

    def test_handleGcode_handlerReturns1Tuple(self):
        """Test _handleGcode when the handler returns a 1-tuple."""
        unit = self._createUnit()

        with mock.patch.object(unit.gcodeHandlers, "handleGcode") as mockHandleGcode:
            mockHandleGcode.return_value = ("string",)
            mockParser = mock.Mock()
            mockParser.stringify.return_value = "stringified"
            mockParser.gcode = "G28"
            mockParser.subCode = None

            result = unit._handleGcode(mockParser)  # pylint: disable=protected-access

            mockHandleGcode.assert_called_with("stringified", "G28", None)
            self.assertEqual(result, "string\n", "The expected result should be returned.")

    def test_handleGcode_handlerReturns2Tuple(self):
        """Test _handleGcode when the handler returns a 2-tuple."""
        unit = self._createUnit()

        with mock.patch.object(unit.gcodeHandlers, "handleGcode") as mockHandleGcode:
            mockHandleGcode.return_value = ("string", {})
            mockParser = mock.Mock()
            mockParser.stringify.return_value = "stringified"
            mockParser.gcode = "G28"
            mockParser.subCode = None

            result = unit._handleGcode(mockParser)  # pylint: disable=protected-access

            mockHandleGcode.assert_called_with("stringified", "G28", None)
            self.assertEqual(result, "string\n", "The expected result should be returned.")

    def test_handleGcode_handlerReturns3Tuple(self):
        """Test _handleGcode when the handler returns a 3-tuple."""
        unit = self._createUnit()

        with mock.patch.object(unit.gcodeHandlers, "handleGcode") as mockHandleGcode:
            mockHandleGcode.return_value = ("string", {}, "extra")
            mockParser = mock.Mock()
            mockParser.stringify.return_value = "stringified"
            mockParser.gcode = "G28"
            mockParser.subCode = None

            result = unit._handleGcode(mockParser)  # pylint: disable=protected-access

            mockHandleGcode.assert_called_with("stringified", "G28", None)
            self.assertEqual(result, "string\n", "The expected result should be returned.")

    def test_handleGcode_handlerReturnsNonEmptySequence(self):
        """Test _handleGcode when the handler returns a non-empty sequence."""
        unit = self._createUnit()

        with mock.patch.object(unit.gcodeHandlers, "handleGcode") as mockHandleGcode:
            mockHandleGcode.return_value = [
                "command1",
                None,
                ("command2",),
                ("command3", {})
            ]
            mockParser = mock.Mock()
            mockParser.stringify.return_value = "stringified"
            mockParser.gcode = "G28"
            mockParser.subCode = None

            result = unit._handleGcode(mockParser)  # pylint: disable=protected-access

            mockHandleGcode.assert_called_with("stringified", "G28", None)
            self.assertEqual(
                result, "command1\ncommand2\ncommand3\n",
                "The expected result should be returned."
            )

    def test_handleGcode_handlerReturnsEmptySequence(self):
        """Test _handleGcode when the handler returns an empty sequence."""
        unit = self._createUnit()

        with mock.patch.object(unit.gcodeHandlers, "handleGcode") as mockHandleGcode:
            mockHandleGcode.return_value = []
            mockParser = mock.Mock()
            mockParser.stringify.return_value = "stringified"
            mockParser.gcode = "G28"
            mockParser.subCode = None

            result = unit._handleGcode(mockParser)  # pylint: disable=protected-access

            mockHandleGcode.assert_called_with("stringified", "G28", None)
            self.assertIsNone(result, "The result should be None.")

    def test_splitAtCommand_emptyCommand(self):
        """Test _splitAtCommand when only "@" is provided."""
        unit = self._createUnit()

        result = unit._splitAtCommand("@")  # pylint: disable=protected-access

        self.assertEqual(
            result, ("", ""),
            "The expected result should be returned."
        )

    def test_splitAtCommand_noParams(self):
        """Test _splitAtCommand when no parameters are provided."""
        unit = self._createUnit()

        result = unit._splitAtCommand("@command")  # pylint: disable=protected-access

        self.assertEqual(
            result, ("command", ""),
            "The expected result should be returned."
        )

    def test_splitAtCommand_params(self):
        """Test _splitAtCommand when parameters are provided."""
        unit = self._createUnit()

        result = unit._splitAtCommand("@command param1 param2")  # pylint: disable=protected-access

        self.assertEqual(
            result, ("command", "param1 param2"),
            "The expected result should be returned."
        )

    def test_splitAtCommand_whitespace_noParams(self):
        """Test _splitAtCommand with only a command and leading and trailing whitespace."""
        unit = self._createUnit()

        result = unit._splitAtCommand("  @command  ")  # pylint: disable=protected-access

        self.assertEqual(
            result, ("command", ""),
            "The expected result should be returned."
        )

    def test_splitAtCommand_whitespace_params(self):
        """Test _splitAtCommand with a command and parameters + leading and trailing whitespace."""
        unit = self._createUnit()

        result = unit._splitAtCommand(  # pylint: disable=protected-access
            "  @command  param1  param2  "
        )

        # Trailing whitespace will not be removed from the parameters, but should have already been
        # removed by the time _splitAtCommand is called anyway.
        self.assertEqual(
            result, ("command", "param1  param2  "),
            "The expected result should be returned."
        )

    def test_handleAtCommand_notHandled(self):
        """Test _handleAtCommand when the command is not processed by the gcodeHandlers."""
        unit = self._createUnit()

        mockParser = mock.Mock()
        mockParser.text = "parserLine"
        mockParser.source = "parserSource"

        with mock.patch.object(unit.gcodeHandlers, "handleAtCommand") as mockHandleAtCommand:
            with mock.patch.multiple(
                unit,
                _splitAtCommand=mock.DEFAULT,
                commInstance=mock.DEFAULT
            ) as mocks:
                mockHandleAtCommand.return_value = False

                mocks["_splitAtCommand"].return_value = ("command", "parameters")

                result = unit._handleAtCommand(mockParser)  # pylint: disable=protected-access

                mocks["commInstance"].reset.assert_called_with()
                mocks["_splitAtCommand"].assert_called_with("parserLine")
                mockHandleAtCommand.assert_called_with(
                    mocks["commInstance"],
                    "command",
                    "parameters"
                )

                self.assertEqual(
                    result,
                    "parserSource",
                    "The original source line should be returned."
                )

    def test_handleAtCommand_noBufferedCommands(self):
        """Test _handleAtCommand if gcodeHandlers handles it but no commands are buffered."""
        unit = self._createUnit()

        mockParser = mock.Mock()
        mockParser.text = "parserLine"
        mockParser.source = "parserSource"

        with mock.patch.object(unit.gcodeHandlers, "handleAtCommand") as mockHandleAtCommand:
            with mock.patch.multiple(
                unit,
                _splitAtCommand=mock.DEFAULT,
                commInstance=mock.DEFAULT
            ) as mocks:
                mockHandleAtCommand.return_value = True

                mocks["_splitAtCommand"].return_value = ("command", "parameters")
                mocks["commInstance"].bufferedCommands = []

                result = unit._handleAtCommand(mockParser)  # pylint: disable=protected-access

                mocks["commInstance"].reset.assert_called_with()
                mocks["_splitAtCommand"].assert_called_with("parserLine")
                mockHandleAtCommand.assert_called_with(
                    mocks["commInstance"],
                    "command",
                    "parameters"
                )

                self.assertIsNone(result, "The result should be None.")

    def test_handleAtCommand_oneBufferedCommand(self):
        """Test _handleAtCommand if gcodeHandlers handles it and a single command is buffered."""
        unit = self._createUnit()

        mockParser = mock.Mock()
        mockParser.text = "parserLine"
        mockParser.source = "parserSource"

        with mock.patch.object(unit.gcodeHandlers, "handleAtCommand") as mockHandleAtCommand:
            with mock.patch.multiple(
                unit,
                _splitAtCommand=mock.DEFAULT,
                commInstance=mock.DEFAULT
            ) as mocks:
                unit.eol = "\r"
                mockHandleAtCommand.return_value = True

                mocks["_splitAtCommand"].return_value = ("command", "parameters")
                mocks["commInstance"].bufferedCommands = ["G28"]

                result = unit._handleAtCommand(mockParser)  # pylint: disable=protected-access

                mocks["commInstance"].reset.assert_called_with()
                mocks["_splitAtCommand"].assert_called_with("parserLine")
                mockHandleAtCommand.assert_called_with(
                    mocks["commInstance"],
                    "command",
                    "parameters"
                )

                self.assertEqual(
                    result, "G28\r",
                    "The result should be 'G28\\r'."
                )

    def test_handleAtCommand_multipleBufferedCommands(self):
        """Test _handleAtCommand if gcodeHandlers handles it and multiple commands are buffered."""
        unit = self._createUnit()

        mockParser = mock.Mock()
        mockParser.text = "parserLine"
        mockParser.source = "parserSource"

        with mock.patch.object(unit.gcodeHandlers, "handleAtCommand") as mockHandleAtCommand:
            with mock.patch.multiple(
                unit,
                _splitAtCommand=mock.DEFAULT,
                commInstance=mock.DEFAULT
            ) as mocks:
                unit.eol = "\r"
                mockHandleAtCommand.return_value = True

                mocks["_splitAtCommand"].return_value = ("command", "parameters")
                mocks["commInstance"].bufferedCommands = ["G28", "M117 Hi"]

                result = unit._handleAtCommand(mockParser)  # pylint: disable=protected-access

                mocks["commInstance"].reset.assert_called_with()
                mocks["_splitAtCommand"].assert_called_with("parserLine")
                mockHandleAtCommand.assert_called_with(
                    mocks["commInstance"],
                    "command",
                    "parameters"
                )

                self.assertEqual(
                    result, "G28\rM117 Hi\r",
                    "The result should be 'G28\\rM117 Hi\\r'."
                )
