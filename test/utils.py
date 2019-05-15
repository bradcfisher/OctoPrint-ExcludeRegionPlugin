# coding=utf-8
"""Provides an enhanced TestCase class to extend when implementing unit tests."""

from __future__ import absolute_import
from builtins import str

import collections
import unittest
import warnings

from callee import Matcher

from octoprint_excluderegion.Position import Position


class FloatAlmostEqual(Matcher):
    """callee.Matcher subclass to test if a mock.call argument is almost equal to a value."""

    def __init__(self, value, places=None, delta=None):
        """Initialize object properties."""
        super(FloatAlmostEqual, self).__init__()

        value = float(value)
        if (delta is None):
            places = 7 if (places is None) else int(places)
        elif (places is not None):
            raise TypeError("Cannot specify both places and delta")

        if (delta is None):
            value = round(value, places)
            self._comparison = lambda other: (round(other, places) == value)
            self._reprStr = "<equal to %s rounded to %s places>" % (value, places)
        else:
            delta = abs(float(delta))
            minValue = value - delta
            maxValue = value + delta
            self._comparison = lambda other: minValue <= other <= maxValue
            self._reprStr = "<between %s and %s>" % (minValue, maxValue)

    def match(self, value):
        """Apply the comparison function to the provided value."""
        return self._comparison(value)

    def __repr__(self):
        """Return a string representation of this object."""
        return self._reprStr


class TestCase(unittest.TestCase):
    """Enhanced untttest.TestCase subclass providing additional asserts and deprecation warnings."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the instance properties.

        This implementation ensures that the longMessage property is set to True so the standard
        assertion messages are prepended to any custom messages provided.
        """
        super(TestCase, self).__init__(*args, **kwargs)
        self.longMessage = True

    @staticmethod
    def _msg(value, defaultMsg, customMsg):
        msg = defaultMsg if (customMsg is None) else customMsg
        result = str(type(value)) + " " + str(value)
        if (msg is not None):
            result = msg + ": " + result
        return result

    def assertIsDictionary(self, value, msg=None):
        """
        Ensure that the specified value is a dictionary-like collection.

        Parameters
        ----------
        value : mixed
            The value to test
        msg : string | None
            Custom assertion error message

        Raises
        ------
        AssertionError
            If the specified value is not a dictionary-like object.
        """
        if (not isinstance(value, collections.Mapping)):
            raise AssertionError(self._msg(value, "Value is not a dictionary", msg))

    def assertIsString(self, value, msg=None):
        """
        Ensure that the specified value is a string value (str or unicode instance).

        Parameters
        ----------
        value : mixed
            The value to test
        msg : string | None
            Custom assertion error message

        Raises
        ------
        AssertionError
            If the specified value is not a string.
        """
        if (not isinstance(value, str)):
            raise AssertionError(self._msg(value, "Value is not a string", msg))

    def assertProperties(self, value, expectedProperties, required=True, exclusive=True, msg=None):
        """
        Ensure a dictionary has specific properties defined and/or doesn't have other properties.

        Parameters
        ----------
        value : mixed
            The dictionary to test the properties for
        expectedProperties : list
            The property names to check
        required : boolean
            Whether all of the specified properties must be present or not.  If True (the default),
            an AssertionError will be raised if any of the expectedProperties are not found.
        exclusive : boolean
            Whether only the specified properties are permitted.  If True (the default), an
            AssertionError will be raised if any property other than one in expectedProperties is
            encountered.
        msg : string | None
            Custom assertion error message

        Raises
        ------
        AssertionError
            If the specified value is not a dictionary, or the dictionary does not contain exactly
            the specified property key names.
        """
        if (not (required or exclusive)):
            raise ValueError("You must specify True for at least one of required or exclusive")

        msg = self._msg(value, "Object properties do not match expectations", msg)

        if (isinstance(value, collections.Mapping)):
            propertiesDict = value  # Already a dict
        else:
            propertiesDict = vars(value)

        missing = []
        if (required):
            for prop in expectedProperties:
                if (prop not in propertiesDict):
                    missing.append(prop)

        unexpected = []
        if (exclusive):
            for prop in iter(propertiesDict):
                if (prop not in expectedProperties):
                    unexpected.append(prop)

        if (missing or unexpected):
            sep = ": "
            if (missing):
                msg = msg + sep + "Missing properties " + str(missing)
                sep = ", "

            if (unexpected):
                msg = msg + sep + "Unexpected properties " + str(unexpected)

            raise AssertionError(msg)


def create_position(x=None, y=None, z=None, extruderPosition=0, unitMultiplier=1):
    """
    Create a new Position object with a specified position and unit multiplier.

    Parameters
    ----------
    x : float | None
        The x coordinate value for the position, in native units.
    y : float | None
        The x coordinate value for the position, in native units.
    z : float | None
        The x coordinate value for the position, in native units.
    extruderPosition : float
        The extruder value for the position, in native units.
    unitMultiplier : float
        The unit multiplier to apply to the position.
    """
    position = Position()

    if (x is not None):
        position.X_AXIS.current = x

    if (y is not None):
        position.Y_AXIS.current = y

    if (z is not None):
        position.Z_AXIS.current = z

    if (extruderPosition is not None):
        position.E_AXIS.current = extruderPosition

    if (unitMultiplier is not None):
        position.setUnitMultiplier(unitMultiplier)

    return position


# ==========
# Ensure calling any of the deprecated assertion methods actually raises a deprecation warning

DEPRECATED_METHODS = [
    "assertEquals", "failIfEqual", "failUnless", "assert_",
    "failIf", "failUnlessRaises", "failUnlessAlmostEqual", "failIfAlmostEqual"
]


def _apply_deprecation_closures():
    def _create_deprecation_closure(deprecatedMethod, origFn):
        def deprecation_closure(self, *args, **kwargs):
            warnings.warn(
                "TestCase." + deprecatedMethod + " is deprecated", DeprecationWarning, stacklevel=2
            )
            origFn(self, *args, **kwargs)

        deprecation_closure.__name__ = deprecatedMethod
        return deprecation_closure

    for deprecatedMethod in DEPRECATED_METHODS:
        if (hasattr(TestCase, deprecatedMethod)):
            setattr(
                TestCase,
                deprecatedMethod,
                _create_deprecation_closure(deprecatedMethod, getattr(TestCase, deprecatedMethod))
            )


_apply_deprecation_closures()
