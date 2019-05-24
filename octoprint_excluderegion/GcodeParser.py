# coding=utf-8
"""Class for parsing lines of Gcode from a string."""

import re
from collections import OrderedDict

from .CommonMixin import CommonMixin

# TODO: parsing options?
#   - specify whitespace chars
#   - disable subcode support
#   - disable case-insensitivity
#   - disable '\' escapes
# TODO: specify special rules per gcode?
#   e.g. Marlin doesn't interpret/split parameter string for M23, M28, M30, M117, (kinda M118),
#        and M928.  It always just assigns the whole thing to string_arg

# Marlin "bugs"?
#   - If you include an asterisk on a line, Marlin only tries to validate any subsequent checksum
#     if there's also a line number (N) (e.g. "G0 X1*323" will silently ignore the bad checksum)
#   - Asterisks can technically be escaped with a backslash when read from serial, but the escape
#     char is only applied during parsing the serial into a line buffer and is no longer available
#     when interpreting the checksum, etc. (e.g. "M117 2 \* 2 = 4" will end up being "M117 2 " when
#     it's executed)
#   - The checksum used will be extracted from the _last_ asterisk in the line
#     (Marlin_main.cpp/get_serial_commands[1081]/char *apos = strrchr(command, '*');)
#     (e.g. "N5 G0 X1 *12 *83" will validate "N5 G0 X1 *12 " against a checksum of 83)
#   - When reading from an SD card, backslashes are not supported, since that's done via a
#     different implementation
#   - When reading from an SD card, a colon will terminate the current line.  That behavior was
#     removed from the serial read routine (I believe when the escaping mechanism was added).
#   - Everything in the line will be truncated following the _first_ asterisk in the line
#     (parse.cpp/GcodeParser::parse[110]/char *starpos = strchr(p, '*'); - not sure why it was even
#     copied into the buffer in the first place... (e.g. "G0 X1 *12 *83" will be truncated to
#     "G0 X1" before being executed)

PAT_WHITESPACE = r"[ ]*"
PAT_LINE_NUMBER = r"(?:[Nn](\d+))?"

PAT_CODE = (
    r"(?:" +
    r"([GgMm])" + PAT_WHITESPACE + r"(\d+)(?:\.(\d+))?" +
    r"|" +
    r"([Tt])" + PAT_WHITESPACE + r"(\d+)" +
    r")"
)

# '\\', '\;' or anything but a ';'
# As of 1.1.9, escapes are only honored by Marlin when reading from the serial, and really only
# affect comments, since they are dropped before other portions of the command are parsed (such as
# checksum, etc)
PAT_PARAMETERS_CHAR = r"(?:\\\\|\\;|[^;*])"

PAT_CHECKSUM = r"(?:\*(\d+))?"
PAT_COMMENT = r"(;[^\r\n]*)?"
PAT_EOL = r"(\r\n|\r|\n|\Z)"

PAT_GCODE_LINE = (
    r"(" + PAT_WHITESPACE + ")" +
    r"(" +
    r"(?:" +
    PAT_LINE_NUMBER +
    PAT_WHITESPACE + PAT_CODE +
    PAT_WHITESPACE + r"(" + PAT_PARAMETERS_CHAR + "+?)?" +
    PAT_WHITESPACE +
    PAT_CHECKSUM +
    r")?" +
    r"|" +
    r"[^;\r\n]*?" +
    r")(" + PAT_WHITESPACE + ")" +
    PAT_COMMENT +
    PAT_EOL
)

print "PAT_GCODE_LINE=" + PAT_GCODE_LINE

# Regex for parsing a Gcode command type+code+subCode
# Capture groups:
#   1 - G or M command type, if present
#   2 - G or M command code, if present
#   3 - G or M command sub code, if present
#   4 - T command type, if present
#   5 - T command code, if present
REGEX_GCODE_CODE = re.compile(r"\A" + PAT_WHITESPACE + PAT_CODE + PAT_WHITESPACE + r"\Z")

# Regex for parsing a line of Gcode
# Capture groups:
#   1 - Leading whitespace (may be empty string)
#   2 - All text before trailing whitespace, comment or eol (may be empty string)
#   3 - Line number, if present, requires G, M or T code
#   4 - G or M command type, if present
#   5 - G or M command code, if present
#   6 - G or M command sub code, if present
#   7 - T command type, if present
#   8 - T command code, if present
#   9 - Parameters, if present, requires G, M or T code
#  10 - Checksum, if present, requires G, M or T code
#  11 - Trailing whitespace before comment or eol (may be empty string)
#  12 - Comment, if present
#  13 - EOL (may be empty string)
REGEX_GCODE_LINE = re.compile(PAT_GCODE_LINE)

# Regex for validating a string intended for use as gcode command parameters
REGEX_PARAMETERS = re.compile(
    r"\A" + PAT_WHITESPACE + r"(" + PAT_PARAMETERS_CHAR + "*?)" + PAT_WHITESPACE + r"\Z"
)

# Pattern matching a typical floating point number value.
PAT_SIGNED_FLOAT = r"[-+]?[0-9]*\.?[0-9]+"

# Pattern for parsing a Gcode parameter with optional floating point value.
PAT_PARAMETER = (
    PAT_WHITESPACE +
    r"(?:" +
    r"([A-Za-z])" +
    PAT_WHITESPACE +
    r"(" + PAT_SIGNED_FLOAT + r")?" +
    r")"
)

# Pattern for matching a parameter OR non-alpha character
PAT_PARAMETER_OR_STR = (
    PAT_WHITESPACE +
    r"(?:" +
    PAT_PARAMETER +
    r"|" +
    r"([^A-Za-z])" +
    r")"
)

# Pattern for parsing a Gcode parameter
# Capture groups:
#   1 - Parameter letter char
#   2 - Parameter value if any
REGEX_PARAMETER = re.compile(PAT_PARAMETER)

# Pattern for parsing a Gcode parameter or start of string argument
# Capture groups:
#   1 - Parameter letter char
#   2 - Parameter value if any
#   3 - Non letter char
REGEX_PARAMETER_OR_STR = re.compile(PAT_PARAMETER_OR_STR)


class GcodeParser(CommonMixin):  # pylint: disable=too-many-instance-attributes
    """
    Class for parsing lines of Gcode from a string.

    Attributes
    ----------
    source : string | None
        The source string that contains the line parsed or None
    offset : int | None
        Starting offset within `source` where the parsed line starts or None
    length : int
        The total length of the match (0 if no match)
    leadingWhitespace : string
        Any leading whitespace in the parsed line, or empty string if none.
    text : string
        The text of the line prior to any checksum, comment or eol.
    rawChecksum : string
        The non-normalized checksum text, including '*' prefix, or None
    trailingWhitespace : string
        Any trailing whitespace prior to the comment or eol.
    lineNumber : int | None
        The parsed and normalized line number or None
    type : string | None - [read only]
        The type of command (G, M or T, always upper case) or None
    code : int | None - [read only]
        The parsed and normalized G, M or T code number or None
    gcode : string | None
        The normalized gcode (type + code)
    subCode : int | None - [read only]
        The parsed and normalized G or M sub code or None
    parameters : string | None
        The parameter string following the command or None
    parameterDict : OrderedDict | None - [read only]
        The parsed parameters or None
    checksum : int | None - [read only]
        The parsed and normalized checksum or None
    comment : string | None
        The comment parsed or None
    eol : string | None
        The EOL marker parsed or None
    fullText : string
        The full text of the line that was parsed, including any checksum, comment and eol.
    commandString : string
        The normalized gcode command string, not including the computed checksum, comment or eol
    """

    def __init__(self):
        """Initialize the instance to defaults."""
        self.source = ""
        self.offset = 0
        self.length = 0

        self._lineNumber = None
        self._type = None
        self._code = None
        self._gcode = None
        self._subCode = None
        self._parameters = None
        self._parameterDict = None
        self._checksum = None

        self.leadingWhitespace = ""
        self.text = ""
        self._rawChecksum = None
        self.trailingWhitespace = ""
        self.comment = None
        self.eol = ""
        self._commandString = ""

    def parse(self, source=None, offset=None):
        """
        Parse a GCode line from the specified source string starting at the given offset position.

        Parameters
        ----------
        source : string
            The string to parse, or None to use the currently assigned source string.
        offset : int
            Position within the source string to start parsing at.  If source and offset are None,
            parsing will resume with the next line from the current position.  If source is not
            None, then offset will default to 0.

        Returns
        -------
        GcodeParser
            The GcodeParser instance the method was called on, to permit chaining.

        Throws
        ------
        ValueError
            If unable to parse the line
        """
        if (source is not None):
            self.source = source
            if (offset is None):
                offset = 0

        if (offset is not None):
            self.offset = offset
        else:
            self.offset += self.length

        match = REGEX_GCODE_LINE.match(self.source, self.offset)
        if (not match):
            raise ValueError(
                "Unable to parse gcode line: '" + self.source[self.offset:self.offset + 100] + "'"
            )

        if (match.start() != self.offset):
            raise AssertionError(
                "Should match at the specified offset: %s != %s" % (match.start(), self.offset)
            )

        self.length = match.end() - self.offset

        self.leadingWhitespace = match.group(1)
        self.text = match.group(2)
        self.lineNumber = match.group(3)

        self._gcodeMatch(match, 4)

        self._updateParameters(match.group(9))

        self._checksum = match.group(10)
        if (self._checksum is not None):
            self._rawChecksum = "*" + self._checksum
            self._checksum = int(self._checksum)
            self.text = self.text[:-len(self._rawChecksum)]

        self.trailingWhitespace = match.group(11)

        self.comment = match.group(12)
        self.eol = match.group(13)

        return self

    def _gcodeMatch(self, match, index):
        self._commandString = None
        self._type = match.group(index) or match.group(index + 3)
        if (self._type is not None):
            self._type = self._type.upper()
            self._code = int(match.group(index + 1) or match.group(index + 4))
            self._gcode = self._type + str(self._code)
            self._subCode = match.group(index + 2)
            if (self._subCode is not None):
                self._subCode = int(self._subCode)
        else:
            self._code = None
            self._gcode = None
            self._subCode = None

    def parseLines(self, source=None, offset=None):
        """
        Parse gcode lines from a source string, producing this instance for each line parsed.

        Parameters
        ----------
        source : string | None
            The string to parse, or None to use the currently assigned source string.
        offset : int | None
            Position within the source string to start parsing at.  If source and offset are None,
            parsing will resume with the next line from the current position.  If source is not
            None, then offset will default to 0.
        """
        self.parse(source, offset)
        while (self.offset < len(self.source)):
            yield self
            self.parse()

    def validate(self):
        """
        Apply validation rules against the parsed properties.

        The following rules are checked:
          - Both a line number and checksum must be provided, if either is.
          - When a checksum is provided, it matches the calculated value.

        Raises
        ------
        ValueError
            If any of the checks fail.
        """
        if (self._checksum is not None) ^ (self.lineNumber is not None):
            if (self.lineNumber is not None):
                raise ValueError("Line number provided, but no checksum found")
            else:
                raise ValueError("Checksum provided, but no lineNumber found")

        if (self._checksum is not None):
            # Verify the checksum matches our computation
            command = self.leadingWhitespace + self.text
            computedChecksum = self.computeChecksum(command)

            if (self._checksum != computedChecksum):
                raise ValueError(
                    "Checksum mismatch (%s != %s [computed]): '%s'" % (
                        self._checksum,
                        computedChecksum,
                        command
                    )
                )

    @property
    def lineNumber(self):
        """Integer line number of the line, or None if no line number was provided."""
        return self._lineNumber

    @lineNumber.setter
    def lineNumber(self, value):
        """
        Assign a new line number to the line.

        Parameters
        ----------
        value : int | None
            The new line number to assign, or None for no line number
        """
        if (self._lineNumber != value):
            if (value is None):
                self._lineNumber = None
            else:
                self._lineNumber = int(value)

            self._commandString = None

    @property
    def type(self):
        """Return the parsed and normalized command code type ['G', 'M', 'T' or None]."""
        return self._type

    @property
    def code(self):
        """Return the parsed and normalized command code number or None."""
        return self._code

    @property
    def gcode(self):
        """Return the parsed and normalized command type and code (but not subcode)."""
        return self._gcode

    @gcode.setter
    def gcode(self, value):
        """
        Assign a new Gcode (type, code, and optional subcode) value.

        Parameters
        ----------
        value : string
            A gcode command (type + code OR type + code + subcode, e.g. 'G0' or 'G38.2')
        """
        match = REGEX_GCODE_CODE.match(value)
        if (not match):
            raise ValueError("Unable to parse gcode value: " + repr(value))

        self._gcodeMatch(match, 1)

    @property
    def subCode(self):
        """Return the parsed and normalized G or M sub code or None."""
        return self._subCode

    @property
    def parameters(self):
        """Command parameters as a single string."""
        return self._parameters

    def _updateParameters(self, value):
        """Assign new command parameters as a single string, without validation."""
        self._parameters = value
        self._parameterDict = None
        self._commandString = None

    @parameters.setter
    def parameters(self, value):
        """
        Assign new command parameters as a single string, with validation.

        Validation consists of ensuring the assigned string does not contain any content that could
        be interpreted as a checksum value or comment.
        """
        match = REGEX_PARAMETERS.match(value)
        if (match):
            self._updateParameters(match.group(1))
        else:
            raise ValueError("Unable to validate parameters value: " + repr(value))

    def parameterItems(self, source=None):
        """
        Generate a sequence of parameter name->value tuples parsed from the parameters string.

        Note that the same non-empty name may be generated multiple times, once for each occurrence
        in the parameter string.

        Parameters
        ----------
        source : string | None
            The parameter string to parse and iterate over.  If None, the current value of the
            'parameters' property will be used.

        Returns
        -------
        Sequence of (name, value)
            Tuple containing the parameter name (e.g. 'X', 'Y', or '' for an otherwise unrecognized
            string value) and the associated value.  When the name is not an empty string, the
            value will be either a float or None.  When the name is an empty string, the value may
            be any string.
        """
        if (source is None):
            source = self._parameters
            if (source is None):
                return

        offset = 0
        stringArgOffset = None

        regex = REGEX_PARAMETER_OR_STR
        match = regex.match(source, offset)
        while (match):
            name = match.group(1)
            if (name):
                name = name.upper()
                value = match.group(2)
                if (value is not None):
                    value = float(value)
                elif (stringArgOffset is None):
                    stringArgOffset = match.start(1)
                    regex = REGEX_PARAMETER

                yield (name, value)
            elif (stringArgOffset is None):
                stringArgOffset = match.start(3)
                regex = REGEX_PARAMETER

            offset = match.end()
            match = regex.match(source, offset)

        if (stringArgOffset is not None):
            yield ('', source[stringArgOffset:])

    @property
    def parameterDict(self):
        """
        Construct a dictionary of the parsed parameter values.

        Returns
        -------
        OrderedDict of parameter name -> value
            Each entry in the returned dictionary is keyed by the parameter name (e.g. 'X', 'Y',
            or '' for an otherwise unrecognized string value) mapped to the associated value.  When
            the name is not an empty string, the value will be either a float or None.  When the
            name is an empty string, the value may be any string.  Should a given parameter name
            occur multiple times in the source string, the value associated with that name will be
            the last occurrence in the string.
        """
        if (self._parameters is None):
            return None

        if (self._parameterDict is None):
            params = OrderedDict()

            for name, value in self.parameterItems():
                params[name] = value

            self._parameterDict = params

        return self._parameterDict

    @parameterDict.setter
    def parameterDict(self, paramsDict):
        """
        Assign the parameters attribute to a string string constructed from the given dictionary.

        Parameters
        ----------
        paramsDict : dictionary
            The argument names and values to apply to the command (e.g. E=1.2, X=100, Y=200).
            If the associated value is None or an empty string, the argument will be added to the
            command with no associated value.
        """
        vals = []
        for key, val in paramsDict.iteritems():
            if (val is not None):
                vals.append(key + str(val))
            else:
                vals.append(key)

        if (vals):
            self._updateParameters(" ".join(vals))
        else:
            self._updateParameters(None)

    @staticmethod
    def computeChecksum(value):
        """
        Compute a checksum for the specified string.

        The checksum is computed by XORing the bytes in the string together.

        Parameters
        ----------
        value : string
            The string to compute the checksum for.

        Returns
        -------
        int
            The computed checksum.
        """
        checksum = 0
        for byte in bytearray(value):
            checksum ^= byte
        return checksum

    @property
    def checksum(self):
        """Return the parsed checksum value for the line."""
        return self._checksum

    @property
    def rawChecksum(self):
        """Return the non-normalized checksum text parsed, including '*' prefix, or None."""
        return self._rawChecksum

    def stringify(
            self,
            separator=" ",
            includeLineNumber=True,
            includeChecksum=None,
            includeComment=True,
            includeEol=True
    ):
        """
        Construct a normalized command string from the instance properties.

        Parameters
        ----------
        separator : string
            The separator to use between the individual command components.  Defaults to a single
            space.
        includeLineNumber : boolean
            Whether to include the line number in the result (if a line number is known).  Defaults
            to True.
        includeChecksum : boolean
            Whether to include a calculated checksum in the result.  Will use the same value and
            logic as 'includeLineNumber' by default, including a checksum if a line number is
            known and 'includeLineNumber' is True.
        includeComment : boolean
            Whether to include the comment in the result (if a comment is known).  Defaults to True.
        includeEol : boolean
            Whether to include the eol marker in the result (if an eol is known).  Defaults to True.
        """
        checksum = ""
        if (self.gcode is None):
            result = self.text
        else:
            pieces = []

            if (includeLineNumber) and (self._lineNumber is not None):
                if (includeChecksum is None):
                    includeChecksum = True

                pieces.append("N" + str(self._lineNumber))

            pieces.append(
                self.gcode if (self._subCode is None) else self.gcode + "." + str(self._subCode)
            )

            if (self._parameters is not None):
                pieces.append(self._parameters)

            result = separator.join(pieces)
            if (includeChecksum):
                result += separator
                checksum = self.computeChecksum(result)

        includeComment = includeComment and (self.comment is not None)

        return (
            result + checksum +
            ((separator + self.comment) if (includeComment) else "") +
            (self.eol if (includeEol) else "")
        )

    @property
    def commandString(self):
        """Return the normalized gcode string, not including the checksum, comment or eol."""
        if (self._commandString is None):
            self._commandString = self.stringify(
                includeChecksum=False,
                includeComment=False,
                includeEol=False
            )

        return self._commandString

    @property
    def fullText(self):
        """Return the full text of the line parsed, including whitespace, comment and eol."""
        return "".join([
            self.leadingWhitespace,
            self.text,
            "" if (self.rawChecksum is None) else self.rawChecksum,
            self.trailingWhitespace,
            "" if (self.comment is None) else self.comment,
            self.eol
        ])

    def buildCommand(self, gcode, **kwargs):
        """Initialize with the specified gcode and parameters and return the command string."""
        self.__init__()
        self.gcode = gcode
        self.parameterDict = kwargs
        self.eol = ""
        return self.stringify(
            includeComment=False,
            includeLineNumber=False,
            includeEol=False
        )

    def __str__(self):
        """Return the full normalized gcode line, possibly with checksum, comment and eol."""
        return self.stringify()
