# coding=utf-8
"""Module providing the AxisPosition class."""

from __future__ import absolute_import
from .CommonMixin import CommonMixin

# Possible enhancements:
#   - Implement physical limits (min/max) & software endstop limits? update_software_endstops?
#   - Support homing to specific offset (baseHomePos?, e.g. home to center of cartesian), or
#       homing to max instead of min?


class AxisPosition(CommonMixin):
    """
    State information associated with an axis (X, Y, Z, or E).

    Attributes
    ----------
    current : float | None
        The current position value, in mm relative to the physical bed origin.  If None, the
        position is unknown
    homeOffset : float
        The home offset value (M206), in mm relative to the physical bed origin
    offset : float
        The offset value, in mm relative to the homeOffset
    absoluteMode : boolean
        Whether to use absolute mode (True) or relative mode (False)
    unitMultiplier : float
        Multiplier for conversion between logical units (inches, etc) and native units (mm)
    """

    def __init__(
            self,
            current=None,
            homeOffset=0,
            offset=0,
            absoluteMode=True,
            unitMultiplier=1
    ):
        """
        Initialize the instance properties.

        Parameters
        ----------
        current : float | None | AxisPosition
            The current position value, in mm relative to the physical bed origin.  If None, the
            position is unknown.  If this parameter is an AxisPosition instance, all of the property
            values from the provided instances will be copied to the new instance and the remaining
            parameters are ignored.
        homeOffset : float
            The home offset value (M206), in mm relative to the physical bed origin.
        offset : float
            The offset value, in mm relative to the homeOffset
        absoluteMode : boolean
            Whether to use absolute mode (True) or relative mode (False)
        unitMultiplier : float
            Multiplier for conversion between logical units (inches, etc) and native units (mm)
        """
        if (isinstance(current, AxisPosition)):
            self.homeOffset = current.homeOffset
            self.offset = current.offset
            self.absoluteMode = current.absoluteMode
            self.unitMultiplier = current.unitMultiplier
            self.current = current.current
        else:
            # Current value and offsets are stored internally in mm
            self.current = current
            self.homeOffset = homeOffset
            self.offset = offset
            self.absoluteMode = absoluteMode
            # Conversion factor from logical units (e.g. inches) to mm
            self.unitMultiplier = unitMultiplier

    def setAbsoluteMode(self, absoluteMode=True):
        """
        Set the absoluteMode property (G90, G91, M82, M83).

        Parameters
        ----------
        absoluteMode : boolean
            The new value to assign to the absoluteMode property.
        """
        self.absoluteMode = absoluteMode

    def setLogicalOffsetPosition(self, offset):
        """
        Update the axis coordinate space offset (G92).

        This method updates the offset to the delta between the current position and the
        specified logical position.

        Parameters
        ----------
        offset : float
            The new offset position, in logical units.  The value of the absoluteMode property will
            determine whether this value is interpreted as an absolute or relative position.
        """
        self.offset += self.logicalToNative(offset) - self.current

    def setHomeOffset(self, homeOffset):
        """
        Set the home offset (M206).

        Parameters
        ----------
        homeOffset : float
            The new home offset in logical units, relative to the physical bed origin.
        """
        oldHomeOffset = self.homeOffset
        self.homeOffset = homeOffset * self.unitMultiplier
        self.current += oldHomeOffset - self.homeOffset

    def setHome(self):
        """
        Reset the axis to the home position (G28).

        Following a call to this method, the current and offset properties will be 0.
        """
        # Marlin does the following:
        #  position_shift = 0                   // equivalent to offset (G92)
        #  current_position = base_home_pos()   // base_home_pos() should be 0 for cartesian or
        #                                       //   delta, unless configured to home to center on
        #                                       //   cartesian.

        self.current = 0
        self.offset = 0

    def setUnitMultiplier(self, unitMultiplier):
        """
        Set the conversion factor from logical units (inches, etc) to native units (mm) (G20, G21).

        Parameters
        ----------
        unitMultiplier : float
            The new unit multiplier to use for converting between logical and native units.
        """
        self.unitMultiplier = unitMultiplier

    def setLogicalPosition(self, position):
        """
        Set the position given a location in logical units.

        Parameters
        ----------
        position : float | None
            The new logical position value to assign.  The value of the absoluteMode property will
            determine whether this position is interpreted as an absolute or relative value.
            If None, the current position will not be modified.

        Returns
        -------
        float
            The new value of the 'current' property (in native units).
        """
        if (position is not None):
            self.current = self.logicalToNative(position)

        return self.current

    def logicalToNative(self, value=None, absoluteMode=None):
        """
        Convert the value from logical units (inches, etc) to native units (mm).

        This method takes into account any offsets in effect as well as whether the axis is in
        relative or absolute positioning mode.

        Parameters
        ----------
        value : float | None
            The logical position value to convert to a native position.  If None, the current native
            position is returned.
        absoluteMode : boolean | None
            Whether the provided value should be interpreted as an absolute or relative position.
            If None, the value of the absoluteMode property will be used.

        Returns
        -------
        float
            The computed native position value.
        """
        if (value is None):
            return self.current

        value *= self.unitMultiplier

        if (absoluteMode is None):
            absoluteMode = self.absoluteMode

        if (absoluteMode):
            value += self.offset + self.homeOffset
        else:
            value += self.current

        return value

    def nativeToLogical(self, value=None, absoluteMode=None):
        """
        Convert the value from native units (mm) to logical units (inches, etc).

        This method takes into account any offsets in effect as well as whether the axis is in
        relative or absolute positioning mode.

        Parameters
        ----------
        value : float | None
            The native position value to convert to a logical position.  If None, the current
            logical position will be returned.
        absoluteMode : boolean | None
            Whether the provided value should be interpreted as an absolute or relative position.
            If None, the value of the absoluteMode property will be used.

        Returns
        -------
        float
            The computed logical position value.
        """
        if (value is None):
            value = self.current
            absoluteMode = True
        else:
            if (absoluteMode is None):
                absoluteMode = self.absoluteMode

        if (absoluteMode):
            value -= self.offset + self.homeOffset
        else:
            value -= self.current

        return value / self.unitMultiplier
