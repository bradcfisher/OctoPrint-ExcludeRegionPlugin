# coding=utf-8
"""Module providing the RetractionState class."""

from __future__ import absolute_import
import re
from .CommonMixin import CommonMixin

# Regular expression for extracting the parameters from a Gcode command
GCODE_PARAMS_REGEX = re.compile("^[A-Za-z][0-9]+(?:\\.[0-9]+)?\\s*(.*)$")


class RetractionState(CommonMixin):
    """
    Information for a retraction that may need to be restored later.

    Attributes
    ----------
    recoverExcluded : boolean
        Whether the recovery for this retraction was excluded or not.  If it was excluded, it will
        need to be processed later.
    firmwareRetract : boolean
        This was a firmware retraction (G10)
    extrusionAmount : float | None
        Amount of filament to extrude when recovering a previous retraction.  Will be None if
        firmwareRetract is True.
    feedRate : float
        Feed rate for filament recovery.  Will be None if firmwareRetract is True.
    originalCommand : string
        Original retraction gcode
    """

    def __init__(
            self, firmwareRetract=None, extrusionAmount=None, feedRate=None, originalCommand=None
    ):
        """
        Initialize the instance properties.

        Parameters
        ----------
        firmwareRetract : boolean
            Whether this was a firmware retraction (G10) or not (G0/G1 with no XYZ move)
        extrusionAmount : float | None
            Amount of filament to extrude when recovering a previous retraction.  Will be None if
            firmwareRetract is True.
        feedRate : float
            Feed rate for filament recovery.  Will be None if firmwareRetract is True.
        originalCommand : string
            The original Gcode command for the retraction
        """
        nonFirmwareRetract = (extrusionAmount is not None) or (feedRate is not None)
        if (firmwareRetract is not None):
            if (nonFirmwareRetract):
                raise ValueError(
                    "You cannot provide a value for extrusionAmount or feedRate if " +
                    "firmwareRetract is specified"
                )
        elif (not nonFirmwareRetract):
            raise ValueError(
                "You must provide a value for firmwareRetract or extrusionAmount and feedRate"
            )
        elif ((extrusionAmount is None) or (feedRate is None)):
            raise ValueError(
                "You must provide values for both extrusionAmount and feedRate together"
            )

        self.recoverExcluded = False
        self.firmwareRetract = firmwareRetract
        self.extrusionAmount = extrusionAmount
        self.feedRate = feedRate
        self.originalCommand = originalCommand

    def addRetractCommands(self, position, returnCommands=None):
        """
        Add the necessary commands to perform a retraction for this instance.

        Parameters
        ----------
        position : Position
            The tool position state to apply the retraction to.
        returnCommands : List of gcode commands
            The Gcode command list to append the new command(s) to.  If None, a new list will be
            created.

        Returns
        -------
        List of gcode commands
            The Gcode command list provided in *returnCommands* or a newly created list.  The
            retraction command(s) will be appended to the returned list.
        """
        return self._addCommands(1, position, returnCommands)

    def addRecoverCommands(self, position, returnCommands=None):
        """
        Add the necessary commands to perform a recovery for this instance.

        Parameters
        ----------
        position : Position
            The tool position state to apply the retraction to.
        returnCommands : List of gcode commands
            The Gcode command list to append the new command(s) to.  If None, a new list will be
            created.

        Returns
        -------
        List of gcode commands
            The Gcode command list provided in *returnCommands* or a newly created list.  The
            recovery command(s) will be appended to the returned list.
        """
        return self._addCommands(-1, position, returnCommands)

    def _addCommands(self, direction, position, returnCommands):
        """
        Add the necessary commands to perform a retraction or recovery for this instance.

        Parameters
        ----------
        direction : { 1, -1 }
            For non-firmware retractions, the direction multiplier to apply to the extrusion
            amount.  Use 1 for retract, -1 for recover.
        position : Position
            The tool position state to apply the retraction to.
        returnCommands : List of gcode commands
            The Gcode command list to append the new command(s) to.  If None, a new list will be
            created.

        Returns
        -------
        List of gcode commands
            The Gcode command list provided in *returnCommands* or a newly created list.  The
            new command(s) will be appended to the returned list.
        """
        if (returnCommands is None):
            returnCommands = []

        if (self.firmwareRetract):
            cmd = "G11" if (direction == -1) else "G10"
            params = GCODE_PARAMS_REGEX.sub("\\1", self.originalCommand)
            if (params):
                cmd += " " + params

            returnCommands.append(cmd)
        else:
            amount = self.extrusionAmount * direction
            eAxis = position.E_AXIS
            eAxis.current += amount

            returnCommands.append(
                # Set logical extruder position
                "G92 E{e}".format(e=eAxis.nativeToLogical())
            )

            eAxis.current -= amount

            returnCommands.append(
                "G1 F{f} E{e}".format(
                    e=eAxis.nativeToLogical(),
                    f=self.feedRate / eAxis.unitMultiplier
                )
            )

        return returnCommands
