# coding=utf-8
"""Module providing the GcodeHandlers class."""

from __future__ import absolute_import

import logging
import re
import math

from .RetractionState import RetractionState
from .ExcludedGcode import EXCLUDE_EXCEPT_FIRST, EXCLUDE_EXCEPT_LAST, EXCLUDE_MERGE
from .Position import Position
# from .AxisPosition import AxisPosition

REGEX_FLOAT_PATTERN = "[-+]?[0-9]*\\.?[0-9]+"
REGEX_FLOAT_ARG = re.compile("^(?P<label>[A-Za-z])(?P<value>%s)" % REGEX_FLOAT_PATTERN)
REGEX_SPLIT = re.compile("\\s+")

INCHES_PER_MM = 25.4
MM_PER_ARC_SEGMENT = 1
TWO_PI = 2 * math.pi

IGNORE_GCODE_CMD = (None,)


def build_command(gcode, **kwargs):
    """
    Construct a Gcode command string with the specified named arguments.

    Parameters
    ----------
    gcode : string
        The Gcode without any arguments (e.g. "G0")

    **kwargs : dict
        The argument names and values to apply to the command (e.g. E=1.2, X=100, Y=200).
        If the associated value is None, that entry will not be added to the command.  To
        include an argument name with no value in the result, set the value for that argument
        to an empty string.

    Returns
    -------
    string
        The final Gcode command as a string
    """
    vals = [gcode]

    for key, val in kwargs.iteritems():
        if (val is not None):
            vals.append(key + str(val))

    if (len(vals) > 1):
        return " ".join(vals)

    return None


class GcodeHandlers(object):
    """
    Maintains the position state and processes Gcode exclusion/manipulation.

    Attributes
    ----------
    _logger : Logger
        Logger for outputting log messages.
    g90InfluencesExtruder : boolean
        Whether a G90 command sets absolute mode for the extruder (True) or not (False).
    enteringExcludedRegionGcode : string | None
        GCode to execute when entering an excluded region.
    exitingExcludedRegionGcode : string | None
        GCode to execute when leaving an excluded region
    extendedExcludeGcodes : dict of Gcode => ExcludedGcode instances
        A dict mapping Gcodes to ExcludedGcode configurations.
    excludedRegions : List of Region
        The currently defined exclusion regions.
    position : Position
        Current axis position, home offsets (M206), offsets (G92) and absolute or relative mode.
    feedRate : float
        Current feed rate.
    feedRateUnitMultiplier : float
        Unit multiplier to apply to feed rate for converting logical units (inches, etc) to native
        units (mm).
    excluding : boolean
        Whether currently in an excluded area or not.
    lastRetraction : RetractionState | None
        Retraction that may need to be recovered.
    lastPosition : Position | None
        Last position state before entering an excluded area.  Used for determining the best time
        to perform Z-axis moves when exiting an excluded region (e.g. before or after X/Y moves)
    pendingCommands : dict of Gcode commands and their arguments
        Storage for pending commands to execute when exiting an excluded area.
    """

    def __init__(self, logger):
        """
        Initialize the instance properties.

        Parameters
        ----------
        logger : Logger
            Logger for outputting log messages.
        """
        self._logger = logger

        # Configuration values
        self.g90InfluencesExtruder = False
        self.enteringExcludedRegionGcode = None
        self.exitingExcludedRegionGcode = None
        self.extendedExcludeGcodes = {}

        self.resetInternalPrintState(True)

    # pylint: disable=attribute-defined-outside-init
    def resetInternalPrintState(self, clearExcludedRegions=False):
        """
        Reset the internal print state properties to their default values.

        This method would typically be executed before a new print is started.

        Parameters
        ----------
        clearExcludedRegions : boolean
            Whether to clear the currently defined exclusion regions or not.
        """
        if (clearExcludedRegions):
            self.excludedRegions = []

        self.position = Position()
        self.feedRate = 0
        self.feedRateUnitMultiplier = 1
        self.excluding = False
        self.lastRetraction = None
        self.lastPosition = None
        self.pendingCommands = {}

    def getRegion(self, regionId):
        """
        Retrieve the region with the specified id.

        Parameters
        ----------
        regionId
            The id of the region to retrieve.

        Returns
        -------
        Region | None
            The requested region, or None if no region matched the given id.
        """
        for region in self.excludedRegions:
            if (region.id == regionId):
                return region

        return None

    def addRegion(self, region):
        """
        Add a new exclusion region.

        Parameters
        ----------
        region : Region
            The new region to add

        Raises
        ------
        ValueError
            If the specified region has the same id as an existing region.
        """
        if (self.getRegion(region.id) is None):
            self._logger.info("New exclude region added: %s", region)
            self.excludedRegions.append(region)
        else:
            raise ValueError("region id collision")

    def deleteRegion(self, regionId):
        """
        Remove the region with the specified id.

        Parameters
        ----------
        regionId : string
            The id of the region to remove.

        Returns
        -------
        boolean
            True if the specified region existed and was removed, False if the id did not match a
            defined region.
        """
        for index in range(0, len(self.excludedRegions)):
            if (self.excludedRegions[index].id == regionId):
                del self.excludedRegions[index]
                return True

        return False

    def replaceRegion(self, newRegion, mustContainOldRegion=False):
        """
        Replace an existing region with a new one, matching by id.

        Parameters
        ----------
        newRegion : Region
            The new region to use as a replacement for an existing one with a matching id.
        mustContainOldRegion : boolean
            If True, the old region must be fully contained in the new region or a ValueError will
            be thrown.

        Raises
        ------
        ValueError
            If the new region does not have an assigned id or mustContainOldRegion is True and the
            old region is not fully contained in the new region.
        """
        if (newRegion.id is None):
            raise ValueError("id is required for new region")

        for index in range(0, len(self.excludedRegions)):
            region = self.excludedRegions[index]
            if (region.id == newRegion.id):
                if (mustContainOldRegion and not newRegion.containsRegion(region)):
                    self._logger.info(
                        "Cannot replace region %s with new region %s.  " +
                        "New region doesn't contain the old region. " +
                        "(new contains old=%s oldContainsNew=%s)",
                        region,
                        newRegion,
                        newRegion.containsRegion(region),
                        region.containsRegion(newRegion)
                    )
                    raise ValueError("the new region must completely contain the original area")

                self.excludedRegions[index] = newRegion
                return

        raise ValueError("specified region not found")

    def isPointExcluded(self, x, y):
        """
        Test a point to determine whether it is contained in an excluded region.

        Parameters
        ----------
        x : float
            The x coordinate of the point to test
        y : float
            The y coordinate of the point to test

        Returns
        -------
        boolean
            True if the point is contained within a defined exclude region, False otherwise.
        """
        for region in self.excludedRegions:
            if (region.containsPoint(x, y)):
                return True

        return False

    def isAnyPointExcluded(self, *xyPairs):
        """
        Test whether any point in a list of x,y coordinate pairs is contained in an excluded region.

        Parameters
        ----------
        xyPairs : List of x,y pairs
            List containing an even number of float values.  Each value at an even index
            (0, 2, 4, etc) is an x coordinate, and each odd indexed value is a y coordinate.
            The first point is comprised of the x value at index 0 and the y value at index 1,
            and so on.

        Returns
        -------
        boolean
            True if any point in the list is contained in an excluded region, False otherwise.
        """
        xAxis = self.position.X_AXIS
        yAxis = self.position.Y_AXIS
        exclude = False

        for index in range(0, len(xyPairs), 2):
            x = xAxis.setLogicalPosition(xyPairs[index])
            y = yAxis.setLogicalPosition(xyPairs[index + 1])

            if (not exclude and self.isPointExcluded(x, y)):
                exclude = True

        self._logger.debug("isAnyPointExcluded: pt=%s,%s: %s", x, y, exclude)
        return exclude

    def recordRetraction(self, retract, returnCommands):
        """
        Process a retraction to determine whether it should be excluded or executed.

        Parameters
        ----------
        retract : RetractionState
            The retraction that occurred.
        returnCommands : List of Gcode commands | None
            The Gcode command list to append any new command(s) to.  If None, a new list will be
            created.

        Returns
        -------
        List of Gcode commands
            The Gcode command list provided in *returnCommands* or a newly created list.  If the
            retraction should be performed, the appropriate Gcode command(s) will be appended to
            the returned list.
        """
        if (self.lastRetraction is None):
            self.lastRetraction = retract

            if (self.excluding):
                # If this is the first retraction while excluding allow the retraction to execute
                self._logger.info(
                    "Initial retraction encountered while excluding, allowing retraction to " +
                    "proceed: retract=%s",
                    retract
                )
                returnCommands = retract.addRetractCommands(self.position, returnCommands)
            elif (returnCommands is None):
                returnCommands = [retract.originalCommand]
            else:
                returnCommands.append(retract.originalCommand)
        elif (self.lastRetraction.recoverExcluded):
            # Ignore this retraction command and clear recovery flag
            # (prior recovery was excluded, so already retracted)
            self.lastRetraction.recoverExcluded = False
            if (not self.lastRetraction.firmwareRetract):
                self.lastRetraction.feedRate = self.feedRate
        else:
            # This is an additonal retraction that hasn't had its recovery excluded
            # It doesn't seem like this should occur in a well-formed file
            # Since it's not expected, log it and let it pass through
            self._logger.debug(
                "Encountered multiple retractions without an intervening recovery " +
                "(excluding=%s). Allowing this retraction to proceed: %s",
                self.excluding, retract
            )
            if (self.excluding):
                returnCommands = retract.addRetractCommands(self.position, returnCommands)
            elif (returnCommands is None):
                returnCommands = [retract.originalCommand]
            else:
                returnCommands.append(retract.originalCommand)

        self._logger.debug(
            "retraction: excluding=%s, retract=%s, returnCommands=%s",
            self.excluding, retract, returnCommands
        )

        return returnCommands

    def recoverRetractionIfNeeded(
            self, returnCommands=None, originalCmd=None, firmwareRecovery=None
    ):
        """
        Execute a recovery for a previously executed retraction if one is needed.

        Parameters
        ----------
        returnCommands : List of Gcode commands | None
            The Gcode command list to append any new command(s) to.  If None, a new list will be
            created.
        originalCmd : string | None
            Original retraction gcode.
        firmwareRecovery : boolean | None
            Whether to request a firmware recovery (G11) or not.

        Returns
        -------
        List of Gcode commands
            The Gcode command list provided in *returnCommands* or a newly created list.  If the
            recovery should be performed, the appropriate Gcode command(s) will be appended to the
            returned list.
        """
        if (self.lastRetraction is not None):
            if (self.excluding):
                if (firmwareRecovery is not None):
                    self.lastRetraction.recoverExcluded = True
            else:
                lastRetraction = self.lastRetraction
                if (lastRetraction.recoverExcluded):
                    # Recover from the previous retraction
                    self._logger.info(
                        "Executing pending recovery for previous retraction: %s",
                        lastRetraction
                    )

                    returnCommands = lastRetraction.addRecoverCommands(
                        self.position,
                        returnCommands
                    )

                self.lastRetraction = None

                # Execute the original command
                if (originalCmd is not None):
                    if (firmwareRecovery is not None) and lastRetraction.recoverExcluded:
                        # The command is a recovery, but we just recovered from a previous
                        # retraction.  That should indicate multiple recoveries without an
                        # intervening retraction.
                        # This isn't really an expected case, so log it
                        self._logger.info(
                            "Recovery encountered immediately following a pending recovery " +
                            "action: originalCmd=%s, lastRetraction=%s",
                            originalCmd, lastRetraction
                        )

                    if (returnCommands is not None):
                        returnCommands.append(originalCmd)
                    else:
                        returnCommands = [originalCmd]
        elif (not self.excluding and (originalCmd is not None)):
            if (firmwareRecovery is not None):
                # This is a recovery that doesn't correspond to a previous retraction
                # It doesn't seem like this should occur (often) in a well-formed file.
                # Cura generates one at the start of the file, but doesn't seem to after that point.
                # Since it's not generally expected, log it
                self._logger.debug(
                    "Encountered recovery without a corresponding retraction: %s",
                    originalCmd
                )

            if (returnCommands is not None):
                returnCommands.append(originalCmd)
            else:
                returnCommands = [originalCmd]

        if (firmwareRecovery is not None):
            self._logger.debug(
                "recovery: excluding=%s, originalCmd=%s, returnCommands=%s",
                self.excluding, originalCmd, returnCommands
            )

        return returnCommands

    def processLinearMoves(self, cmd, extruderPosition, feedRate, finalZ, *xyPairs):
        """
        Process the specified moves to update the position state and determine whether to exclude.

        Parameters
        ----------
        cmd : string
            The original Gcode command that produced the move being processed.
        extruderPosition : float | None
            The ending extruder position of the sequence of moves.  If None, the current extruder
            position is not updated.
        feedRate : float | None
            The feed rate value specified for the move.  If None, the current feed rate is used.
        finalZ : float | None
            The ending z position of the sequence of moves.  If None, the current z position is
            not updated.
        xyPairs : List of x,y pairs
            List containing an even number of float (or None) values.  Each value at an even index
            (0, 2, 4, etc) is an x coordinate, and each odd indexed value is a y coordinate.
            The first point is comprised of the x value at index 0 and the y value at index 1,
            and so on.

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute, if any.
        """
        isDebug = self._logger.isEnabledFor(logging.DEBUG)
        startPosition = None
        if (isDebug):
            startPosition = Position(self.position)

        if (feedRate is not None):
            feedRate *= self.feedRateUnitMultiplier

        eAxis = self.position.E_AXIS
        priorE = eAxis.current
        if (extruderPosition is not None):
            extruderPosition = eAxis.setLogicalPosition(extruderPosition)
            deltaE = extruderPosition - priorE
        else:
            deltaE = 0

        isMove = False

        if (finalZ is not None):
            self.position.Z_AXIS.setLogicalPosition(finalZ)
            isMove = True

        if (not isMove):
            for val in xyPairs:
                if (val is not None):
                    isMove = True
                    break

        if (isMove and (feedRate is not None)):
            self.feedRate = feedRate

        returnCommands = None

        if (isDebug):
            self._logger.debug(
                "processLinearMoves: " +
                "cmd=%s, isMove=%s, extruderPosition=%s, priorE=%s, deltaE=%s, feedRate=%s, " +
                "finalZ=%s, xyPairs=%s, excluding=%s, lastRetraction=%s, startPosition=%s",
                cmd, isMove, extruderPosition, priorE, deltaE, feedRate,
                finalZ, xyPairs, self.excluding, self.lastRetraction, startPosition
            )

        if (not isMove):
            if (deltaE < 0):
                # retraction, record the amount to potentially recover later
                returnCommands = self.recordRetraction(
                    RetractionState(
                        extrusionAmount=-deltaE,
                        feedRate=feedRate,
                        originalCommand=cmd
                    ),
                    returnCommands
                )
            elif (deltaE > 0):
                # recovery
                returnCommands = self.recoverRetractionIfNeeded(returnCommands, cmd, False)
            elif (not self.excluding):
                # something else (no move, no extrude, probably just setting feedrate)
                returnCommands = [cmd]
        elif (self.isAnyPointExcluded(*xyPairs)):
            if (not self.excluding):
                returnCommands = self.enterExcludedRegion(cmd, returnCommands)
        elif (self.excluding):
            returnCommands = self.exitExcludedRegion(cmd, returnCommands)
        else:
            if (deltaE > 0):
                # Recover any retraction recorded from the excluded region before the next
                # extrusion occurs
                returnCommands = self.recoverRetractionIfNeeded(returnCommands, cmd)
            else:
                returnCommands = [cmd]

        if (isDebug):
            self._logger.debug(
                "processLinearMoves: returnCommands=%s, endPosition=%s",
                returnCommands, self.position
            )

        if (returnCommands is None):
            returnCommands = IGNORE_GCODE_CMD

        return returnCommands

    def enterExcludedRegion(self, cmd, returnCommands):
        """
        Determine the Gcode commands to execute when the tool enters an excluded region.

        Parameters
        ----------
        cmd : string
            The Gcode command that caused the tool to exit the excluded region.
        returnCommands : List of Gcode commands | None
            The Gcode command list to append any new command(s) to.  If None, a new list will be
            created.

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute, if any.
        """
        self.excluding = True
        self.lastPosition = Position(self.position)
        self._logger.debug("START excluding: cmd=%s", cmd)

        if (self.enteringExcludedRegionGcode is not None):
            if (returnCommands is None):
                returnCommands = []
            returnCommands.append(self.enteringExcludedRegionGcode)

        return returnCommands

    def exitExcludedRegion(self, cmd, returnCommands):
        """
        Determine the Gcode commands to execute when the tool exits an excluded region.

        Generated commands include recovery for a retraction initiated inside of an excluded
        region, as well as any custom Gcode command configured for the exitingExcludedRegionGcode
        setting.

        Parameters
        ----------
        cmd : string
            The Gcode command that caused the tool to exit the excluded region.
        returnCommands : List of Gcode commands | None
            The Gcode command list to append any new command(s) to.  If None, a new list will be
            created.

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute, if any.
        """
        self.excluding = False

        # Moving back into printable region, process recovery command(s) if needed
        if (returnCommands is None):
            returnCommands = []

        if (self.exitingExcludedRegionGcode is not None):
            returnCommands.append(self.exitingExcludedRegionGcode)

        if (self.pendingCommands):
            for gcode, cmdArgs in self.pendingCommands.iteritems():
                if (isinstance(cmdArgs, dict)):
                    returnCommands.append(build_command(gcode, **cmdArgs))
                else:
                    returnCommands.append(cmdArgs)
            self.pendingCommands = {}

        returnCommands.append(
            # Set logical extruder position
            "G92 E{e}".format(e=self.position.E_AXIS.nativeToLogical())
        )

        newZ = self.position.Z_AXIS.nativeToLogical()
        oldZ = self.lastPosition.Z_AXIS.nativeToLogical()
        moveZcmd = "G0 F{f} Z{z}".format(
            f=self.feedRate / self.feedRateUnitMultiplier,
            z=newZ
        )

        if (newZ > oldZ):
            # Move Z axis _up_ to new position
            # (hopefully help avoid hitting any part we may pass over)
            returnCommands.append(moveZcmd)

        returnCommands.append(
            # Move X/Y axes to new position
            "G0 F{f} X{x} Y{y}".format(
                f=self.feedRate / self.feedRateUnitMultiplier,
                x=self.position.X_AXIS.nativeToLogical(),
                y=self.position.Y_AXIS.nativeToLogical()
            )
        )

        if (newZ < oldZ):
            # Move Z axis _down_ to new position
            # (hopefully we avoided hitting any part we may pass over)
            returnCommands.append(moveZcmd)

        self._logger.debug(
            "STOP excluding: cmd=%s, returnCommands=%s",
            cmd, returnCommands
        )

        return returnCommands

    def planArc(self, endX, endY, i, j, clockwise):  # pylint: disable=invalid-name
        """
        Compute a sequence of moves approximating an arc (G2/G3).

        Parameters
        ----------
        endX : float
            The final x axis position for the tool after the arc is processed
        endY : float
            The final y axis position for the tool after the arc is processed
        i : float
            Offset from the initial x axis position to the center point of the arc
        j : float
            Offset from the initial y axis position to the center point of the arc
        clockwise : boolean
            Whether this is a clockwise (G2) or counter-clockwise (G3) arc.

        Returns
        -------
        List of x,y pairs
            List containing an even number of float values describing coordinate pairs that
            approximate the arc.  Each value at an even index (0, 2, 4, etc) is an x coordinate,
            and each odd indexed value is a y coordinate.  The first point is comprised of the
            x value at index 0 and the y value at index 1, and so on.
        """
        x = self.position.X_AXIS.current
        y = self.position.Y_AXIS.current

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

        # Make a circle if the angular rotation is 0 and the target is current position
        if (angularTravel == 0) and (x == endX) and (y == endY):
            angularTravel = TWO_PI

        # Compute the number of segments based on the length of the arc
        arcLength = angularTravel * radius
        numSegments = int(min(math.ceil(arcLength / MM_PER_ARC_SEGMENT), 2))

        # TODO: verify this
        angle = math.atan2(-i, -j)
        angularIncrement = angularTravel / (numSegments - 1)

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

    def setUnitMultiplier(self, unitMultiplier):
        """
        Set the conversion factor from logical units to native units (G20, G21).

        Parameters
        ----------
        unitMultiplier : float
            The new unit multiplier to use for converting between logical and native units.
        """
        self.feedRateUnitMultiplier = unitMultiplier
        self.position.setUnitMultiplier(unitMultiplier)

    def setAbsoluteMode(self, absolute):
        """
        Set absolute mode for the X, Y, and Z axes, and optionally the E axis.

        Parameters
        ----------
        absolute : boolean
            Whether to enable absolute mode or not.
        """
        self.position.setPositionAbsoluteMode(absolute)
        if (self.g90InfluencesExtruder):
            self.position.setExtruderAbsoluteMode(absolute)

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
        method = getattr(self, "_handle_" + gcode, self._handleOtherGcode)
        return method(cmd, gcode, subcode)

    def _handleOtherGcode(self, cmd, gcode, subcode=None):
        """
        Determine whether a Gcode command is configured for exclusion and process accordingly.

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
        None | IGNORE_GCODE_CMD
            If the command should be processed, returns None, otherwise returns IGNORE_GCODE_CMD to
            prevent processing.
        """
        if (self._logger.isEnabledFor(logging.DEBUG)):
            self._logger.debug(
                "_handleOtherGcode: cmd=%s, gcode=%s, subcode=%s " +
                "(excluding=%s, extendedExcludeGcodes=%s)",
                cmd, gcode, subcode,
                self.excluding, self.extendedExcludeGcodes
            )

        if (gcode and self.excluding):
            entry = self.extendedExcludeGcodes.get(gcode)
            if (entry is not None):
                mode = entry.mode
                if (mode is not None):
                    self._logger.debug(
                        "_handle_other_gcode: gcode excluded by extended configuration: " +
                        "mode=%s, cmd=%s",
                        mode, cmd
                    )

                    if (mode == EXCLUDE_MERGE):
                        pendingArgs = self.pendingCommands.get(gcode)
                        if (pendingArgs is None):
                            pendingArgs = {}
                            self.pendingCommands[gcode] = pendingArgs

                        cmdArgs = REGEX_SPLIT.split(cmd)
                        for index in range(1, len(cmdArgs)):
                            arg = cmdArgs[index]
                            pendingArgs[arg[0].upper()] = arg[1:]
                    elif (mode == EXCLUDE_EXCEPT_FIRST):
                        if (not (gcode in self.pendingCommands)):
                            self.pendingCommands[gcode] = cmd
                    elif (mode == EXCLUDE_EXCEPT_LAST):
                        self.pendingCommands[gcode] = cmd

                    return IGNORE_GCODE_CMD

        # Otherwise, let the command process normally
        return None

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
        cmdArgs = REGEX_SPLIT.split(cmd)
        for index in range(1, len(cmdArgs)):
            match = REGEX_FLOAT_ARG.search(cmdArgs[index])
            if (match is not None):
                label = match.group("label").upper()
                value = float(match.group("value"))
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

        return self.processLinearMoves(cmd, extruderPosition, feedRate, z, x, y)

    def _handle_G1(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G1 - Linear Move (by convention: G1 is used when extruding).

        G1 [E<pos>] [F<rate>] [X<pos>] [Y<pos>] [Z<pos>]
          E - amount to extrude while moving
          F - feed rate to accelerate to while moving
        """
        return self._handle_G0(cmd, gcode, subcode)

    def _handle_G2(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G2 - Controlled Arc Move (Clockwise).

        G2 [E<pos>] [F<rate>] R<radius> [X<pos>] [Y<pos>] [Z<pos>]
        G2 [E<pos>] [F<rate>] I<offset> J<offset> [X<pos>] [Y<pos>] [Z<pos>]
        """
        # pylint: disable=invalid-name
        clockwise = (gcode == "G2")
        xAxis = self.position.X_AXIS
        yAxis = self.position.Y_AXIS
        zAxis = self.position.Z_AXIS

        extruderPosition = None
        feedRate = None
        x = xAxis.current
        y = yAxis.current
        z = zAxis.current
        radius = None
        i = 0
        j = 0
        cmdArgs = REGEX_SPLIT.split(cmd)
        for index in range(1, len(cmdArgs)):
            match = REGEX_FLOAT_ARG.search(cmdArgs[index])
            if (match is not None):
                label = match.group("label").upper()
                value = float(match.group("value"))
                if (label == "X"):
                    x = xAxis.logicalToNative(value)
                elif (label == "Y"):
                    y = yAxis.logicalToNative(value)
                elif (label == "Z"):
                    z = zAxis.logicalToNative(value)
                elif (label == "E"):
                    extruderPosition = self.position.E_AXIS.logicalToNative(value)
                elif (label == "F"):
                    feedRate = value
                elif (label == "R"):
                    radius = value
                if (label == "I"):
                    i = xAxis.logicalToNative(value)
                if (label == "J"):
                    j = yAxis.logicalToNative(value)

        # Based on Marlin 1.1.8
        if (radius is not None):
            p1 = xAxis.current
            q1 = yAxis.current
            p2 = x
            q2 = y

            if (radius and (p1 != p2 or q1 != q2)):
                e = (1 if clockwise else 0) ^ (-1 if (radius < 0) else 1)
                deltaX = p2 - p1
                deltaY = q2 - q1
                dist = math.hypot(deltaX, deltaY)
                halfDist = dist / 2
                h = math.sqrt(radius*radius - halfDist*halfDist)
                midX = (p1 + p2) / 2
                midY = (q1 + q2) / 2
                sx = -deltaY / dist
                sy = -deltaX / dist
                centerX = midX + e * h * sx
                centerY = midY + e * h * sy

                i = centerX - p1
                j = centerY - q1

        if (i or j):
            xyPairs = self.planArc(x, y, i, j, clockwise)
            return self.processLinearMoves(cmd, extruderPosition, feedRate, z, *xyPairs)

        return None

    def _handle_G3(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G3 - Controlled Arc Move (Counter-Clockwise).

        G3 [E<pos>] [F<rate>] R<radius> [X<pos>] [Y<pos>] [Z<pos>]
        G3 [E<pos>] [F<rate>] I<offset> J<offset> [X<pos>] [Y<pos>] [Z<pos>]
        """
        return self._handle_G2(cmd, gcode, subcode)

    # TODO: Implement: G5  - Bezier curve
    #       G5 [E<pos>] I<pos> J<pos> P<pos> Q<pos> X<pos> Y<pos>

    def _handle_G10(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G10 [S0 or S1] - Retract (if no P or L parameter).

        S parameter is for Repetier (0 = short retract, 1 = long retract)
        Existence of a P or L parameter indicates RepRap tool offset/temperature or workspace
        coordinates and is simply passed through unfiltered
        """
        cmdArgs = REGEX_SPLIT.split(cmd)
        for index in range(1, len(cmdArgs)):
            argType = cmdArgs[index][0].upper()
            if (argType == "P") or (argType == "L"):
                return None

        self._logger.debug("_handle_G10: firmware retraction: cmd=%s", cmd)
        returnCommands = self.recordRetraction(
            RetractionState(
                firmwareRetract=True,
                originalCommand=cmd
            ),
            None
        )

        if (returnCommands is None):
            return IGNORE_GCODE_CMD

        return returnCommands

    def _handle_G11(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G11 [S0 or S1] - Recover (unretract).

        S parameter is for Repetier (0 = short unretract, 1 = long unretract)
        """
        returnCommands = self.recoverRetractionIfNeeded(None, cmd, True)
        if (returnCommands is None):
            return IGNORE_GCODE_CMD

        return returnCommands

    def _handle_G20(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """G20 - Set units to inches."""
        self.setUnitMultiplier(INCHES_PER_MM)

    def _handle_G21(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """G21 - Set units to millimeters."""
        self.setUnitMultiplier(1)

    def _handle_G28(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G28 - Auto home.

        G28 [X] [Y] [Z]
        Set the current position to 0 for each axis in the command
        """
        cmdArgs = REGEX_SPLIT.split(cmd)
        homeX = False
        homeY = False
        homeZ = False
        for arg in cmdArgs:
            arg = arg.upper()
            if (arg.startswith("X")):
                homeX = True
            elif (arg.startswith("Y")):
                homeY = True
            elif (arg.startswith("Z")):
                homeZ = True

        if (not (homeX or homeY or homeZ)):
            homeX = True
            homeY = True
            homeZ = True

        if (homeX):
            self.position.X_AXIS.setHome()

        if (homeY):
            self.position.Y_AXIS.setHome()

        if (homeZ):
            self.position.Z_AXIS.setHome()

    def _handle_G90(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """G90 - Set absolute positioning mode."""
        self.setAbsoluteMode(True)

    def _handle_G91(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """G91 - Set relative positioning mode."""
        self.setAbsoluteMode(False)

    def _handle_G92(self, cmd, gcode, subcode=None):  # pylint: disable=unused-argument,invalid-name
        """
        G92 - Set current position.

        G92 [E<pos>] [X<pos>] [Y<pos>] [Z<pos>]
        The hotend isn't actually moved, this command just changes where the firmware thinks it is
        by defining a coordinate offset.
        """
        cmdArgs = REGEX_SPLIT.split(cmd)
        for index in range(1, len(cmdArgs)):
            match = REGEX_FLOAT_ARG.search(cmdArgs[index])
            if (match is not None):
                label = match.group("label").upper()
                value = float(match.group("value"))
                if (label == "E"):
                    # Note: 1.0 Marlin and earlier stored an offset for E instead of directly
                    #   updating the position.
                    # This assumes the newer behavior
                    self.position.E_AXIS.setLogicalPosition(value)
                elif (label == "X"):
                    self.position.X_AXIS.setLogicalOffsetPosition(value)
                elif (label == "Y"):
                    self.position.Y_AXIS.setLogicalOffsetPosition(value)
                elif (label == "Z"):
                    self.position.Z_AXIS.setLogicalOffsetPosition(value)

    def _handle_M206(self, cmd, gcode, subcode=None):  # nopep8 pylint: disable=unused-argument,invalid-name
        """
        M206 - Set home offsets.

        M206 [P<offset>] [T<offset>] [X<offset>] [Y<offset>] [Z<offset>]
        """
        cmdArgs = REGEX_SPLIT.split(cmd)
        for index in range(1, len(cmdArgs)):
            match = REGEX_FLOAT_ARG.search(cmdArgs[index])
            if (match is not None):
                label = match.group("label").upper()
                value = float(match.group("value"))
                if (label == "X"):
                    self.position.X_AXIS.setHomeOffset(value)
                elif (label == "Y"):
                    self.position.Y_AXIS.setHomeOffset(value)
                elif (label == "Z"):
                    self.position.Z_AXIS.setHomeOffset(value)
