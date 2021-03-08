# coding=utf-8
"""Module providing the GcodeHandlers class."""

# Potential future improvements:
#
# - Implement: G5  - Bezier curve
#      G5 [E<pos>] I<pos> J<pos> P<pos> Q<pos> X<pos> Y<pos>
#

from __future__ import absolute_import, division

import math

from .RetractionState import RetractionState
from .AtCommandAction import ENABLE_EXCLUSION, DISABLE_EXCLUSION
from .GcodeParser import GcodeParser
from .Arc import Arc
from .LineSegment import LineSegment
from .GeometryMixin import floatCmp


# A unit multiplier for converting logical units in inches to millimeters.
INCH_TO_MM_FACTOR = 25.4

TWO_PI = 2 * math.pi


class GcodeHandlers(object):
    """
    Maintains the position state and processes Gcode exclusion/manipulation.

    Attributes
    ----------
    _logger : Logger
        Logger for outputting log messages.
    state : ExcludeRegionState
        The plugin state object
    gcodeParser : GcodeParser
        GcodeParser instance for extracting data from a line of Gcode
    """

    def __init__(self, state, logger):
        """
        Initialize the instance properties.

        Parameters
        ----------
        state : ExcludeRegionState
            The plugin state object
        logger : Logger
            Logger for outputting log messages.
        """
        assert state is not None, "A state must be provided"
        assert logger is not None, "A logger must be provided"
        self.state = state
        self._logger = logger
        self.gcodeParser = GcodeParser()

    def handleGcode(self, cmd, gcode, subcode=None):
        """
        Inspects the provided gcode command and performs any necessary processing.

        Parameters
        ----------
        cmd : string
            The full Gcode command, including arguments.
        gcode : string
            Gcode command code only, e.g. G0 or M110
        subcode : string | None
            Subcode of the GCODE command, e.g. 1 for M80.1.

        Returns
        -------
        None | List of Gcode commands | IGNORE_GCODE_CMD
            If the command should be processed normally, returns None, otherwise returns one or
            more Gcode commands to execute instead or IGNORE_GCODE_CMD to prevent processing.
        """
        gcode = gcode.upper()

        self.state.numCommands += 1
        method = getattr(self, "_handle_" + gcode, self.state.processExtendedGcode)
        return method(cmd, gcode, subcode)

    def _handle_G0(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G0 - Linear Move (by convention: G0 is used when not extruding).

        G0 [E<pos>] [F<rate>] [X<pos>] [Y<pos>] [Z<pos>]
          E - amount to extrude while moving
          F - feed rate to accelerate to while moving
        """
        position = self.state.position
        extruderPosition = None
        feedRate = None
        x0 = position.X_AXIS.nativeToLogical()
        y0 = position.Y_AXIS.nativeToLogical()
        x = None
        y = None
        z = None

        for label, value in self.gcodeParser.parse(cmd).parameterItems():
            if (value is not None):
                if (label == "E"):
                    extruderPosition = value
                elif (label == "F"):
                    feedRate = value
                elif (label == "X"):
                    x = value
                elif (label == "Y"):
                    y = value
                elif (label == "Z"):
                    z = value

        lineSegment = LineSegment(
            x1=x0,
            y1=y0,
            x2=x0 if (x is None) else x,
            y2=y0 if (y is None) else y
        )

        return self.state.processMove(cmd, extruderPosition, feedRate, lineSegment, x, y, z)

    def _handle_G1(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G1 - Linear Move (by convention: G1 is used when extruding).

        G1 [E<pos>] [F<rate>] [X<pos>] [Y<pos>] [Z<pos>]
          E - amount to extrude while moving
          F - feed rate to accelerate to while moving
        """
        return self._handle_G0(cmd, gcode, subcode)

    def _handle_G2(self, cmd, gcode, subcode=None):  # noqa: C901,unused-argument,invalid-name
        """
        G2 - Controlled Arc Move (Clockwise).

        G2 [E<pos>] [F<rate>] R<radius> [X<pos>] [Y<pos>] [Z<pos>]
        G2 [E<pos>] [F<rate>] I<offset> J<offset> [X<pos>] [Y<pos>] [Z<pos>]
        """
        # pylint: disable=invalid-name, too-many-locals
        clockwise = (gcode == "G2")
        position = self.state.position

        extruderPosition = None
        feedRate = None
        x = x0 = position.X_AXIS.nativeToLogical()
        y = y0 = position.Y_AXIS.nativeToLogical()
        z = position.Z_AXIS.nativeToLogical()
        radius = None
        i = 0
        j = 0

        for label, value in self.gcodeParser.parse(cmd).parameterItems():
            if (value is not None):
                if (label == "X"):
                    x = value
                elif (label == "Y"):
                    y = value
                elif (label == "Z"):
                    z = value
                elif (label == "E"):
                    extruderPosition = value
                elif (label == "F"):
                    feedRate = value
                elif (label == "R"):
                    radius = value
                elif (label == "I"):
                    i = value
                elif (label == "J"):
                    j = value

        try:
            if (radius is not None):
                arc = Arc.fromRadiusP1P2Clockwise(
                    radius, x0, y0, x, y, clockwise
                )
            elif (i or j):
                arc = Arc.fromCenterP1P2Clockwise(
                    x0 + i, y0 + j, x0, y0, x, y, clockwise
                )
            else:
                arc = None

            if (arc is not None):
                return self.state.processMove(cmd, extruderPosition, feedRate, arc, x, y, z)
        except ValueError as ex:
            self._logger.info(
                "Unable to construct Arc from input '%s': from=[%s, %s], to=[X=%s, Y=%s, Z=%s]," +
                " E=%s, F=%s, R=%s, I=%s, J=%s: %s",
                cmd, x0, y0, x, y, z, extruderPosition, feedRate, radius, i, j, ex
            )

        return None

    def _handle_G3(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G3 - Controlled Arc Move (Counter-Clockwise).

        G3 [E<pos>] [F<rate>] R<radius> [X<pos>] [Y<pos>] [Z<pos>]
        G3 [E<pos>] [F<rate>] I<offset> J<offset> [X<pos>] [Y<pos>] [Z<pos>]
        """
        return self._handle_G2(cmd, gcode, subcode)

    def _handle_G10(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G10 [S0 or S1] - Retract (if no P or L parameter).

        S parameter is for Repetier (0 = short retract, 1 = long retract)
        Existence of a P or L parameter indicates RepRap tool offset/temperature or workspace
        coordinates and is simply passed through unfiltered
        """
        for label, _ in self.gcodeParser.parse(cmd).parameterItems():
            if (label in ("P", "L")):
                return None

        self._logger.debug("_handle_G10: firmware retraction: cmd=%s", cmd)
        returnCommands = self.state.recordRetraction(
            RetractionState(
                originalCommand=cmd,
                firmwareRetract=True
            )
        )

        if (not returnCommands):
            return self.state.ignoreGcodeCommand()

        return returnCommands

    def _handle_G11(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G11 [S0 or S1] - Recover (unretract).

        S parameter is for Repetier (0 = short unretract, 1 = long unretract)
        """
        returnCommands = self.state.recoverRetractionIfNeeded(cmd, True)
        if (not returnCommands):
            return self.state.ignoreGcodeCommand()

        return returnCommands

    def _handle_G20(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """G20 - Set units to inches."""
        self.state.setUnitMultiplier(INCH_TO_MM_FACTOR)

    def _handle_G21(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """G21 - Set units to millimeters."""
        self.state.setUnitMultiplier(1)

    def _handle_G28(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G28 - Auto home.

        G28 [X] [Y] [Z]
        Set the current position to 0 for each axis in the command
        """
        position = self.state.position
        homeX = False
        homeY = False
        homeZ = False

        # TODO: Support the "O" parameter (don't home if position known?)
        #    If we think a position is known, then don't change position?
        #    It may be safest to send a position request after the home and wait for the printer
        #    to respond with the new position.

        for label, _ in self.gcodeParser.parse(cmd).parameterItems():
            if (label == "X"):
                homeX = True
            elif (label == "Y"):
                homeY = True
            elif (label == "Z"):
                homeZ = True

        if (not (homeX or homeY or homeZ)):
            homeX = True
            homeY = True
            homeZ = True

        if (homeX):
            position.X_AXIS.setHome()

        if (homeY):
            position.Y_AXIS.setHome()

        if (homeZ):
            position.Z_AXIS.setHome()

    def _handle_G90(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """G90 - Set absolute positioning mode."""
        self.state.setAbsoluteMode(True)

    def _handle_G91(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """G91 - Set relative positioning mode."""
        self.state.setAbsoluteMode(False)

    def _handle_G92(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G92 - Set current position.

        G92 [E<pos>] [X<pos>] [Y<pos>] [Z<pos>]
        The hotend isn't actually moved, this command just changes where the firmware thinks it is
        by defining a coordinate offset.
        """
        position = self.state.position

        for label, value in self.gcodeParser.parse(cmd).parameterItems():
            if (value is not None):
                if (label == "E"):
                    # Note: 1.0 Marlin and earlier stored an offset for E instead of directly
                    #   updating the position.
                    # This assumes the newer behavior
                    position.E_AXIS.setLogicalPosition(value)
                elif (label == "X"):
                    position.X_AXIS.setLogicalOffsetPosition(value)
                elif (label == "Y"):
                    position.Y_AXIS.setLogicalOffsetPosition(value)
                elif (label == "Z"):
                    position.Z_AXIS.setLogicalOffsetPosition(value)

    def _handle_M206(  # pylint: disable=unused-argument,invalid-name
            self, cmd, gcode, subcode=None
    ):
        """
        M206 - Set home offsets.

        M206 [P<offset>] [T<offset>] [X<offset>] [Y<offset>] [Z<offset>]
        """
        position = self.state.position

        for label, value in self.gcodeParser.parse(cmd).parameterItems():
            if (value is not None):
                if (label == "X"):
                    position.X_AXIS.setHomeOffset(value)
                elif (label == "Y"):
                    position.Y_AXIS.setHomeOffset(value)
                elif (label == "Z"):
                    position.Z_AXIS.setHomeOffset(value)

    def handleAtCommand(self, commInstance, cmd, parameters):
        """
        Process registered @-command actions.

        @-commands are only processed when the commInstance is NOT streaming to the SD card.

        Parameters
        ----------
        commInstance : octoprint.util.comm.MachineCom
            The MachineCom instance to use for determining whether streaming to SD and for sending
            any Gcode commands produced.
        cmd : string
            The @-command that was encountered
        parameters : string
            The parameters provided for the @-command

        Returns
        -------
        boolean
            True if the command was processed, False if no action was taken (no registered action,
            or streaming to SD).
        """
        if (commInstance.isStreaming()):
            return False

        handled = False
        entries = self.state.atCommandActions.get(cmd)
        if (entries is not None):
            for entry in entries:
                if (entry.matches(cmd, parameters)):
                    self._logger.debug(
                        "handleAtCommand: processing At-Command: action=%s, cmd=%s, parameters=%s",
                        entry.action, cmd, parameters
                    )

                    handled = True
                    if (entry.action == ENABLE_EXCLUSION):
                        self.state.enableExclusion(cmd + " " + parameters)
                    elif (entry.action == DISABLE_EXCLUSION):
                        for command in self.state.disableExclusion(cmd + " " + parameters):
                            self._logger.debug(
                                "handleAtCommand: sending Gcode command to printer: %s",
                                command
                            )
                            commInstance.sendCommand(command)

                    else:
                        self._logger.warn(
                            "handleAtCommand: unsupported action configuration encountered" +
                            ": action=%s, cmd=%s, parameters=%s",
                            entry.action, cmd, parameters
                        )

        return handled
