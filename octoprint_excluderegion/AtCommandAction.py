# coding=utf-8
"""Module providing the AtCommandAction class."""

from __future__ import absolute_import

import re

from .CommonMixin import CommonMixin

ENABLE_EXCLUSION = "enable_exclusion"
DISABLE_EXCLUSION = "disable_exclusion"
# CLEAR_REGIONS = "clear_regions"
# ADD_REGION = "add_region"


# pylint: disable=too-few-public-methods
class AtCommandAction(CommonMixin):
    """
    Configuration for a custom At-Command action configuration.

    Attributes
    ----------
    command : string
        The At-Command to trigger for.
    parameterPattern : string
        Optional regex pattern to match against the command parameter(s)
    action : string
        The action to perform.  May be one of ENABLE_EXCLUSION or DISABLE_EXCLUSION.
    description : string
        Description of the action.
    """

    def __init__(self, command, parameterPattern, action, description):
        """
        Initialize the instance properties.

        Parameters
        ----------
        command : string
            The At-Command to trigger for.
        parameterPattern : string
            Optional regex pattern to match against the command parameter(s)
        action : string
            The action to perform.  May be one of ENABLE_EXCLUSION or DISABLE_EXCLUSION.
        description : string
            Description of the action.
        """
        assert command, "You must provide a value for command"
        assert action in (ENABLE_EXCLUSION, DISABLE_EXCLUSION), \
            "Invalid action parameter value"

        self.command = command
        self.parameterPattern = None if (parameterPattern is None) else re.compile(parameterPattern)
        self.action = action
        self.description = description

    def matches(self, command, parameters):
        """
        Determine if this instance matches the specified At-Command and parameters.

        Parameters
        ----------
        command : string
            The At-Command to match
        parameters : string
            The parameters to match

        Returns
        -------
        boolean
            True if the command and parameters match this instance, False otherwise.
        """
        if (self.command == command):
            if (parameters is None):
                parameters = ""

            return (self.parameterPattern is None) or self.parameterPattern.match(parameters)

        return False
