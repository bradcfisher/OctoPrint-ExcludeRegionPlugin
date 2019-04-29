# coding=utf-8
"""Unit tests for the CommonMixin class."""

from __future__ import absolute_import

import json
from datetime import date, datetime
from octoprint_excluderegion.CommonMixin import CommonMixin, JsonEncoder
from .utils import TestCase


class MyUnserializableClass(object):  # pylint: disable=too-few-public-methods
    """Class that doesn't extend CommonMixin or define a toDict method."""

    def __init__(self):
        """No operation."""
        pass


class MyClass(CommonMixin):  # pylint: disable=too-few-public-methods
    """Class that extends CommonMixin."""

    def __init__(self, a, b):
        """Initialize the properties."""
        # pylint: disable=invalid-name
        self.a = a
        self.b = b


class CommonMixinTests(TestCase):  # pylint: disable=too-many-instance-attributes
    """Unit tests for the CommonMixin class."""

    def __init__(self, *args, **kwargs):
        """Perform property initialization."""
        super(CommonMixinTests, self).__init__(*args, **kwargs)

        self.testDate1 = date(2010, 1, 31)
        self.testDate1String = "2010-01-31"

        self.testDate2 = date(1999, 12, 31)
        self.testDate2String = "1999-12-31"

        self.testDateTime = datetime(2000, 1, 15, 1, 2, 3)
        self.testDateTimeString = "2000-01-15T01:02:03"

        self.testDict = {
            "date": self.testDate2,
            "string": self.testDate2String
        }
        self.testDictExpected = {
            "date": self.testDate2String,
            "string": self.testDate2String
        }

    def test_toDict(self):
        """Test the toDict method."""
        unit = MyClass(self.testDate1, self.testDict).toDict()

        self.assertIsDictionary(unit, "toDict should return a dict")
        self.assertProperties(unit, ["a", "b", "type"])
        self.assertEqual(unit["type"], "MyClass", "type should be 'MyClass'")
        self.assertIsInstance(unit["a"], date, "'a' should be a date")
        self.assertEqual(unit["a"], self.testDate1, "'a' should be the expected date")
        self.assertIsDictionary(unit["b"], "'b' should be a dictionary")
        self.assertEqual(
            unit["b"], self.testDict, "'b' should have the expected properties and values"
        )

    def test_repr(self):
        """Test the repr method."""
        unit = MyClass(self.testDate1, self.testDict)
        reprStr = unit.__repr__()
        reprDict = json.loads(reprStr)
        self.assertEqual(
            reprDict,
            {"a": self.testDate1String, "b": self.testDictExpected, "type": "MyClass"}
        )

    def test_toJson_1(self):
        """Test the toJson method with a nested date and dictionary."""
        unit = MyClass(self.testDate1, self.testDict)
        jsonStr = unit.toJson()
        reprDict = json.loads(jsonStr)
        self.assertEqual(
            reprDict,
            {"a": self.testDate1String, "b": self.testDictExpected, "type": "MyClass"}
        )

    def test_toJson_2(self):
        """Test the toJson method with simple type and a nested date time."""
        unit = MyClass(1, self.testDateTime)
        jsonStr = unit.toJson()
        reprDict = json.loads(jsonStr)
        self.assertEqual(
            reprDict,
            {"a": 1, "b": self.testDateTimeString, "type": "MyClass"}
        )

    def _assert_eq_and_ne(self, aVal, otherVal, expectedEquality, msg):
        """Apply assertions for testing the __eq__ and __ne__ methods."""
        self.assertEqual(
            aVal == otherVal, expectedEquality,
            "it should " + ("" if expectedEquality else "not ") + "== " + msg
        )
        self.assertEqual(
            aVal != otherVal, not expectedEquality,
            "it should " + ("not " if expectedEquality else "") + "!= " + msg
        )

    def test_eq_and_ne(self):
        """Test the __eq__ and __ne__ methods."""
        unit = MyClass(1, 2)

        self._assert_eq_and_ne(unit, unit, True, "itself")
        self._assert_eq_and_ne(
            unit, MyClass(1, 2), True,
            "another instance with the same property values"
        )

        self._assert_eq_and_ne(unit, None, False, "None")
        self._assert_eq_and_ne(
            unit, MyClass(0, 2), False,
            "another instance with a different 'a' value"
        )
        self._assert_eq_and_ne(
            unit, MyClass(1, 0), False,
            "another instance with a different 'b' value"
        )

    def test_JsonEncoder_defaultTypeError(self):
        """Test that the JsonEncoder calls the super class to raise a TypeError."""
        unit = JsonEncoder()
        with self.assertRaises(TypeError):
            unit.default(MyUnserializableClass())

    def test_JsonEncoder_toDict(self):
        """Test that the JsonEncoder invokes the toDict method if it's defined."""
        unit = JsonEncoder()
        self.assertEqual(unit.default(MyClass(1, 2)), {"a": 1, "b": 2, "type": "MyClass"})

    def test_JsonEncoder_date(self):
        """Test that the JsonEncoder encodes dates as ISO date strings."""
        unit = JsonEncoder()
        self.assertEqual(unit.default(self.testDate1), self.testDate1String)

    def test_JsonEncoder_datetime(self):
        """Test that the JsonEncoder encodes date times as ISO date time strings."""
        unit = JsonEncoder()
        self.assertEqual(unit.default(self.testDateTime), self.testDateTimeString)
