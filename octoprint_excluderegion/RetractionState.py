# coding=utf-8
"""Module providing the RetractionState class."""

from __future__ import absolute_import, division
import re
from .CommonMixin import CommonMixin

# Regular expression for extracting the parameters from a Gcode command
GCODE_PARAMS_REGEX = re.compile("^[A-Za-z][0-9]+(?:\\.[0-9]+)?\\s*(.*)$")


class RetractionState(CommonMixin):
    """
    Information for a retraction that may need to be restored later.

    Attributes
    ----------
    originalCommand : string
        Original retraction gcode
    firmwareRetract : boolean
        This was a firmware retraction (G10)
    extrusionAmount : float | None
        Amount of filament to extrude when recovering a previous retraction, in millimeters.  Will
        be None if firmwareRetract is True and a float otherwise.
    feedRate : float | None
        Feed rate in millimeters/minute for filament recovery.  Will be None if firmwareRetract
        is True and a float otherwise.
    recoverExcluded : boolean
        Whether the recovery for this retraction was excluded or not (default False).  If it was
        excluded, it will need to be processed later.
    allowCombine : boolean
        Whether this retraction should be combined with subsequent retractions or not.  Retractions
        may be combined as long as there is no extrusion/recovery executed between the two
        retractions.
    """

    def __init__(
            self, originalCommand, firmwareRetract, extrusionAmount=None, feedRate=None
    ):
        """
        Initialize the instance properties.

        Parameters
        ----------
        originalCommand : string
            The original Gcode command for the retraction
        firmwareRetract : boolean
            Whether this was a firmware retraction (G10) or not (G0/G1 with no XYZ move)
        extrusionAmount : float | None
            Amount of filament to extrude when recovering a previous retraction, in millimeters.
            Must be None if firmwareRetract is True, and a float otherwise.
        feedRate : float | None
            Feed rate in millimeters/minute for filament recovery.  Must be None if firmwareRetract
            is True, and a float otherwise.
        """
        if (firmwareRetract):
            if (extrusionAmount is not None) or (feedRate is not None):
                raise ValueError(
                    "You cannot provide a value for extrusionAmount or feedRate if " +
                    "firmwareRetract is specified"
                )
        elif ((extrusionAmount is None) or (feedRate is None)):
            raise ValueError(
                "You must provide values for both extrusionAmount and feedRate together"
            )

        self.recoverExcluded = False
        self.allowCombine = True
        self.firmwareRetract = firmwareRetract
        self.extrusionAmount = extrusionAmount
        self.feedRate = feedRate
        self.originalCommand = originalCommand

    def combine(self, other, logger):
        """
        Combine the retraction amount from the specified other instance with this instance.

        Parameters
        ----------
        other : RetractionState
            The other instance to combine with this instance.

        Returns
        -------
            This instance
        """
        if (self.allowCombine):
            if (self.firmwareRetract == other.firmwareRetract):
                if (not self.firmwareRetract):
                    self.extrusionAmount += other.extrusionAmount
            else:
                logger.warn(
                    "Encountered mix of firmware and non-firmware retractions.  " +
                    "Extruder position may not be tracked correctly."
                )
        else:
            logger.warn("Cannot combine retractions, since allowCombine = False")

        return self

    def generateRetractCommands(self, position):
        """
        Add the necessary commands to perform a retraction for this instance.

        Parameters
        ----------
        position : Position
            The tool position state to apply the retraction to.

        Returns
        -------
        List of gcode commands
            A list containing the retraction command(s) to execute.
        """
        return self._addCommands(1, position)

    def generateRecoverCommands(self, position):
        """
        Add the necessary commands to perform a recovery for this instance.

        Parameters
        ----------
        position : Position
            The tool position state to apply the retraction to.

        Returns
        -------
        List of gcode commands
            A list containing the recovery command(s) to execute.
        """
        return self._addCommands(-1, position)

    def _addCommands(self, direction, position):
        """
        Add the necessary commands to perform a retraction or recovery for this instance.

        Parameters
        ----------
        direction : { 1, -1 }
            For non-firmware retractions, the direction multiplier to apply to the extrusion
            amount.  Use 1 for retract, -1 for recover.
        position : Position
            The tool position state to apply the retraction to.

        Returns
        -------
        List of gcode commands
            A list containing the new command(s).
        """
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

            # Use "G1" over "G0", since an extrusion amount is being supplied
            returnCommands.append(
                "G1 F{f} E{e}".format(
                    e=eAxis.nativeToLogical(),
                    f=self.feedRate / eAxis.unitMultiplier
                )
            )

        return returnCommands
