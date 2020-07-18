# coding=utf-8
"""Unit tests for the GcodeParser class."""

from __future__ import absolute_import
from collections import OrderedDict
import mock

from octoprint_excluderegion.GcodeParser import GcodeParser

from .utils import TestCase


class GcodeParserTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for the GcodeParser class."""

    def test_parseLines_None(self):
        """Test parseLines parses the current source when passed None."""
        unit = GcodeParser()
        unit.source = "command 1"

        result = []
        for item in unit.parseLines(None):
            result.append(item.fullText)

        self.assertEqual(result, ["command 1"], "The expected commands should be parsed")

    def test_parseLines_emptyString(self):
        """Test parseLines when passed an empty string."""
        unit = GcodeParser()

        result = []
        for item in unit.parseLines(""):
            result.append(item.fullText)

        self.assertEqual(result, [], "No lines should be parsed")

    def test_parseLines_blankLine(self):
        """Test parseLines when passed a single line ending."""
        unit = GcodeParser()

        result = []
        for item in unit.parseLines("\n"):
            result.append(item.fullText)

        self.assertEqual(result, ["\n"], "The expected lines should be parsed")

    def test_parseLines_singleLine(self):
        """Test parseLines when passed a string containing a single line."""
        unit = GcodeParser()

        result = []
        for item in unit.parseLines("command 1"):
            result.append(item.fullText)

        self.assertEqual(result, ["command 1"], "The expected lines should be parsed")

    def test_parseLines_multipleLines(self):
        """Test parseLines when passed a string containing multiple lines."""
        unit = GcodeParser()

        result = []
        for item in unit.parseLines("command 1\rcommand 2\rcommand 3"):
            result.append(item.fullText)

        self.assertEqual(
            result, ["command 1\r", "command 2\r", "command 3"],
            "The expected lines should be parsed"
        )

    def test_parseLines_offset(self):
        """Test parseLines when passed an offset value."""
        unit = GcodeParser()

        result = []
        for item in unit.parseLines("command 1\rcommand 2\rcommand 3", 10):
            result.append(item.fullText)

        self.assertEqual(
            result, ["command 2\r", "command 3"],
            "The expected lines should be parsed"
        )

    def test_lineNumber_setter_notNone(self):
        """Test the lineNumber setter assigning a non-None value."""
        unit = GcodeParser()
        unit.parse("G0")
        self.assertIsNone(unit.lineNumber, "The lineNumber should be None.")

        unit.lineNumber = 1234

        self.assertEqual(unit.lineNumber, 1234, "The lineNumber should be 1234.")
        self.assertEqual(unit.gcode, "G0", "The gcode should be 'G0'.")
        self.assertEqual(unit.commandString, "N1234 G0", "The commandString should be 'N1234 G0'.")

    def test_lineNumber_setter_none(self):
        """Test the lineNumber setter assigning None."""
        unit = GcodeParser()
        unit.parse("N1234 G0")
        self.assertEqual(unit.lineNumber, 1234, "The lineNumber should be 1234.")

        unit.lineNumber = None

        self.assertIsNone(unit.lineNumber, "The lineNumber should be None.")
        self.assertEqual(unit.gcode, "G0", "The gcode should be 'G0'.")
        self.assertEqual(unit.commandString, "G0", "The commandString should be 'G0'.")

    def test_gcode_setter_noSubCode(self):
        """Test the gcode setter when no subCode is supplied."""
        unit = GcodeParser()

        unit.gcode = "G0"

        self.assertEqual(unit.type, "G", "The type should be 'G'.")
        self.assertEqual(unit.code, 0, "The code should be 0.")
        self.assertIsNone(unit.subCode, "The subCode should be None.")
        self.assertEqual(unit.gcode, "G0", "The gcode should be 'G0'.")
        self.assertEqual(unit.commandString, "G0", "The commandString should be 'G0'.")

        unit.gcode = "M17"

        self.assertEqual(unit.type, "M", "The type should be 'M'.")
        self.assertEqual(unit.code, 17, "The code should be 17.")
        self.assertIsNone(unit.subCode, "The subCode should be None.")
        self.assertEqual(unit.gcode, "M17", "The gcode should be 'M17'.")
        self.assertEqual(unit.commandString, "M17", "The commandString should be 'M17'.")

        unit.gcode = "T2"

        self.assertEqual(unit.type, "T", "The type should be 'T'.")
        self.assertEqual(unit.code, 2, "The code should be 2.")
        self.assertEqual(unit.gcode, "T2", "The gcode should be 'T2'.")
        self.assertIsNone(unit.subCode, "The subCode should be None.")
        self.assertEqual(unit.commandString, "T2", "The commandString should be 'T2'.")

    def test_gcode_setter_subCode(self):
        """Test the gcode setter when supplied with a subcode."""
        unit = GcodeParser()

        unit.gcode = "G1.2"

        self.assertEqual(unit.type, "G", "The type should be 'G'.")
        self.assertEqual(unit.code, 1, "The code should be 1.")
        self.assertEqual(unit.subCode, 2, "The subCode should be 2.")
        self.assertEqual(unit.gcode, "G1", "The gcode should be 'G1'.")
        self.assertEqual(unit.commandString, "G1.2", "The commandString should be 'G1.2'.")

        unit.gcode = "M17.1"

        self.assertEqual(unit.type, "M", "The type should be 'M'.")
        self.assertEqual(unit.code, 17, "The code should be 17.")
        self.assertEqual(unit.subCode, 1, "The subCode should be 1.")
        self.assertEqual(unit.gcode, "M17", "The gcode should be 'M17'.")
        self.assertEqual(unit.commandString, "M17.1", "The commandString should be 'M17.1'.")

        # T codes don't support subCodes
        with self.assertRaises(ValueError):
            unit.gcode = "T2.3"

        # No side-effects from exception
        self.assertEqual(unit.type, "M", "The type should be 'M'.")
        self.assertEqual(unit.code, 17, "The code should be 17.")
        self.assertEqual(unit.subCode, 1, "The subCode should be 1.")

    def test_gcode_setter_whitespace(self):
        """Test the gcode setter when the supplied value has leading/trailing whitespace."""
        unit = GcodeParser()

        unit.gcode = "  G  1  "

        self.assertEqual(unit.type, "G", "The type should be 'G'.")
        self.assertEqual(unit.code, 1, "The code should be 1.")
        self.assertIsNone(unit.subCode, "The subCode should be None.")

        unit.gcode = "  M  17.1  "

        self.assertEqual(unit.type, "M", "The type should be 'M'.")
        self.assertEqual(unit.code, 17, "The code should be 17.")
        self.assertEqual(unit.subCode, 1, "The subCode should be 1.")

        unit.gcode = "  T  2  "

        self.assertEqual(unit.type, "T", "The type should be 'T'.")
        self.assertEqual(unit.code, 2, "The code should be 2.")
        self.assertEqual(unit.gcode, "T2", "The gcode should be 'T2'.")

    def test_parameters_setter_valid(self):
        """Test the parameters setter when valid parameters are provided."""
        unit = GcodeParser()
        unit.parse("G1")
        self.assertEqual(unit.commandString, "G1", "The commandString should be 'G1'.")

        unit.parameters = "X10 Y3.2 Foo"

        self.assertEqual(
            unit.parameters, "X10 Y3.2 Foo",
            "The parameters should be the expected value."
        )
        self.assertEqual(
            unit.commandString, "G1 X10 Y3.2 Foo",
            "The commandString should be the expected value."
        )
        self.assertEqual(
            unit.parameterDict,
            OrderedDict([
                ("X", 10),
                ("Y", 3.2),
                ("F", None),
                ("O", None),
                ("", "Foo")
            ]),
            "The parameterDict should be the expected value."
        )

    def test_parameters_setter_valid_escapes(self):
        """Test the parameters setter when valid parameters with escaped chars are provided."""
        unit = GcodeParser()
        unit.parse("G1")
        self.assertEqual(unit.commandString, "G1", "The commandString should be 'G1'.")

        unit.parameters = r"X10 \\ \;Not a comment"

        self.assertEqual(
            unit.parameters, r"X10 \\ \;Not a comment",
            "The parameters should be the expected value."
        )
        self.assertEqual(
            unit.commandString, r"G1 X10 \\ \;Not a comment",
            "The commandString should be the expected value."
        )
        self.assertEqual(
            unit.parameterDict,
            OrderedDict([
                ("X", 10),
                ("N", None),
                ("O", None),
                ("T", None),
                ("A", None),
                ("C", None),
                ("M", None),
                ("E", None),
                ("", r"\\ \;Not a comment")
            ]),
            "The parameterDict should be the expected value."
        )

    def test_parameters_setter_valid_whitespace(self):
        """Test parameters setter when valid parameters are provided with extraneous whitespace."""
        unit = GcodeParser()
        unit.parse("G1")
        self.assertEqual(unit.commandString, "G1", "The commandString should be 'G1'.")

        unit.parameters = "   X  10 Y3.2 Foo  "

        self.assertEqual(
            unit.parameters, "X  10 Y3.2 Foo",
            "The parameters should be the expected value."
        )
        self.assertEqual(
            unit.commandString, "G1 X  10 Y3.2 Foo",
            "The commandString should be the expected value."
        )
        self.assertEqual(
            unit.parameterDict,
            OrderedDict([
                ("X", 10),
                ("Y", 3.2),
                ("F", None),
                ("O", None),
                ("", "Foo")
            ]),
            "The parameterDict should be the expected value."
        )

    def test_parameters_setter_invalid_checksum(self):
        """Test parameters setter when parameters provided include a checksum-like value."""
        unit = GcodeParser()
        unit.parse("G1")
        self.assertEqual(unit.commandString, "G1", "The commandString should be 'G1'.")

        with self.assertRaises(ValueError):
            unit.parameters = "X10 Y3.2 Foo *12"

    def test_parameters_setter_invalid_comment(self):
        """Test parameters setter when parameters provided include a comment-like value."""
        unit = GcodeParser()
        unit.parse("G1")
        self.assertEqual(unit.commandString, "G1", "The commandString should be 'G1'.")

        with self.assertRaises(ValueError):
            unit.parameters = "X10 Y3.2 Foo ;Invalid"

    def test_parameterItems_no_string_given(self):
        """Test that parameterItems uses the parameters property when no string is given."""
        unit = GcodeParser()
        unit.parse("G1 A1BC2")

        self.assertEqual(unit.parameters, "A1BC2", "The parameters should be 'A1BC2'.")

        result = [item for item in unit.parameterItems()]

        self.assertEqual(
            result, [("A", 1), ("B", None), ("C", 2), ("", "BC2")],
            "The expected result should be generated."
        )

    def test_parameterItems_custom_string(self):
        """Test that parameterItems parses the given string when one is given."""
        unit = GcodeParser()

        self.assertIsNone(unit.parameters, "The parameters should be None.")

        result = [item for item in unit.parameterItems("A1BC2")]

        self.assertEqual(
            result, [("A", 1), ("B", None), ("C", 2), ("", "BC2")],
            "The expected result should be generated."
        )

    def test_parameterItems_nonAlphaFirstChar(self):
        """Test parameterItems when the first character is non-alphabetic."""
        unit = GcodeParser()

        self.assertIsNone(unit.parameters, "The parameters should be None.")

        result = [item for item in unit.parameterItems("12 A2")]

        self.assertEqual(
            result, [("A", 2), ("", "12 A2")],
            "The expected result should be generated."
        )

    def test_parameterItems_none(self):
        """Test parameterItems when the parameters attribute is None."""
        unit = GcodeParser()

        self.assertIsNone(unit.parameters, "The parameters should be None.")

        result = [item for item in unit.parameterItems()]

        self.assertEqual(result, [], "An empty list should be generated.")

    def test_parameterItems_empty_string(self):
        """Test parameterItems when provided an empty string."""
        unit = GcodeParser()

        self.assertIsNone(unit.parameters, "The parameters should be None.")

        result = [item for item in unit.parameterItems("")]

        self.assertEqual(result, [], "An empty list should be generated.")

    def test_parameterItems_whitespace_params(self):
        """Test that parameterItems permits whitespace between parameters."""
        unit = GcodeParser()
        self.assertIsNone(unit.parameters, "The parameters should be None.")

        result = [item for item in unit.parameterItems("A1 B C2")]

        self.assertEqual(
            result, [("A", 1), ("B", None), ("C", 2), ("", "B C2")],
            "The expected result should be generated."
        )

    def test_parameterItems_whitespace_labels_and_values(self):
        """Test that parameterItems permits whitespace between labels and values."""
        unit = GcodeParser()
        self.assertIsNone(unit.parameters, "The parameters should be None.")

        result = [item for item in unit.parameterItems("A  1 B C  2")]

        self.assertEqual(
            result, [("A", 1), ("B", None), ("C", 2), ("", "B C  2")],
            "The expected result should be generated."
        )

    def test_parameterDict_getter_parametersNone(self):
        """Test the parameterDict getter when the parameters property is None."""
        unit = GcodeParser()
        unit._parameters = None  # pylint: disable=protected-access

        with mock.patch.object(unit, 'parameterItems') as mockParameterItems:
            result = unit.parameterDict

            mockParameterItems.assert_not_called()
            self.assertIsNone(result, "The result should be None")

    def test_parameterDict_getter_notCached(self):
        """Test the parameterDict getter when the result is not cached."""
        unit = GcodeParser()
        unit._parameters = "A1 B2"  # pylint: disable=protected-access

        with mock.patch.object(unit, 'parameterItems') as mockParameterItems:
            mockParameterItems.return_value = [("A", 1), ("B", 2)]

            result = unit.parameterDict

            mockParameterItems.assert_called()
            self.assertEqual(
                result,
                OrderedDict([
                    ("A", 1),
                    ("B", 2)
                ]),
                "The expected result should be returned"
            )

    def test_parameterDict_getter_cached(self):
        """Test the parameterDict getter when the result is already cached."""
        expected = OrderedDict([
            ("A", 1),
            ("B", 2)
        ])

        unit = GcodeParser()
        unit._parameters = "A1 B2"      # pylint: disable=protected-access
        unit._parameterDict = expected  # pylint: disable=protected-access

        with mock.patch.object(unit, 'parameterItems') as mockParameterItems:
            result = unit.parameterDict

            mockParameterItems.assert_not_called()
            self.assertEqual(
                result, expected,
                "The expected result should be returned"
            )

    def test_parameterDict_setter_None(self):
        """Test the parameterDict setter when passed None."""
        unit = GcodeParser()
        unit.parse("G28 X")
        self.assertEqual(
            unit.parameterDict, OrderedDict([("X", None), ("", "X")]),
            "The parameterDict should be the expected value"
        )

        unit.parameterDict = None

        self.assertIsNone(unit.parameters, "The parameters should be None")
        self.assertIsNone(unit.parameterDict, "The parameterDict should be None")

    def test_parameterDict_setter_empty(self):
        """Test the parameterDict setter when passed an empty dict."""
        unit = GcodeParser()
        unit.parse("G28 X")
        self.assertEqual(
            unit.parameterDict, OrderedDict([("X", None), ("", "X")]),
            "The parameterDict should be the expected value"
        )

        unit.parameterDict = {}

        self.assertIsNone(unit.parameters, "The parameters should be None")
        self.assertIsNone(unit.parameterDict, "The parameterDict should be None")

    def test_parameterDict_setter_emptyStr_emptyStr(self):
        """Test the parameterDict setter when passed {"": ""}."""
        unit = GcodeParser()
        unit.parse("G28 X")
        self.assertEqual(
            unit.parameterDict, OrderedDict([("X", None), ("", "X")]),
            "The parameterDict should be the expected value"
        )

        unit.parameterDict = {"": ""}

        self.assertIsNone(unit.parameters, "The parameters should be None")
        self.assertIsNone(unit.parameterDict, "The parameterDict should be None")

    def test_parameterDict_setter_emptyStr_none(self):
        """Test the parameterDict setter when passed {"": None}."""
        unit = GcodeParser()
        unit.parse("G28 X")
        self.assertEqual(
            unit.parameterDict, OrderedDict([("X", None), ("", "X")]),
            "The parameterDict should be the expected value"
        )

        unit.parameterDict = {"": None}

        self.assertIsNone(unit.parameters, "The parameters should be None")
        self.assertIsNone(unit.parameterDict, "The parameterDict should be None")

    def test_parameterDict_setter_falsyLabel_noValue(self):
        """Test the parameterDict setter when passed {"0": ""}."""
        unit = GcodeParser()
        unit.parse("G28 X")
        self.assertEqual(
            unit.parameterDict, OrderedDict([("X", None), ("", "X")]),
            "The parameterDict should be the expected value"
        )

        unit.parameterDict = {"0": ""}

        self.assertEqual(unit.parameters, "0", "The parameters should be '0'")
        self.assertEqual(
            unit.parameterDict,
            OrderedDict([("", "0")]),
            "The parameterDict should be the expected value"
        )

    def test_parameterDict_setter_noLabel_falsyValue(self):
        """Test the parameterDict setter when passed {"": "0"}."""
        unit = GcodeParser()
        unit.parse("G28 X")
        self.assertEqual(
            unit.parameterDict, OrderedDict([("X", None), ("", "X")]),
            "The parameterDict should be the expected value"
        )

        unit.parameterDict = {"": "0"}

        self.assertEqual(unit.parameters, "0", "The parameters should be '0'")
        self.assertEqual(
            unit.parameterDict,
            OrderedDict([("", "0")]),
            "The parameterDict should be the expected value"
        )

    def test_parameterDict_setter_label_emptyStr(self):
        """Test the parameterDict setter when passed a label with a value of empty string."""
        unit = GcodeParser()
        unit.parse("G28 X")
        self.assertEqual(
            unit.parameterDict, OrderedDict([("X", None), ("", "X")]),
            "The parameterDict should be the expected value"
        )

        unit.parameterDict = {"A": ""}

        self.assertEqual(unit.parameters, "A", "The parameters should be 'A'")
        self.assertEqual(
            unit.parameterDict,
            OrderedDict([("A", None), ("", "A")]),
            "The parameterDict should be the expected value"
        )

    def test_parameterDict_setter_label_none(self):
        """Test the parameterDict setter when passed a label with a value of None."""
        unit = GcodeParser()
        unit.parse("G28 X")
        self.assertEqual(
            unit.parameterDict, OrderedDict([("X", None), ("", "X")]),
            "The parameterDict should be the expected value"
        )

        unit.parameterDict = {"A": None}

        self.assertEqual(unit.parameters, "A", "The parameters should be 'A'")
        self.assertEqual(
            unit.parameterDict,
            OrderedDict([("A", None), ("", "A")]),
            "The parameterDict should be the expected value"
        )

    def test_parameterDict_setter_label_value(self):
        """Test the parameterDict setter when passed a label and non empty value."""
        unit = GcodeParser()
        unit.parse("G28 X")
        self.assertEqual(
            unit.parameterDict, OrderedDict([("X", None), ("", "X")]),
            "The parameterDict should be the expected value"
        )

        unit.parameterDict = {"A": 12}

        self.assertEqual(unit.parameters, "A12", "The parameters should be 'A12'")
        self.assertEqual(
            unit.parameterDict,
            OrderedDict([("A", 12)]),
            "The parameterDict should be the expected value"
        )

    def test_validate_noLineNumber_noChecksum(self):  # pylint: disable=no-self-use
        """Test validate when no lineNumber or checksum value is present."""
        unit = GcodeParser()
        unit.lineNumber = None
        unit._checksum = None  # pylint: disable=protected-access

        unit.validate()

    def test_validate_lineNumber_noChecksum(self):
        """Test validate when a lineNumber is present without a checksum value."""
        unit = GcodeParser()
        unit.lineNumber = 10
        unit._checksum = None  # pylint: disable=protected-access

        with self.assertRaises(ValueError):
            unit.validate()

    def test_validate_noLineNumber_checksum(self):
        """Test validate when a no lineNumber is present but a checksum value is."""
        unit = GcodeParser()
        unit._checksum = 10  # pylint: disable=protected-access
        unit.lineNumber = None

        with self.assertRaises(ValueError):
            unit.validate()

    def test_validate_checksum_mismatch(self):
        """Test validate when a lineNumber and checksum are present, but the checksum is invalid."""
        unit = GcodeParser()
        unit.text = "G28"  # Checksum should be 77
        unit.lineNumber = 10
        unit._checksum = 20  # pylint: disable=protected-access

        with self.assertRaises(ValueError):
            unit.validate()

    def test_validate_checksum_ok(self):  # pylint: disable=no-self-use
        """Test validate when a lineNumber and checksum are present, and the checksum is valid."""
        unit = GcodeParser()
        unit.text = "G28"
        unit.lineNumber = 10
        unit._checksum = 77  # pylint: disable=protected-access

        unit.validate()

    def test_computeChecksum(self):
        """Test computeChecksum."""
        unit = GcodeParser()

        self.assertEqual(
            unit.computeChecksum(""), 0,
            "computeChecksum should return 0 for an empty string"
        )

        self.assertEqual(
            unit.computeChecksum("A"), 65,
            "computeChecksum should return 65 for 'A'"
        )

        self.assertEqual(
            unit.computeChecksum("ABC"), 64,
            "computeChecksum should return 64 for 'ABC'"
        )

        self.assertEqual(
            unit.computeChecksum("foo bar"), 55,
            "computeChecksum should return 55 for 'foo bar'"
        )

    def test_stringify_notGcodeText(self):
        """Test stringify when the text is not a valid Gcode line."""
        unit = GcodeParser()
        unit.parse("not gcode")

        result = unit.stringify()

        self.assertEqual(result, "not gcode", "The result should be the original text")

    def test_stringify_defaults(self):
        """Test stringify when no parameters are supplied."""
        unit = GcodeParser()

        unit.parse("   N0123   G028  X  *107   ; Comment   \r\n")

        result = unit.stringify()

        self.assertEqual(
            result, "   N123 G28 X *75 ; Comment   \r\n",
            "The result should be the normalized text"
        )

    def test_stringify_leadingWhitespaceTrue(self):
        """Test stringify when the includeLeadingWhitespace parameter is True."""
        unit = GcodeParser()
        unit.parse("   G28")

        result = unit.stringify(includeLeadingWhitespace=True)

        self.assertEqual(result, "   G28", "The result should be the original text")

    def test_stringify_leadingWhitespaceFalse(self):
        """Test stringify when the includeLeadingWhitespace parameter is False."""
        unit = GcodeParser()
        unit.parse("   G28")

        result = unit.stringify(includeLeadingWhitespace=False)

        self.assertEqual(result, "G28", "The result should have the leading whitespace removed")

    def test_stringify_lineNumberTrue_checksumNone(self):
        """Test stringify when includeLineNumber=True and includeChecksum=None."""
        unit = GcodeParser()
        unit.parse("N123   G28")

        result = unit.stringify(includeLineNumber=True, includeChecksum=None)

        self.assertEqual(
            result, "N123 G28 *51",
            "The expected result should be returned"
        )

    def test_stringify_lineNumberTrue_checksumTrue(self):
        """Test stringify when includeLineNumber=True and includeChecksum=True."""
        unit = GcodeParser()
        unit.parse("N123   G28")

        result = unit.stringify(includeLineNumber=True, includeChecksum=True)

        self.assertEqual(
            result, "N123 G28 *51",
            "The expected result should be returned"
        )

    def test_stringify_lineNumberTrue_checksumFalse(self):
        """Test stringify when includeLineNumber=True and includeChecksum=False."""
        unit = GcodeParser()
        unit.parse("N123   G28")

        result = unit.stringify(includeLineNumber=True, includeChecksum=False)

        self.assertEqual(
            result, "N123 G28",
            "The expected result should be returned"
        )

    def test_stringify_lineNumberFalse_checksumNone(self):
        """Test stringify when includeLineNumber=True and includeChecksum=None."""
        unit = GcodeParser()
        unit.parse("N123   G28")

        result = unit.stringify(includeLineNumber=False, includeChecksum=None)

        self.assertEqual(
            result, "G28",
            "The expected result should be returned"
        )

    def test_stringify_lineNumberFalse_checksumTrue(self):
        """Test stringify when includeLineNumber=False and includeChecksum=True."""
        unit = GcodeParser()
        unit.parse("N123   G28")

        result = unit.stringify(includeLineNumber=False, includeChecksum=True)

        self.assertEqual(
            result, "G28 *109",
            "The expected result should be returned"
        )

    def test_stringify_lineNumberFalse_checksumFalse(self):
        """Test stringify when includeLineNumber=False and includeChecksum=False."""
        unit = GcodeParser()
        unit.parse("N123   G28")

        result = unit.stringify(includeLineNumber=False, includeChecksum=False)

        self.assertEqual(
            result, "G28",
            "The expected result should be returned"
        )

    def test_stringify_subCodeNone(self):
        """Test stringify when the subCode is None."""
        unit = GcodeParser()

        unit.parse("G 28")
        self.assertIsNone(unit.subCode, "The subCode property should be None")

        result = unit.stringify()

        self.assertEqual(
            result, "G28",
            "The expected result should be returned"
        )

    def test_stringify_subCodeNotNone(self):
        """Test stringify when the subCode is not None."""
        unit = GcodeParser()

        unit.parse("G 28.1")
        self.assertIsNotNone(unit.subCode, "The subCode property should not be None")

        result = unit.stringify()

        self.assertEqual(
            result, "G28.1",
            "The expected result should be returned"
        )

    def test_stringify_parametersNone(self):
        """Test stringify when the parameters property is None."""
        unit = GcodeParser()

        unit.parse("G 28")
        self.assertIsNone(unit.parameters, "The parameters property should be None")

        result = unit.stringify()

        self.assertEqual(
            result, "G28",
            "The expected result should be returned"
        )

    def test_stringify_parametersNotNone(self):
        """Test stringify when the parameters property is not None."""
        unit = GcodeParser()

        unit.parse("G 28 X  Y")
        self.assertIsNotNone(unit.parameters, "The parameters property should not be None")

        result = unit.stringify()

        self.assertEqual(
            result, "G28 X  Y",
            "The expected result should be returned"
        )

    def test_stringify_includeCommentTrue_commentNone(self):
        """Test stringify when includeComment=True and there is no comment."""
        unit = GcodeParser()

        unit.parse("G 28")
        self.assertIsNone(unit.comment, "The comment property should be None")

        result = unit.stringify(includeComment=True)

        self.assertEqual(
            result, "G28",
            "The expected result should be returned"
        )

    def test_stringify_includeCommentTrue_withComment(self):
        """Test stringify when includeComment=True and there is a comment."""
        unit = GcodeParser()

        unit.parse("G 28   ; My comment")
        self.assertIsNotNone(unit.comment, "The comment property should not be None")

        result = unit.stringify(includeComment=True)

        self.assertEqual(
            result, "G28 ; My comment",
            "The expected result should be returned"
        )

    def test_stringify_includeCommentFalse_commentNone(self):
        """Test stringify when includeComment=False and there is no comment."""
        unit = GcodeParser()

        unit.parse("G 28")
        self.assertIsNone(unit.comment, "The comment property should be None")

        result = unit.stringify(includeComment=False)

        self.assertEqual(
            result, "G28",
            "The expected result should be returned"
        )

    def test_stringify_includeCommentFalse_withComment(self):
        """Test stringify when includeComment=False and there is a comment."""
        unit = GcodeParser()

        unit.parse("G 28   ; My comment")
        self.assertIsNotNone(unit.comment, "The comment property should not be None")

        result = unit.stringify(includeComment=False)

        self.assertEqual(
            result, "G28",
            "The expected result should be returned"
        )

    def test_stringify_includeEolTrue(self):
        """Test stringify when includeEol=True."""
        unit = GcodeParser()

        unit.parse("G 28\n")
        self.assertEqual(unit.eol, "\n", "The eol should be '\\n'")

        result = unit.stringify(includeEol=True)

        self.assertEqual(
            result, "G28\n",
            "The expected result should be returned"
        )

    def test_stringify_includeEolFalse(self):
        """Test stringify when includeEol=False."""
        unit = GcodeParser()

        unit.parse("G 28\n")
        self.assertEqual(unit.eol, "\n", "The eol should be '\\n'")

        result = unit.stringify(includeEol=False)

        self.assertEqual(
            result, "G28",
            "The expected result should be returned"
        )

    def test_commandString_cached(self):
        """Test the commandString property when a value is already cached."""
        unit = GcodeParser()
        unit._commandString = "foo"  # pylint: disable=protected-access

        with mock.patch.object(unit, 'stringify') as mockStringify:
            result = unit.commandString

            mockStringify.assert_not_called()
            self.assertEqual(result, "foo", "The result should be the cached value.")

    def test_commandString_notCached(self):
        """Test the commandString property when no value is cached."""
        unit = GcodeParser()
        unit._commandString = None  # pylint: disable=protected-access

        with mock.patch.object(unit, 'stringify') as mockStringify:
            mockStringify.return_value = "foo bar"

            result = unit.commandString

            mockStringify.assert_called_with(
                includeChecksum=False,
                includeComment=False,
                includeEol=False
            )
            self.assertEqual(result, "foo bar", "The result of stringify should be returned.")

    def test_str(self):
        """Test the __str__ magic method."""
        unit = GcodeParser()

        with mock.patch.object(unit, 'stringify') as mockStringify:
            mockStringify.return_value = "expectedResult"

            result = str(unit)

            mockStringify.assert_called_with()
            self.assertEqual(
                result, "expectedResult",
                "The result of stringify should be returned."
            )

    def test_buildCommand_no_kwargs(self):
        """Test buildCommand when passed a GCode command and no kwargs."""
        unit = GcodeParser()

        result = unit.buildCommand("G0")

        self.assertEqual(result, "G0", "The returned command should be 'G0'")

    def test_buildCommand_one_kwarg(self):
        """Test buildCommand when passed a GCode command and one kwargs."""
        unit = GcodeParser()

        result = unit.buildCommand("G0", X=10)

        self.assertEqual(result, "G0 X10", "The returned command should be 'G0 X10'")

    def test_buildCommand_two_kwargs(self):
        """Test buildCommand when passed a GCode command and two kwargs."""
        unit = GcodeParser()

        result = unit.buildCommand("G0", X=10, Y=20)

        if sys.version_info[0] < 3:
            self.assertRegexpMatches(result, "^G0 ", "The returned command should start with 'G0 '")
            # Due to kwargs, order of arguments is not guaranteed, and also is not required
            self.assertRegexpMatches(result, " X10( |$)", "The returned command should contain ' X10'")
            self.assertRegexpMatches(result, " Y20( |$)", "The returned command should contain ' Y20'")
        else:
            self.AssertRegEx(result, "^G0 ", "The returned command should start with 'G0 '")
            # Due to kwargs, order of arguments is not guaranteed, and also is not required
            self.AssertRegEx(result, " X10( |$)", "The returned command should contain ' X10'")
            self.AssertRegEx(result, " Y20( |$)", "The returned command should contain ' Y20'")

    def test_buildCommand_argValueNone(self):
        """Test buildCommand when passed a GCode command and a kwarg set to None."""
        unit = GcodeParser()

        result = unit.buildCommand("G0", X=None)

        self.assertEqual(result, "G0 X", "The returned command should be 'G0 X'")

    def test_buildCommand_argValueEmptyString(self):
        """Test buildCommand when passed a GCode command and a kwarg set to empty string."""
        unit = GcodeParser()

        result = unit.buildCommand("G0", X="")

        self.assertEqual(result, "G0 X", "The returned command should be 'G0 X'")
