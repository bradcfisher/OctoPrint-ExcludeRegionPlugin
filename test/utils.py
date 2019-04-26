
from __future__ import absolute_import
from builtins import str
import unittest
import collections

import warnings

class TestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        """
        Initialize the instance properties.

        This implementation ensures that the longMessage property is set to True so the standard
        assertion messages are prepended to any custom messages provided.
        """
        super(TestCase, self).__init__(*args, **kwargs)
        self.longMessage = True

    def _msg(self, value, defaultMsg, customMsg):
        msg = defaultMsg if (customMsg is None) else customMsg
        result = str(type(value)) + " " + str(value)
        if (msg != None):
            result = msg +": "+ result
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

    def assertProperties(self, value, expectedProperties, msg=None):
        """
        Ensure that only the expected properties are defined.

        Parameters
        ----------
        value : mixed
            The dictionary to test the properties for
        expectedProperties : list
            The property names to check
        msg : string | None
            Custom assertion error message

        Raises
        ------
        AssertionError
            If the specified value is not a dictionary, or the dictionary does not contain exactly
            the specified property key names.
        """
        msg = self._msg(value, "Object properties do not match expectations", msg)

        if (isinstance(value, collections.Mapping)):
            propertiesDict = value # Already a dict
        else:
            propertiesDict = vars(value)

        missing = []
        for property in expectedProperties:
            if (property not in propertiesDict):
              missing.append(property)

        unexpected = []
        for property in iter(propertiesDict):
            if (property not in expectedProperties):
                unexpected.append(property)

        if (len(missing) or len(unexpected)):
            sep = ": "
            if (len(missing)):
                msg = msg + sep + "Missing properties " + str(missing)
                sep = ", "

            if (len(unexpected)):
                msg = msg + sep + "Unexpected properties " + str(unexpected)

            raise AssertionError(msg)


# ==========
# Ensure calling any of the deprecated assertion methods actually raises a deprecation warning

deprecatedMethods = [
    "assertEquals", "failIfEqual", "failUnless", "assert_",
    "failIf", "failUnlessRaises", "failUnlessAlmostEqual", "failIfAlmostEqual"
]

def createDeprecationClosure(deprecatedMethod, origFn):
    def deprecationClosure(self, *args, **kwargs):
        warnings.warn("TestCase."+ deprecatedMethod +" is deprecated", DeprecationWarning, stacklevel=2)
        origFn(self, *args, **kwargs)

    deprecationClosure.__name__ = deprecatedMethod
    return deprecationClosure

for deprecatedMethod in deprecatedMethods:
    if (hasattr(TestCase, deprecatedMethod)):
        setattr(TestCase, deprecatedMethod,
            createDeprecationClosure(deprecatedMethod, getattr(TestCase, deprecatedMethod)))
