# coding=utf-8
"""Module providing the GcodeHandlers class."""

# Potential future improvements:
#
# - Implement: G5  - Bezier curve
#      G5 [E<pos>] I<pos> J<pos> P<pos> Q<pos> X<pos> Y<pos>
#

from __future__ import absolute_import

import math

from .RetractionState import RetractionState
from .AtCommandAction import ENABLE_EXCLUSION, DISABLE_EXCLUSION
from .GcodeParser import GcodeParser


# A unit multiplier for converting logical units in inches to millimeters.
INCH_TO_MM_FACTOR = 25.4

# The length of individual generated arc segments.
MM_PER_ARC_SEGMENT = 1

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

    def planArc(self, endX, endY, i, j, clockwise):  # pylint: disable=too-many-locals,invalid-name
        """
        Compute a sequence of moves approximating an arc (G2/G3).

        This code is based on the arc planning logic in Marlin.

        Parameters
        ----------
        endX : float
            The final x axis position for the tool after the arc is processed, in logical units
        endY : float
            The final y axis position for the tool after the arc is processed, in logical units
        i : float
            Offset from the initial x axis position to the center point of the arc, in logical units
        j : float
            Offset from the initial y axis position to the center point of the arc, in logical units
        clockwise : boolean
            Whether this is a clockwise (G2) or counter-clockwise (G3) arc.

        Returns
        -------
        List of x,y pairs
            List containing an even number of float values describing coordinate pairs in logical
            units that approximate the arc.  Each value at an even index (0, 2, 4, etc) is an x
            coordinate, and each odd indexed value is a y coordinate.  The first point is comprised
            of the x value at index 0 and the y value at index 1, and so on.
        """
        x = self.state.position.X_AXIS.nativeToLogical()
        y = self.state.position.Y_AXIS.nativeToLogical()

        radius = math.hypot(i, j)

        # CCW angle of rotation between position and target from the circle center.
        centerX = x + i
        centerY = y + j
        rtX = endX - centerX
        rtY = endY - centerY
        angularTravel = math.atan2(-i * rtY + j * rtX, -i * rtX - j * rtY)
        if (angularTravel < 0):
            angularTravel += TWO_PI
        if (clockwise):
            angularTravel -= TWO_PI

        # Make a circle if the angular travel is 0 and the target is current position
        if (angularTravel == 0) and (x == endX) and (y == endY):
            angularTravel = TWO_PI

        # Compute the number of segments to produce based on the length of the arc
        arcLength = abs(angularTravel) * radius
        numSegments = int(math.ceil(arcLength / MM_PER_ARC_SEGMENT))

        angle = math.atan2(-j, -i)
        angularIncrement = angularTravel / numSegments

        rval = []
        for dummy in range(1, numSegments):
            angle += angularIncrement
            rval += [centerX + math.cos(angle) * radius, centerY + math.sin(angle) * radius]

        rval += [endX, endY]

        self._logger.debug(
            "planArc(endX=%s, endY=%s, i=%s, j=%s, clockwise=%s) = %s",
            endX, endY, i, j, clockwise, rval
        )

        return rval

    def computeArcCenterOffsets(
            self, endX, endY, radius, clockwise
    ):  # pylint: disable=too-many-locals
        """
        Compute the i & j offsets for an arc given a radius, direction and ending point.

        Parameters
        ----------
        endX : float
            The ending X coordinate provided to the GCode command, in logical units.
        endY : float
            The ending Y coordinate provided to the GCode command, in logical units.
        radius : float
            The radius of the arc to compute the center point offset for, in logical units.
            A positive value will result in the shortest arc proceeding in the specified direction,
            a negative radius will mirror the calculated center point on the chord between the two
            endpoints to produce the longer arc between the two endpoints.  A value of 0 is not
            permitted.
        clockwise : boolean
            Whether the arc proceeds in a clockwise or counter-clockwise direction.

        Returns
        -------
        pair(i, j)
            The computed center point offset position, in logical units relative to the current
            position.  Will be (0,0) if radius == 0 or the distance between the end points is
            greater that twice the radius.
        """
        # pylint: disable=invalid-name
        position = self.state.position
        i = 0
        j = 0
        p1 = position.X_AXIS.nativeToLogical()
        q1 = position.Y_AXIS.nativeToLogical()
        p2 = endX
        q2 = endY

        # radius cannot be 0, and the two end points cannot be identical
        if (radius and (p1 != p2 or q1 != q2)):
            # clockwise -1/1, counterclockwise 1/-1
            e = -1 if (clockwise ^ (radius < 0)) else 1

            # X and Y differences
            deltaX = p2 - p1
            deltaY = q2 - q1

            # Linear distance between the points
            dist = math.hypot(deltaX, deltaY)
            halfDist = dist / 2

            # Midpoint of chord between the two endpoints
            midX = (p1 + p2) / 2
            midY = (q1 + q2) / 2

            # radius cannot be less than half the distance between the two end points
            if (halfDist <= abs(radius)):
                # Distance to the arc pivot point
                h = math.sqrt(radius*radius - halfDist*halfDist)

                # Slope of the perpendicular bisector
                sx = -deltaY / dist
                sy = -deltaX / dist

                # Pivot point of the arc
                centerX = midX + e * h * sx
                centerY = midY + e * h * sy

                # Offset to pivot point
                i = centerX - p1
                j = centerY - q1

        return (i, j)

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
        extruderPosition = None
        feedRate = None
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

        return self.state.processLinearMoves(cmd, extruderPosition, feedRate, z, x, y)

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
        x = position.X_AXIS.nativeToLogical()
        y = position.Y_AXIS.nativeToLogical()
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

        # Based on Marlin 1.1.8
        if (radius is not None):
            (i, j) = self.computeArcCenterOffsets(x, y, radius, clockwise)

        if (i or j):
            xyPairs = self.planArc(x, y, i, j, clockwise)
            return self.state.processLinearMoves(cmd, extruderPosition, feedRate, z, *xyPairs)

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
