# coding=utf-8
"""Module providing the ExcludedGcode class."""

from __future__ import absolute_import
from .CommonMixin import CommonMixin

EXCLUDE_ALL = "exclude"
EXCLUDE_EXCEPT_FIRST = "first"
EXCLUDE_EXCEPT_LAST = "last"
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
        self.gcode = gcode
        self.mode = mode
        self.description = description
