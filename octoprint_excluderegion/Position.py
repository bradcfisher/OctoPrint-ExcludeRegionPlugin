# coding=utf-8
"""Module providing the Position class."""

from __future__ import absolute_import
from .CommonMixin import CommonMixin
from .AxisPosition import AxisPosition


class Position(CommonMixin):
    """
    Encapsulates the current position of all the axes.

    Attributes
    ----------
    X_AXIS : AxisPosition
        The X axis position state.  This position is initially unknown/None by default.
    Y_AXIS : AxisPosition
        The Y axis position state.  This position is initially unknown/None by default.
    Z_AXIS : AxisPosition
        The Z axis position state.  This position is initially unknown/None by default.
    E_AXIS : AxisPosition
        The E axis position state.  The extruder position defaults to 0
    """

    def __init__(self, position=None):
        """
        Initialize the instance properties.

        Parameters
        ----------
        position : Position | None
            If a Position is provided, its property values will be cloned to the new instance.
        """
        # pylint: disable=invalid-name
        if (position is None):
            self.X_AXIS = AxisPosition()
            self.Y_AXIS = AxisPosition()
            self.Z_AXIS = AxisPosition()
            self.E_AXIS = AxisPosition(0)
        else:
            assert isinstance(position, Position), "position must be a Position instance"
            self.X_AXIS = AxisPosition(position.X_AXIS)
            self.Y_AXIS = AxisPosition(position.Y_AXIS)
            self.Z_AXIS = AxisPosition(position.Z_AXIS)
            self.E_AXIS = AxisPosition(position.E_AXIS)

    def setUnitMultiplier(self, unitMultiplier):
        """
        Set the conversion factor from logical units to native units for all of the axes (G20, G21).

        Parameters
        ----------
        unitMultiplier : float
            The new unit multiplier to use for converting between logical and native units to assign
            to all of the axes.
        """
        self.X_AXIS.setUnitMultiplier(unitMultiplier)
        self.Y_AXIS.setUnitMultiplier(unitMultiplier)
        self.Z_AXIS.setUnitMultiplier(unitMultiplier)
        self.E_AXIS.setUnitMultiplier(unitMultiplier)

    def setPositionAbsoluteMode(self, absolute):
        """
        Set the absoluteMode property for the X, Y and Z axes (G90, G91).

        Parameters
        ----------
        absoluteMode : boolean
            The new value to assign to the absoluteMode property of the X, Y and Z axes
        """
        self.X_AXIS.setAbsoluteMode(absolute)
        self.Y_AXIS.setAbsoluteMode(absolute)
        self.Z_AXIS.setAbsoluteMode(absolute)

    def setExtruderAbsoluteMode(self, absolute):
        """
        Set the absoluteMode property for the E axis (M82, M83).

        Parameters
        ----------
        absoluteMode : boolean
            The new value to assign to the absoluteMode property of the E axis
        """
        self.E_AXIS.setAbsoluteMode(absolute)
