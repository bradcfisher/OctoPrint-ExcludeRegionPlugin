
from __future__ import absolute_import
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

    #def assertEquals(self, a, b, msg = None):
    #    warnings.warn("assertEquals is deprecated!", DeprecationWarning, stacklevel=2)
    #    super(TestCase, self).assertEquals(a, b, msg)

    # Ensures that only the expected properties are defined
    def assertProperties(self, unit, expectedProperties, msg=None):
        if (isinstance(unit, collections.Mapping)):
            propertiesDict = unit # Already a dict
        else:
            propertiesDict = vars(unit)

        it = unit.__class__.__name__
        if (msg != None):
            it = msg +": "+ it

        for property in expectedProperties:
            self.assertTrue(property in propertiesDict, it +" should have a property named '"+ property +"'")

        for property in iter(propertiesDict):
            self.assertTrue(property in expectedProperties, it +" has an unexpected property '"+ property +"'")


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
