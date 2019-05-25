# coding=utf-8
"""Unit tests for the GcodeParser class' parse method."""

from __future__ import absolute_import
from collections import OrderedDict

from octoprint_excluderegion.GcodeParser import GcodeParser

from .utils import TestCase


class GcodeParserParseTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for the GcodeParser class' parse method."""

    def test_initializer(self):
        """Test the class __init__ method."""
        expectedProperties = [
            "source",
            "offset",
            "length",
            "_lineNumber",
            "_type",
            "_code",
            "_gcode",
            "_subCode",
            "_parameters",
            "_parameterDict",
            "_checksum",
            "leadingWhitespace",
            "text",
            "_rawChecksum",
            "trailingWhitespace",
            "comment",
            "eol",
            "_commandString"
        ]

        unit = GcodeParser()

        self.assertParserProperties(
            unit=unit,
            source="",
            length=0
        )

        # pylint: disable=protected-access
        self.assertIsNone(unit._parameterDict, "The _parameterDict should be None")

        self.assertProperties(unit, expectedProperties)

    def assertParserProperties(  # pylint: disable=too-many-arguments, too-many-locals
            self,
            unit,
            source=None,
            offset=0,
            length=None,
            leadingWhitespace="",
            text="",
            trailingWhitespace="",
            lineNumber=None,
            type=None,  # pylint: disable=redefined-builtin
            code=None,
            subCode=None,
            parameters=None,
            parameterDict=None,
            rawChecksum=None,
            checksum=None,
            comment=None,
            eol=""
    ):
        """
        Test the parse method given a source string/offset and expected length and property values.

        Assertions will be made to verify the resulting values of the following properties, based
        on the parameter values provided:
            source, offset, length, leadingWhitespace, text, trailingWhitespace, lineNumber, type,
            code, gcode (based on the provided type and code), subCode, parameters, rawChecksum,
            checksum, comment, eol, and fullText (based on the provided string, offset and length).

        Parameters
        ----------
        source : string
            The source string to attempt to parse.
        offset : int
            The offset within the source to start parsing the line.
        length : int | None
            The expected length of the match.  If None, the entire source string will be expected
            to match.
        leadingWhitespace : string
            The expected parsed 'leadingWhitespace' value.
        text : string
            The expected parsed 'text' value.
        trailingWhitespace : string
            The expected parsed 'trailingWhitespace' value.
        lineNumber : int | None
            The expected parsed 'lineNumber' value.
        type : string | None
            The expected parsed 'type' value.
        code : int | None
            The expected parsed 'code' value.
        subCode : int | None
            The expected parsed 'subCode' value.
        parameters : string | None
            The expected parsed 'parameters' value.
        parameterDict : dict | None
            The expected parsed parameter labels and values.
        rawChecksum : string | None
            The expected parsed 'rawChecksum' value.
        checksum : int | None
            The expected parsed 'checksum' value.
        comment : string | None
            The expected parsed 'comment' value.
        eol : string
            The expected line ending value (CR, LF, CRLF, or empty string for none)

        Returns
        -------
        GcodeParser
            The GcodeParser instance created for the test, so additional assertions may be applied
            against its properties.
        """
        gcode = None if (type is None) else (type + str(code))

        useSource = unit.source if (source is None) else source

        if (length is None):
            length = len(useSource)

        fullText = useSource[offset:offset + length]

        self.assertEqual(unit.source, useSource, "The source should match the provided string")
        self.assertEqual(unit.offset, offset, "The offset should be " + repr(offset))
        self.assertEqual(unit.length, length, "The length should be " + repr(length))
        self.assertEqual(
            unit.leadingWhitespace, leadingWhitespace,
            "The leadingWhitespace should be " + repr(leadingWhitespace)
        )
        self.assertEqual(unit.text, text, "The text should be " + repr(text))
        self.assertEqual(
            unit.trailingWhitespace, trailingWhitespace,
            "The trailingWhitespace should be " + repr(trailingWhitespace)
        )
        self.assertEqual(
            unit.lineNumber, lineNumber,
            "The lineNumber should be " + repr(lineNumber)
        )
        self.assertEqual(unit.type, type, "The type should be " + repr(type))
        self.assertEqual(unit.code, code, "The code should be " + repr(code))
        self.assertEqual(unit.subCode, subCode, "The subCode should be " + repr(subCode))
        self.assertEqual(unit.gcode, gcode, "The gcode should be " + repr(gcode))
        self.assertEqual(
            unit.parameters, parameters,
            "The parameters should be " + repr(parameters)
        )
        self.assertEqual(
            unit.parameterDict, parameterDict,
            "The parameterDict should be " + repr(parameterDict)
        )
        self.assertEqual(
            unit.rawChecksum, rawChecksum,
            "The rawChecksum should be " + repr(rawChecksum)
        )
        self.assertEqual(unit.checksum, checksum, "The checksum should be " + repr(checksum))
        self.assertEqual(unit.comment, comment, "The comment should be " + repr(comment))
        self.assertEqual(unit.eol, eol, "The eol should be " + repr(eol))
        self.assertEqual(unit.fullText, fullText, "The fullText should be " + repr(fullText))

    def _test_parse_line(  # pylint: disable=too-many-arguments, too-many-locals
            self,
            source,
            offset=0,
            length=None,
            leadingWhitespace="",
            text="",
            trailingWhitespace="",
            lineNumber=None,
            type=None,  # pylint: disable=redefined-builtin
            code=None,
            subCode=None,
            parameters=None,
            parameterDict=None,
            rawChecksum=None,
            checksum=None,
            comment=None,
            eol=""
    ):
        """
        Test the parse method given a source string/offset and expected length and property values.

        Assertions will be made to verify the resulting values of the following properties, based
        on the parameter values provided:
            source, offset, length, leadingWhitespace, text, trailingWhitespace, lineNumber, type,
            code, gcode (based on the provided type and code), subCode, parameters, rawChecksum,
            checksum, comment, eol, and fullText (based on the provided string, offset and length).

        Parameters
        ----------
        source : string
            The source string to attempt to parse.
        offset : int
            The offset within the source to start parsing the line.
        length : int | None
            The expected length of the match.  If None, the entire source string will be expected
            to match.
        leadingWhitespace : string
            The expected parsed 'leadingWhitespace' value.
        text : string
            The expected parsed 'text' value.
        trailingWhitespace : string
            The expected parsed 'trailingWhitespace' value.
        lineNumber : int | None
            The expected parsed 'lineNumber' value.
        type : string | None
            The expected parsed 'type' value.
        code : int | None
            The expected parsed 'code' value.
        subCode : int | None
            The expected parsed 'subCode' value.
        parameters : string | None
            The expected parsed 'parameters' value.
        parameterDict : dict | None
            The expected parsed parameter labels and values.
        rawChecksum : string | None
            The expected parsed 'rawChecksum' value.
        checksum : int | None
            The expected parsed 'checksum' value.
        comment : string | None
            The expected parsed 'comment' value.
        eol : string
            The expected line ending value (CR, LF, CRLF, or empty string for none)

        Returns
        -------
        GcodeParser
            The GcodeParser instance created for the test, so additional assertions may be applied
            against its properties.
        """
        unit = GcodeParser()
        result = unit.parse(source, offset)
        self.assertParserProperties(
            unit=unit,
            source=source,
            offset=offset,
            length=length,
            leadingWhitespace=leadingWhitespace,
            text=text,
            trailingWhitespace=trailingWhitespace,
            lineNumber=lineNumber,
            type=type,
            code=code,
            subCode=subCode,
            parameters=parameters,
            parameterDict=parameterDict,
            rawChecksum=rawChecksum,
            checksum=checksum,
            comment=comment,
            eol=eol
        )
        self.assertEqual(result, unit, "The instance should be returned")

    def test_parse_None(self):
        """Test the parse method when no source string is provided for the initial call."""
        self._test_parse_line(None)

    def test_parse_empty_string(self):
        """Test parsing an empty input string."""
        self._test_parse_line(source="")

    def test_parse_blank_line_first(self):
        """Test parsing a blank line at the beginning of the input string."""
        self._test_parse_line(source="\nSecond line", length=1, eol="\n")

    def test_parse_blank_line_mid(self):
        """Test parsing a blank line in the middle of the input string."""
        self._test_parse_line(source="First\n\nLast", offset=6, length=1, eol="\n")

    def test_parse_blank_line_last(self):
        """Test parsing a blank line at the end of the input string."""
        self._test_parse_line(source="First\n", offset=6, length=0, eol="")

    def test_parse_only_whitespace(self):
        """Test parsing a line containing only whitespace."""
        self._test_parse_line(source="      ", leadingWhitespace="      ")

    def test_parse_only_comment(self):
        """Test parsing a line containing only a comment."""
        self._test_parse_line(
            source="; This is a comment ",
            comment="; This is a comment "
        )

    def test_parse_leading_whitespace_and_comment(self):
        """Test parsing a line containing whitespace and a comment."""
        self._test_parse_line(
            source="    ; This is a comment ",
            comment="; This is a comment ",
            leadingWhitespace="    "
        )

    def test_parse_eol_following_comment(self):
        """Test parsing a line containing a comment terminated in an eol."""
        def _test_eol_following_comment(eol):
            """Test parsing a line containing a comment terminated in an eol."""
            self._test_parse_line(
                source="; This is a comment " + eol,
                comment="; This is a comment ",
                eol=eol
            )

        _test_eol_following_comment("\n")
        _test_eol_following_comment("\r")
        _test_eol_following_comment("\r\n")

    def test_parse_eol_following_checksum(self):
        """Test parsing a line containing a checksum terminated in an eol."""
        def _test_eol_following_checksum(eol):
            """Test parsing a line containing a checksum terminated in an eol."""
            self._test_parse_line(
                source="G28*10" + eol,
                text="G28",
                type="G",
                code=28,
                rawChecksum="*10",
                checksum=10,
                eol=eol
            )

        _test_eol_following_checksum("\n")
        _test_eol_following_checksum("\r")
        _test_eol_following_checksum("\r\n")

    def test_parse_eol_following_parameters(self):
        """Test parsing a line containing parameters terminated in an eol."""
        def _test_eol_following_parameters(eol):
            """Test parsing a line containing parameters terminated in an eol."""
            self._test_parse_line(
                source="G28 X Y Z" + eol,
                text="G28 X Y Z",
                type="G",
                code=28,
                parameters="X Y Z",
                parameterDict=OrderedDict([
                    ("X", None),
                    ("Y", None),
                    ("Z", None),
                    ("", "X Y Z")
                ]),
                eol=eol
            )

        _test_eol_following_parameters("\n")
        _test_eol_following_parameters("\r")
        _test_eol_following_parameters("\r\n")

    def test_parse_eol_following_gcode(self):
        """Test parsing a line containing a gcode without parameters terminated in an eol."""
        def _test_eol_following_gcode(eol):
            """Test parsing a line containing a gcode without parameters terminated in an eol."""
            self._test_parse_line(
                source="G28" + eol,
                text="G28",
                type="G",
                code=28,
                eol=eol
            )

        _test_eol_following_gcode("\n")
        _test_eol_following_gcode("\r")
        _test_eol_following_gcode("\r\n")

    def test_parse_T(self):
        """Test parsing a Gcode tool selection command."""
        self._test_parse_line(
            source="T0",
            text="T0",
            type="T",
            code=0
        )

    def test_parse_T_with_lineNumber_and_checksum(self):
        """Test parsing a Gcode tool selection command with a line number and checksum."""
        self._test_parse_line(
            source="N1T0*27",
            text="N1T0",
            lineNumber=1,
            type="T",
            code=0,
            rawChecksum="*27",
            checksum=27
        )

    def test_parse_T_with_parameters(self):
        """Test parsing a tool selection command with parameters."""
        self._test_parse_line(
            source="T0P10",
            text="T0P10",
            type="T",
            code=0,
            parameters="P10",
            parameterDict=OrderedDict([("P", 10)])
        )

    def test_parse_T_with_parameters_and_comment(self):
        """Test parsing a tool selection command with parameters and a comment."""
        self._test_parse_line(
            source="T0P10;Comment",
            text="T0P10",
            type="T",
            code=0,
            parameters="P10",
            parameterDict=OrderedDict([("P", 10)]),
            comment=";Comment"
        )

    def test_parse_T_with_parameters_and_checksum(self):
        """Test parsing a tool selection command with parameters and a checksum."""
        self._test_parse_line(
            source="T0P10*123",
            text="T0P10",
            type="T",
            code=0,
            parameters="P10",
            parameterDict=OrderedDict([("P", 10)]),
            rawChecksum="*123",
            checksum=123
        )

    def test_parse_T_with_checksum_and_comment(self):
        """Test parsing a tool selection command with a checksum and comment."""
        self._test_parse_line(
            source="T0*123;Comment",
            text="T0",
            type="T",
            code=0,
            rawChecksum="*123",
            checksum=123,
            comment=";Comment"
        )

    def test_parse_T_all_with_whitespace(self):
        """Test parsing a tool selection command with all components."""
        self._test_parse_line(
            source="  N1  T0  P10  Q11  *123  ;  Comment  \n",
            leadingWhitespace="  ",
            text="N1  T0  P10  Q11  ",
            trailingWhitespace="  ",
            lineNumber=1,
            type="T",
            code=0,
            parameters="P10  Q11",
            parameterDict=OrderedDict([
                ("P", 10),
                ("Q", 11)
            ]),
            rawChecksum="*123",
            checksum=123,
            comment=";  Comment  ",
            eol="\n"
        )

    def test_parse_T_case_insensitive(self):
        """Test parsing a tool selection command with lower-case inputs."""
        self._test_parse_line(
            source="  n1  t0  p10  q11  *123  ;  Comment  \n",
            leadingWhitespace="  ",
            text="n1  t0  p10  q11  ",
            trailingWhitespace="  ",
            lineNumber=1,
            type="T",
            code=0,
            parameters="p10  q11",
            parameterDict=OrderedDict([
                ("P", 10),
                ("Q", 11)
            ]),
            rawChecksum="*123",
            checksum=123,
            comment=";  Comment  ",
            eol="\n"
        )

    def test_parse_T_normalization(self):
        """Test T command normalization of lineNumber, code and checksum."""
        self._test_parse_line(
            source="N0305T01*0034",
            text="N0305T01",
            lineNumber=305,
            type="T",
            code=1,
            rawChecksum="*0034",
            checksum=34
        )

    def test_parse_G(self):
        """Test parsing a Gcode general command."""
        self._test_parse_line(
            source="G28",
            text="G28",
            type="G",
            code=28
        )

    def test_parse_G_with_lineNumber_and_checksum(self):
        """Test parsing a Gcode general command with a line number and checksum."""
        self._test_parse_line(
            source="N2G28*31",
            text="N2G28",
            lineNumber=2,
            type="G",
            code=28,
            rawChecksum="*31",
            checksum=31
        )

    def test_parse_G_with_subCode_and_parameters(self):
        """Test parsing a Gcode general command with a subCode and parameters."""
        self._test_parse_line(
            source="G32.2F10X20",
            text="G32.2F10X20",
            type="G",
            code=32,
            subCode=2,
            parameters="F10X20",
            parameterDict=OrderedDict([
                ("F", 10),
                ("X", 20)
            ])
        )

    def test_parse_G_with_parameters(self):
        """Test parsing a Gcode general command with parameters."""
        self._test_parse_line(
            source="G28XYZ",
            text="G28XYZ",
            type="G",
            code=28,
            parameters="XYZ",
            parameterDict=OrderedDict([
                ("X", None),
                ("Y", None),
                ("Z", None),
                ("", "XYZ")
            ])
        )

    def test_parse_G_with_parameters_and_comment(self):
        """Test parsing a Gcode general command with parameters and a comment."""
        self._test_parse_line(
            source="G28X;Comment",
            text="G28X",
            type="G",
            code=28,
            parameters="X",
            parameterDict=OrderedDict([
                ("X", None),
                ("", "X")
            ]),
            comment=";Comment"
        )

    def test_parse_G_with_parameters_and_checksum(self):
        """Test parsing a Gcode general command with parameters and a checksum."""
        self._test_parse_line(
            source="G28XY*123",
            text="G28XY",
            type="G",
            code=28,
            parameters="XY",
            parameterDict=OrderedDict([
                ("X", None),
                ("Y", None),
                ("", "XY")
            ]),
            rawChecksum="*123",
            checksum=123
        )

    def test_parse_G_with_checksum_and_comment(self):
        """Test parsing a Gcode general command with a checksum and comment."""
        self._test_parse_line(
            source="G28*123;Comment",
            text="G28",
            type="G",
            code=28,
            rawChecksum="*123",
            checksum=123,
            comment=";Comment"
        )

    def test_parse_G_all_with_whitespace(self):
        """Test parsing a Gcode general command with all components."""
        self._test_parse_line(
            source="  N1  G28  X  YZ *123  ;  Comment  \n",
            leadingWhitespace="  ",
            text="N1  G28  X  YZ ",
            trailingWhitespace="  ",
            lineNumber=1,
            type="G",
            code=28,
            parameters="X  YZ",
            parameterDict=OrderedDict([
                ("X", None),
                ("Y", None),
                ("Z", None),
                ("", "X  YZ")
            ]),
            rawChecksum="*123",
            checksum=123,
            comment=";  Comment  ",
            eol="\n"
        )

    def test_parse_G_case_insensitive(self):
        """Test parsing a Gcode general command with lower case inputs."""
        self._test_parse_line(
            source="  n1  g28  x  yZ *123  ;  Comment  \n",
            lineNumber=1,
            leadingWhitespace="  ",
            text="n1  g28  x  yZ ",
            trailingWhitespace="  ",
            type="G",
            code=28,
            parameters="x  yZ",
            parameterDict=OrderedDict([
                ("X", None),
                ("Y", None),
                ("Z", None),
                ("", "x  yZ")
            ]),
            rawChecksum="*123",
            checksum=123,
            comment=";  Comment  ",
            eol="\n"
        )

    def test_parse_G_normalization(self):
        """Test G command normalization of lineNumber, code and checksum."""
        self._test_parse_line(
            source="N0305G01*0034",
            text="N0305G01",
            lineNumber=305,
            type="G",
            code=1,
            rawChecksum="*0034",
            checksum=34
        )

    def test_parse_M(self):
        """Test parsing a Gcode miscellaneous command."""
        self._test_parse_line(
            source="M17",
            text="M17",
            type="M",
            code=17
        )

    def test_parse_M_with_lineNumber_and_checksum(self):
        """Test parsing a Gcode miscellaneous command with a line number and checksum."""
        self._test_parse_line(
            source="N123M17*35",
            text="N123M17",
            lineNumber=123,
            type="M",
            code=17,
            rawChecksum="*35",
            checksum=35
        )

    def test_parse_M_with_subCode_and_parameters(self):
        """Test parsing a Gcode miscellaneous command with a subCode and parameters."""
        self._test_parse_line(
            source="M42.1A1B2",
            text="M42.1A1B2",
            type="M",
            code=42,
            subCode=1,
            parameters="A1B2",
            parameterDict=OrderedDict([
                ("A", 1),
                ("B", 2)
            ])
        )

    def test_parse_M_with_parameters(self):
        """Test parsing a Gcode miscellaneous command with parameters."""
        self._test_parse_line(
            source="M109S185",
            text="M109S185",
            type="M",
            code=109,
            parameters="S185",
            parameterDict=OrderedDict([("S", 185)])
        )

    def test_parse_M_with_parameters_and_comment(self):
        """Test parsing a Gcode miscellaneous command with parameters and a comment."""
        self._test_parse_line(
            source="M109S185;Comment",
            text="M109S185",
            type="M",
            code=109,
            parameters="S185",
            parameterDict=OrderedDict([("S", 185)]),
            comment=";Comment"
        )

    def test_parse_M_with_parameters_and_checksum(self):
        """Test parsing a Gcode miscellaneous command with parameters and a checksum."""
        self._test_parse_line(
            source="M109S185*123",
            text="M109S185",
            type="M",
            code=109,
            parameters="S185",
            parameterDict=OrderedDict([("S", 185)]),
            rawChecksum="*123",
            checksum=123
        )

    def test_parse_M_with_checksum_and_comment(self):
        """Test parsing a Gcode miscellaneous command with a checksum and comment."""
        self._test_parse_line(
            source="M17*123;Comment",
            text="M17",
            type="M",
            code=17,
            rawChecksum="*123",
            checksum=123,
            comment=";Comment"
        )

    def test_parse_M_all_with_whitespace(self):
        """Test parsing a Gcode miscellaneous command with all components."""
        self._test_parse_line(
            source="  N1  M145  S3  B60  H210  F75  *123  ;  Comment  \n",
            leadingWhitespace="  ",
            text="N1  M145  S3  B60  H210  F75  ",
            trailingWhitespace="  ",
            lineNumber=1,
            type="M",
            code=145,
            parameters="S3  B60  H210  F75",
            parameterDict=OrderedDict([
                ("S", 3),
                ("B", 60),
                ("H", 210),
                ("F", 75)
            ]),
            rawChecksum="*123",
            checksum=123,
            comment=";  Comment  ",
            eol="\n"
        )

    def test_parse_M_case_insensitive(self):
        """Test parsing a Gcode miscellaneous command with lower case inputs."""
        self._test_parse_line(
            source="  n1  m145  s3  b60  h210  f75  *123  ;  Comment  \n",
            leadingWhitespace="  ",
            text="n1  m145  s3  b60  h210  f75  ",
            trailingWhitespace="  ",
            lineNumber=1,
            type="M",
            code=145,
            parameters="s3  b60  h210  f75",
            parameterDict=OrderedDict([
                ("S", 3),
                ("B", 60),
                ("H", 210),
                ("F", 75)
            ]),
            rawChecksum="*123",
            checksum=123,
            comment=";  Comment  ",
            eol="\n"
        )

    def test_parse_M_normalization(self):
        """Test M command normalization of lineNumber, code and checksum."""
        self._test_parse_line(
            source="N0305M01*0034",
            text="N0305M01",
            lineNumber=305,
            type="M",
            code=1,
            rawChecksum="*0034",
            checksum=34
        )

    def test_parse_non_gcode_line(self):
        """Test parsing a line that is not valid Gcode."""
        # Lines starting with TtGgMm are not valid if a number doesn't follow
        self._test_parse_line(
            source="This is not valid gcode",
            text="This is not valid gcode"
        )
        self._test_parse_line(
            source="G: Nor is this",
            text="G: Nor is this"
        )

        self._test_parse_line(
            source="g> or this",
            text="g> or this"
        )
        self._test_parse_line(
            source="M) Neither is this",
            text="M) Neither is this"
        )
        self._test_parse_line(
            source="m) or this",
            text="m) or this"
        )

        # Lines with line numbers or checksums are not valid without a Gcode
        self._test_parse_line(
            source="N2",
            text="N2"
        )
        self._test_parse_line(
            source="N2*10",
            text="N2*10"
        )
        self._test_parse_line(
            source="*10",
            text="*10"
        )

    def test_parse_at_command(self):
        """Test parsing a line containing an OctoPrint @-command."""
        self._test_parse_line(
            source="@ExcludeRegion enable\r\nSecond line",
            length=23,
            text="@ExcludeRegion enable",
            eol="\r\n"
        )

    def test_parse_paramterDict_uses_last_value(self):
        """Test that parameterDict returns the last value specified for a parameter."""
        self._test_parse_line(
            source="G1 X1 Y2 y3 Y4 y5",
            text="G1 X1 Y2 y3 Y4 y5",
            type="G",
            code=1,
            parameters="X1 Y2 y3 Y4 y5",
            parameterDict=OrderedDict([
                ("X", 1),
                ("Y", 5)
            ])
        )

    def test_parse_offset(self):
        """Test parse when provided a specific offset to start at."""
        self._test_parse_line(
            source=(
                "G28 ;Home\n" +
                "G1 X1 Y2\n" +
                "G20"
            ),
            offset=10,
            length=9,
            text="G1 X1 Y2",
            type="G",
            code=1,
            parameters="X1 Y2",
            parameterDict=OrderedDict([
                ("X", 1),
                ("Y", 2)
            ]),
            eol="\n"
        )

    def test_parse_multiple_lines_first(self):
        """Test parse to parse the first of multiple lines."""
        unit = GcodeParser()
        source = (
            "G28 ;Home\n" +
            "G1 X1 Y2\n" +
            "G20"
        )

        result = unit.parse(source)

        self.assertEqual(result, unit, "The instance should be returned")
        self.assertParserProperties(
            unit=unit,
            source=source,
            offset=0,
            length=10,
            text="G28 ",
            type="G",
            code=28,
            comment=";Home",
            eol="\n"
        )

    def test_parse_multiple_lines_mid(self):
        """Test parse to parse a line in the middle of multiple lines."""
        unit = GcodeParser()
        source = (
            "G28 ;Home\n" +
            "G1 X1 Y2\n" +
            "G20"
        )
        unit.parse(source)  # Read the first line

        result = unit.parse()

        self.assertEqual(result, unit, "The instance should be returned")
        self.assertParserProperties(
            unit=unit,
            source=source,
            offset=10,
            length=9,
            text="G1 X1 Y2",
            type="G",
            code=1,
            parameters="X1 Y2",
            parameterDict=OrderedDict([
                ("X", 1),
                ("Y", 2)
            ]),
            eol="\n"
        )

    def test_parse_multiple_lines_last(self):
        """Test parse to parse the last of multiple lines."""
        unit = GcodeParser()
        source = (
            "G28 ;Home\n" +
            "G1 X1 Y2\n" +
            "G20"
        )
        unit.parse(source)  # Read the first line
        unit.parse()        # Read the second line

        result = unit.parse()

        self.assertEqual(result, unit, "The instance should be returned")
        self.assertParserProperties(
            unit=unit,
            source=source,
            offset=19,
            length=3,
            text="G20",
            type="G",
            code=20
        )
