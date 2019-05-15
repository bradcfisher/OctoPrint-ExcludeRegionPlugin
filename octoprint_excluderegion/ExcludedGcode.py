# coding=utf-8
"""Module providing the ExcludedGcode class."""

from __future__ import absolute_import
from .CommonMixin import CommonMixin

# Filter out the command when in an exclude region and do not send it to the printer.
EXCLUDE_ALL = "exclude"

# Execute the first instance of a command from an exclude region when exiting the region.
EXCLUDE_EXCEPT_FIRST = "first"

# Execute the last instance of a command from an exclude region when exiting the region.
EXCLUDE_EXCEPT_LAST = "last"

# Execute command with last encountered value of each argument when exiting an exclude region.
EXCLUDE_MERGE = "merge"


# pylint: disable=too-few-public-methods
class ExcludedGcode(CommonMixin):
    """
    Configuration for a custom excluded Gcode command.

    Attributes
    ----------
    gcode : string
        The gcode to exclude (e.g. "G4")
    mode : string
        The type of exclusion processing to perform.  One of the following constant values:
        EXCLUDE_ALL, EXCLUDE_EXCEPT_FIRST, EXCLUDE_EXCEPT_LAST, EXCLUDE_MERGE
    description : string
        Description of the exclusion.
    """

    def __init__(self, gcode, mode, description):
        """
        Initialize the instance properties.

        Parameters
        ----------
        gcode : string
            The gcode to exclude (e.g. "G4").
        mode : string
            The type of exclusion processing to perform.  One of the following constant values:
            EXCLUDE_ALL, EXCLUDE_EXCEPT_FIRST, EXCLUDE_EXCEPT_LAST, EXCLUDE_MERGE
        description : string
            Description of the exclusion.
        """
        assert gcode, "You must provide a value for gcode"
        assert mode in (EXCLUDE_ALL, EXCLUDE_EXCEPT_FIRST, EXCLUDE_EXCEPT_LAST, EXCLUDE_MERGE), \
            "Invalid mode parameter value"

        self.gcode = gcode
        self.mode = mode
        self.description = description
