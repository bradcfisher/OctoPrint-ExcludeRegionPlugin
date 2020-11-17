# coding=utf-8
"""Module providing the CommonMixin class."""

from __future__ import absolute_import, division

import json
import re
from datetime import date, datetime

# This is a hack to determine the type of object that re.compile returns, since the type
#    "re.RegexObject" mentioned in the official Python documentation doesn't actually exist.
# Could alternatively use "re._pattern_type" (undocumented and marked private)
#    or the following in 3.6: "from typing import Pattern"
REGEX_TYPE = type(re.compile(""))


class JsonEncoder(json.JSONEncoder):
    """JSON encoder with logic for objects not serializable by default json code."""

    def default(self, obj):  # pylint: disable=W0221,E0202
        """JSON serialization logic for objects not serializable by default json code."""
        toDict = getattr(obj, "toDict", None)
        if (toDict is not None):
            return toDict()

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        if (isinstance(obj, REGEX_TYPE)):
            return obj.pattern

        return json.JSONEncoder.default(self, obj)


class CommonMixin(object):
    """Provides some common behavior methods and overloads."""

    def toDict(self):
        """
        Return a dictionary representation of this object.

        Returns
        -------
        dict
            All of the standard instance properties are included in the dictionary, with an
            additional "type" property containing the class name.
        """
        result = self.__dict__.copy()
        result['type'] = self.__class__.__name__
        return result

    def toJson(self):
        """
        Return a JSON string representation of this object.

        Returns
        -------
        string
            JSON representation of the dictionary returned by toDict()
        """
        return json.dumps(self.toDict(), cls=JsonEncoder)

    def __repr__(self):
        """
        Return a string representation of this object.

        Returns
        -------
        string
            JSON representation of the dictionary returned by toDict()
        """
        return self.toJson()

    def __eq__(self, value):
        """
        Determine whether this object is equal to another value.

        Parameters
        ----------
        value : any
            The value to test for equality

        Returns
        -------
        boolean
            True if the value is the same type and has the same property values as this instance,
            and False otherwise.
        """
        return isinstance(value, type(self)) and (self.__dict__ == value.__dict__)

    def __ne__(self, value):
        """
        Determine whether this object is not equal to another value.

        Parameters
        ----------
        value : any
            The value to test for inequality

        Returns
        -------
        boolean
            True if the value is not the same type or same property value differs when compared to
            this instance, and False otherwise.
        """
        return not self.__eq__(value)
