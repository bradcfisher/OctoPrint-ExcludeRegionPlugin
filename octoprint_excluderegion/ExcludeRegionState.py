# coding=utf-8
"""Module providing the ExcludeRegionState class."""

from __future__ import absolute_import, division

import logging
import time
from collections import OrderedDict
from collections.abc import Mapping

from .ExcludedGcode import EXCLUDE_EXCEPT_FIRST, EXCLUDE_EXCEPT_LAST, EXCLUDE_MERGE
from .Position import Position
from .RetractionState import RetractionState
from .GcodeParser import GcodeParser

IGNORE_GCODE_CMD = (None,)


class ExcludeRegionState(object):  # pylint: disable=too-many-instance-attributes
    """
    Maintains the current plugin state information.

    Attributes
    ----------
    _logger : Logger
        Logger for outputting log messages.
    g90InfluencesExtruder : boolean
        Whether a G90 command sets absolute mode for the extruder (True) or not (False).
    enteringExcludedRegionGcode : List of string | None
        GCode to execute when entering an excluded region.
    exitingExcludedRegionGcode : List of string | None
        GCode to execute when leaving an excluded region
    extendedExcludeGcodes : dict of Gcode => ExcludedGcode instances
        A dict mapping Gcodes to ExcludedGcode configurations.
    atCommandActions : dict of At-Command => List of AtCommandAcion instances
        A dict mapping At-Commands to AtCommandAction instances.
    excludedRegions : List of Region
        The currently defined exclusion regions.
    position : Position
        Current axis position, home offsets (M206), offsets (G92) and absolute or relative mode.
    feedRate : float
        Current feed rate in native units/minute.
    feedRateUnitMultiplier : float
        Unit multiplier to apply to feed rate for converting logical units (inches/min, etc) to
        native units (mm/min).
    _exclusionEnabled : boolean
        Whether exclusion is currently enabled or not (default True/enabled).  May be controlled
        through At-Commands embedded in the Gcode file or sent via terminal.
    excluding : boolean
        Whether currently in an excluded area or not.
    excludeStartTime : float
        The timstamp when the current exclusion region was entered
    numCommands : int
        The number of Gcode commands that have been intercepted for the current exclusion region
    numExcludedCommands : int
        The number of Gcode commands that have been excluded for the current exclusion region
    lastRetraction : RetractionState | None
        Retraction that may need to be recovered.
    lastPosition : Position | None
        Last position state before entering an excluded area.  Used for determining the best time
        to perform Z-axis moves when exiting an excluded region (e.g. before or after X/Y moves)
    gcodeParser : GcodeParser
        GcodeParser instance for extracting data from a line of Gcode
    pendingCommands : ordereddict of Gcode commands and their arguments
        Storage for pending commands to execute when exiting an excluded area.  Stored either as
        (gcode -> {argName->value, ...}) for EXCLUDE_MERGE, or as (gcode -> commandString) for
        EXCLUDE_EXCEPT_FIRST and EXCLUDE_EXCEPT_LAST.
    """

    def __init__(self, logger):
        """
        Initialize the instance properties.

        Parameters
        ----------
        logger : Logger
            Logger for outputting log messages.
        """
        assert logger is not None, "A logger must be provided"

        self._logger = logger

        # Configuration values
        self.g90InfluencesExtruder = False
        self.enteringExcludedRegionGcode = None
        self.exitingExcludedRegionGcode = None
        self.extendedExcludeGcodes = {}
        self.atCommandActions = {}
        self.gcodeParser = GcodeParser()

        self.resetState(True)

    # pylint: disable=attribute-defined-outside-init
    def resetState(self, clearExcludedRegions=False):
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
        self._exclusionEnabled = True
        self.excluding = False
        self.excludeStartTime = None
        self.numExcludedCommands = 0
        self.numCommands = 0
        self.lastRetraction = None
        self.lastPosition = None
        self.pendingCommands = OrderedDict()

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
            raise ValueError("Region id collision")

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
                    raise ValueError("The updated region must completely contain the original area")

                self.excludedRegions[index] = newRegion
                return

        raise ValueError("Specified region not found")

    def isPointExcluded(self, x, y):
        """
        Test a point to determine whether it is contained in an excluded region.

        Parameters
        ----------
        x : float
            The x coordinate of the point to test, in physical units
        y : float
            The y coordinate of the point to test, in physical units

        Returns
        -------
        boolean
            True if the point is contained within a defined exclude region, False otherwise.
        """
        if (self._exclusionEnabled):
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
            List containing an even number of float values, in logical coordinate units.  Each
            value at an even index (0, 2, 4, etc) is an x coordinate, and each odd indexed value
            is a y coordinate.  The first point is comprised of the x value at index 0 and the y
            value at index 1, and so on.

        Returns
        -------
        boolean
            True if any point in the list is contained in an excluded region, False otherwise.
        """
        if (self._exclusionEnabled):
            xAxis = self.position.X_AXIS
            yAxis = self.position.Y_AXIS

            for index in range(0, len(xyPairs), 2):
                x = xAxis.setLogicalPosition(xyPairs[index])
                y = yAxis.setLogicalPosition(xyPairs[index + 1])

                if (self.isPointExcluded(x, y)):
                    return True

        return False

    def isExclusionEnabled(self):
        """Whether exclusion is currently enabled (True) or disabled (False)."""
        return self._exclusionEnabled

    def disableExclusion(self, context):
        """
        Disable exclusion processing.

        Parameters
        ----------
        context : string
            Context string (generally an At-Command or OctoPrint event) to include in log output.

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute, or an empty list if none were generated.  It is up to
            the caller to ensure these commands are sent to the printer.
        """
        returnCommands = []
        if (self._exclusionEnabled):
            self._logger.info("Exclusion disabled: context=%s", context)
            self._exclusionEnabled = False

            # If exclusion was disabled, stop any current exclusion
            if (self.excluding):
                returnCommands = self.exitExcludedRegion(context)
        else:
            self._logger.debug("Exclusion already disabled, NOP: context=%s", context)

        return returnCommands

    def enableExclusion(self, context):
        """
        Enable exclusion processing.

        Parameters
        ----------
        context : string
            Context string (generally an At-Command or OctoPrint event) to include in log output.
        """
        if (not self._exclusionEnabled):
            self._logger.info("Exclusion enabled: context=%s", context)
            self._exclusionEnabled = True
        else:
            self._logger.debug("Exclusion already enabled, NOP: context=%s", context)

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

        The mode for the E axis will only be updated if the g90InfluencesExtruder property is set
        to True.

        Parameters
        ----------
        absolute : boolean
            Whether to enable absolute mode or not.
        """
        self.position.setPositionAbsoluteMode(absolute)
        if (self.g90InfluencesExtruder):
            self.position.setExtruderAbsoluteMode(absolute)

    def ignoreGcodeCommand(self):
        """Add one to the excluded Gcode count and return IGNORE_GCODE_CMD."""
        self.numExcludedCommands += 1
        return IGNORE_GCODE_CMD

    def recordRetraction(self, retract):
        """
        Process a retraction to determine whether it should be excluded or executed.

        Parameters
        ----------
        retract : RetractionState
            The retraction that occurred.

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute, or an empty list if none were generated.  If the
            retraction should be performed, the appropriate Gcode command(s) will be appended to
            the returned list.  It is up to the caller to ensure these commands are sent to the
            printer.
        """
        returnCommands = []

        if (self.lastRetraction is None):
            self.lastRetraction = retract

            if (self.excluding):
                # If this is the first retraction while excluding allow the retraction to execute
                self._logger.info(
                    "Initial retraction encountered while excluding, allowing retraction to " +
                    "proceed: retract=%s",
                    retract
                )
                returnCommands = retract.generateRetractCommands(self.position)
            else:
                returnCommands.append(retract.originalCommand)
        elif (self.lastRetraction.recoverExcluded):
            # Ignore this retraction command and clear recovery flag
            # (prior recovery was excluded, so already retracted)
            self.lastRetraction.recoverExcluded = False
            if (not self.lastRetraction.firmwareRetract):
                self.lastRetraction.feedRate = self.feedRate
        elif (self.lastRetraction.allowCombine):
            # Multiple retractions have been encountered without any intervening recovery/extrusion.
            # This type of retraction can be genrated by Slic3r when retraction is enabled along
            # with wipe or retract_layer_change.  That combination of options can generate multiple
            # retractions as part of the wipe or layer changed moves.

            self.lastRetraction.combine(retract, self._logger)

            if (self.excluding):
                self._logger.debug(
                    "Encountered multiple retractions without an intervening recovery " +
                    "(excluding=%s). Allowing this retraction to proceed: %s",
                    self.excluding, retract
                )

                returnCommands = retract.generateRetractCommands(self.position)
            else:
                returnCommands.append(retract.originalCommand)
        elif (self.excluding):
            # A retraction was encountered that would have normally been combined, but the current
            # retraction state no longer permits accumulating more retraction (e.g. some
            # extrusion/recovery occurred between the prior retraction and this retraction.
            # In this case, we simply ignore the retraction to prevent over-retracting the filament.
            self._logger.debug(
                "Suppressing retraction following excluded recover (already retracted)"
            )
        else:
            # Let it pass unhindered
            returnCommands.append(retract.originalCommand)

        self._logger.debug(
            "retraction: excluding=%s, retract=%s, returnCommands=%s",
            self.excluding, retract, returnCommands
        )

        return returnCommands

    def _recoverRetraction(self, cmd, isRecoveryCommand):
        """
        Execute a recovery for a previously executed retraction (if any).

        The provided command will be appended at the end of the returned list of Gcodes.

        Parameters
        ----------
        cmd : string
            The gcode the retraction is being recovered for.
        isRecoveryCommand : boolean
            Whether the triggering command is a recovery (G11 or G0/G1 with no X/Y/Z component)
            [True], or an extruding move (G0/G1 with some X/Y/Z component) [False].

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute.  If a recovery should be performed, the appropriate
            Gcode command(s) will be prepended to the returned list.  The cmd value passed in will
            always be included as the final value in the returned list.  It is up to the caller to
            ensure these commands are sent to the printer.
        """
        returnCommands = []

        lastRetraction = self.lastRetraction
        if (lastRetraction.recoverExcluded):
            # Recover from the previous retraction
            self._logger.info(
                "Executing pending recovery for previous retraction: %s",
                lastRetraction
            )

            returnCommands = lastRetraction.generateRecoverCommands(self.position)

        self.lastRetraction = None

        if (isRecoveryCommand and lastRetraction.recoverExcluded):
            # The command is a recovery (not an extruding move), but we just recovered from a
            # previous retraction.  That should indicate multiple recoveries without an
            # intervening retraction.
            # This isn't really an expected case, so log it
            self._logger.info(
                "Recovery encountered immediately following a pending recovery " +
                "action: cmd=%s, lastRetraction=%s",
                cmd, lastRetraction
            )

        # Execute the command
        returnCommands.append(cmd)

        return returnCommands

    def recoverRetractionIfNeeded(
            self, cmd, isRecoveryCommand
    ):
        """
        Execute a recovery for a previously executed retraction if one is needed.

        This will typically be invoked before an extruding move to ensure that a previously executed
        retraction (if any) is recovered before executing the move.

        When not excluding, the cmd passed in will be included in the return value.  When excluding,
        the cmd will not be included in the result and will instead be dropped.

        Parameters
        ----------
        cmd : string
            The gcode the retraction is being recovered for.
        isRecoveryCommand : boolean
            Whether the triggering command is a recovery (G11 or G0/G1 with no X/Y/Z component)
            [True], or an extruding move (G0/G1 with some X/Y/Z component) [False].

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute, or an empty list if currently within an excluded
            region.  If a recovery should be performed, the appropriate Gcode command(s) will be
            prepended to the returned list, and the cmd value passed in will be included as the
            final value.  It is up to the caller to ensure these commands are sent to the printer.
        """
        returnCommands = []

        if (self.lastRetraction is not None):
            self.lastRetraction.allowCombine = False

            if (self.excluding):
                # If excluding, and encountered a recovery (not an extruding move), then update the
                # current retraction state to indicate the retraction should be automatically
                # recovered after exiting the excluded region.
                if (isRecoveryCommand):
                    self.lastRetraction.recoverExcluded = True
            else:
                # If not excluding, then execute any needed recovery commands and then the
                # provided cmd
                returnCommands = self._recoverRetraction(cmd, isRecoveryCommand)
        elif (not self.excluding):
            if (isRecoveryCommand):
                # This is a recovery that doesn't correspond to a previous retraction
                # It doesn't seem like this should occur (often) in a well-formed file.
                # Cura generates one at the start of the file to prime the nozzle, but doesn't seem
                # to after that point.
                # Since it's not generally expected, log it
                self._logger.debug(
                    "Encountered recovery without a corresponding retraction: %s",
                    cmd
                )

            returnCommands.append(cmd)

        if (isRecoveryCommand):
            self._logger.debug(
                "recovery: excluding=%s, cmd=%s, returnCommands=%s",
                self.excluding, cmd, returnCommands
            )

        return returnCommands

    def _processNonMove(self, cmd, deltaE):
        """
        Process a command that doesn't affect the physical position of the X/Y/Z axes.

        These commands will generally be either retractions (deltaE < 0) or recoveries (deltaE > 0)
        which will be tracked to ensure the correct extruder position is maintained.

        Parameters
        ----------
        cmd : Gcode command string
            The Gcode command that is being processed.  Typically a G0/G1 with no X/Y/Z component
            or G10/G11 command.
        deltaE : number
            The offset to apply to the extruder position, in millimeters.

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute, or an empty list if none were generated.  It is up to
            the caller to ensure these commands are sent to the printer.
        """
        if (deltaE < 0):
            # retraction, record the amount to potentially recover later
            return self.recordRetraction(
                RetractionState(
                    originalCommand=cmd,
                    firmwareRetract=False,
                    extrusionAmount=-deltaE,
                    feedRate=self.feedRate
                )
            )
        elif (deltaE > 0):
            # recovery
            return self.recoverRetractionIfNeeded(cmd, True)
        elif (not self.excluding):
            # something else (no move, no extrude, probably just setting feedrate)
            return [cmd]

        return []

    def _processExcludedMove(self, cmd, deltaE):
        """
        Process a command for which some point falls within an excluded region.

        Parameters
        ----------
        cmd : Gcode command string
            The Gcode command that is being processed.  Typically a G0/G1 with some X/Y/Z component.
        deltaE : number
            The offset to apply to the extruder position, in millimeters.

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute, or an empty list if none were generated.  It is up to
            the caller to ensure these commands are sent to the printer.
        """
        if (not self.excluding):
            returnCommands = self.enterExcludedRegion(cmd)
        else:
            returnCommands = []

        if (deltaE < 0):
            # To accommodate for Slic3r retraction behavior, check for retractions
            # for moves as well.
            returnCommands.extend(self._processNonMove(cmd, deltaE))

        return returnCommands

    def processLinearMoves(self, cmd, extruderPosition, feedRate, finalZ, *xyPairs):
        """
        Process the specified moves to update the position state and determine whether to exclude.

        Parameters
        ----------
        cmd : string
            The original Gcode command that produced the move being processed.
        extruderPosition : float | None
            The ending extruder position of the sequence of moves, in logical units.  If None, the
            current extruder position is not updated, otherwise the extruder position will be
            updated to this value.
        feedRate : float | None
            The feed rate value specified for the move, in logical units/minute.  If None, the
            current feed rate is used, otherwise the current feed rate will be updated based on
            this value.
        finalZ : float | None
            The ending z position of the sequence of moves, in logical units.  If None, the current
            Z position is not updated, otherwise the Z axis position will be updated to this value.
        xyPairs : List of x,y pairs
            List containing an even number of float (or None) values, in logical units.  Each value
            at an even index (0, 2, 4, etc) is an x coordinate, and each odd indexed value is a y
            coordinate.  The first point is comprised of the x value at index 0 and the y value at
            index 1, and so on.  The current X and Y axis position will be updated to the last
            coordinate pair in this list.

        Returns
        -------
        List of Gcode commands | IGNORE_GCODE_CMD
            The Gcode command(s) to execute, or IGNORE_GCODE_CMD if no commands should be sent to
            the printer (including excluding the original cmd).  It is up to the caller to ensure
            these commands are sent to the printer.
        """
        isDebug = self._logger.isEnabledFor(logging.DEBUG)
        startPosition = None
        if (isDebug):
            startPosition = Position(self.position)

        eAxis = self.position.E_AXIS
        priorE = eAxis.current
        if (extruderPosition is not None):
            # Update axis position and convert local var from logical units to millimeters/minute
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

        if (feedRate is not None):
            # Marlin 1.1.9 maintains a single "current" feedrate ("feedrate_mm_s" global var) which
            # is updated by the gcode_get_destination() function in Marlin_main.cpp.
            # (G0/G1/G2/G3/G5)
            # Convert incoming feedRate to millimeters/minute
            self.feedRate = feedRate * self.feedRateUnitMultiplier

        if (isDebug):
            self._logger.debug(
                "processLinearMoves: " +
                "cmd=%s, isMove=%s, extruderPosition=%s, priorE=%s, deltaE=%s, feedRate=%s, " +
                "finalZ=%s, xyPairs=%s, excluding=%s, lastRetraction=%s, startPosition=%s",
                cmd, isMove, extruderPosition, priorE, deltaE, self.feedRate,
                finalZ, xyPairs, self.excluding, self.lastRetraction, startPosition
            )

        if (not isMove):
            # If none of the X/Y/Z argument values were provided (e.g. they are all None), then see
            # if it is a retraction/recovery.  Note that this will NOT execute in any case when any
            # of the X, Y or Z values are provided, even if the provided values are identical to the
            # current position.  This matches the Marlin auto-retract detection behavior (at least
            # for Marlin 1.1.9).
            returnCommands = self._processNonMove(cmd, deltaE)
        elif (self.isAnyPointExcluded(*xyPairs)):
            returnCommands = self._processExcludedMove(cmd, deltaE)
        elif (self.excluding):
            # Moving from an excluded region into a non-excluded region.
            # Processes the necessary commands to move the tool to the new position specified by the
            # command, but does not perform any extrusion or retraction recovery.
            returnCommands = self.exitExcludedRegion(cmd)
        elif (deltaE != 0):
            # Recover any retraction recorded from the excluded region before the next
            # extrusion occurs
            returnCommands = self.recoverRetractionIfNeeded(cmd, False)
        else:
            returnCommands = [cmd]

        if (isDebug):
            self._logger.debug(
                "processLinearMoves: returnCommands=%s, endPosition=%s",
                returnCommands, self.position
            )

        if (not returnCommands):
            returnCommands = self.ignoreGcodeCommand()

        return returnCommands

    def enterExcludedRegion(self, cmd):
        """
        Determine the Gcode commands to execute when the tool enters an excluded region.

        Parameters
        ----------
        cmd : string
            The Gcode command that caused the tool to exit the excluded region.

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute, or an empty list if none were generated.  It is up to
            the caller to ensure these commands are sent to the printer.
        """
        assert self._exclusionEnabled, "Exclusion is disabled"

        if (self.excluding):
            self._logger.debug(
                "Ignoring enterExcludedRegion call when already excluding: cmd=%s" % cmd
            )
            return []

        self.excluding = True
        self.excludeStartTime = time.time()
        self.numExcludedCommands = 0
        self.numCommands = 0
        self.lastPosition = Position(self.position)
        self._logger.info("START excluding: cmd=%s", cmd)

        returnCommands = []
        if (self.enteringExcludedRegionGcode is not None):
            returnCommands.extend(self.enteringExcludedRegionGcode)

        return returnCommands

    def _processPendingCommands(self):
        """
        Generate any pending commands after excluding, including any exit exclude region script.

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute, or an empty list if none were generated.  It is up to
            the caller to ensure these commands are sent to the printer.
        """
        returnCommands = []

        if (self.pendingCommands):
            for gcode, cmdArgs in self.pendingCommands.items():
                if (isinstance(cmdArgs, Mapping)):
                    returnCommands.append(
                        self.gcodeParser.buildCommand(gcode, **cmdArgs)
                    )
                else:
                    returnCommands.append(cmdArgs)
            self.pendingCommands.clear()

        if (self.exitingExcludedRegionGcode is not None):
            returnCommands.extend(self.exitingExcludedRegionGcode)

        return returnCommands

    def exitExcludedRegion(self, cmd):
        """
        Determine the Gcode commands to execute when the tool exits an excluded region.

        Generated commands include the commands necessary to move the tool to the appropriate
        position, as well as any custom Gcode commands configured for the exitingExcludedRegionGcode
        setting.

        Parameters
        ----------
        cmd : string
            The Gcode command that caused the tool to exit the excluded region, used for logging.
            May be an At-Command if triggered as a result of disabling exclusion, or None if
            triggered due to user cancellation.

        Returns
        -------
        List of Gcode commands
            The Gcode command(s) to execute, or an empty list if none were generated.  It is up to
            the caller to ensure these commands are sent to the printer.
        """
        if (not self.excluding):
            self._logger.debug(
                "Ignoring exitExcludedRegion call when not excluding: cmd=%s" % cmd
            )
            return []

        self.excluding = False

        # Moving back into printable region, process recovery command(s) if needed
        returnCommands = self._processPendingCommands()

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
            # Use G0 ("fast" linear move) as this is a non-extruding move
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

        self._logger.info(
            "STOP excluding: cmd=%s, returnCommands=%s, numCommands=%s, numExcludedCommands=%s, " +
            "elapsed seconds=%s",
            cmd, returnCommands, self.numCommands, self.numExcludedCommands,
            time.time() - self.excludeStartTime
        )

        return returnCommands

    def _processExtendedGcodeEntry(self, mode, cmd, gcode):
        """
        Process the given extended GCode command using the provided processing mode.

        Parameters
        ----------
        mode : string
            The mode to use for processing the command.  One of EXCLUDE_ALL, EXCLUDE_MERGE,
            EXCLUDE_EXCEPT_FIRST, or EXCLUDE_EXCEPT_LAST.
        cmd : string
            The full Gcode command, including arguments.
        gcode : string
            Gcode command code only, e.g. G0 or M110

        Returns
        -------
        IGNORE_GCODE_CMD
            Returns IGNORE_GCODE_CMD to prevent processing.
        """
        self._logger.debug(
            "processExtendedGcode: gcode excluded by extended configuration: " +
            "mode=%s, cmd=%s",
            mode, cmd
        )

        if (mode == EXCLUDE_MERGE):
            # Capture the last value for each argument encountered for the command
            # Retrieve & remove existing entry, or create new empty arg dict
            pendingArgs = self.pendingCommands.pop(gcode, {})
            # Append the entry at the end
            self.pendingCommands[gcode] = pendingArgs

            for label, value in self.gcodeParser.parse(cmd).parameterItems():
                pendingArgs[label] = value
        elif (mode == EXCLUDE_EXCEPT_FIRST):
            # Capture the first instance of the command encountered
            if (not (gcode in self.pendingCommands)):
                self.pendingCommands[gcode] = cmd
        elif (mode == EXCLUDE_EXCEPT_LAST):
            # Remove any previous entry and append the last instance of the command encountered
            self.pendingCommands.pop(gcode, None)
            self.pendingCommands[gcode] = cmd

        return self.ignoreGcodeCommand()

    def processExtendedGcode(self, cmd, gcode, subcode=None):
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
                "processExtendedGcode: cmd=%s, gcode=%s, subcode=%s (excluding=%s)",
                cmd, gcode, subcode, self.excluding
            )

        if (gcode and self.excluding):
            entry = self.extendedExcludeGcodes.get(gcode)
            if (entry is not None):
                return self._processExtendedGcodeEntry(entry.mode, cmd, gcode)

        # Otherwise, let the command process normally
        return None
