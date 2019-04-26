# coding=utf-8

from __future__ import absolute_import

import json
from .utils import TestCase
from octoprint_excluderegion.CommonMixin import CommonMixin, JsonEncoder
from datetime import date, datetime

class MyUnserializableClass:
    """Class that doesn't extend CommonMixin or define a toDict method"""
    def __init__(self):
        pass

class MyClass(CommonMixin):
    def __init__(self, a, b):
        self.a = a
        self.b = b

class CommonMixinTests(TestCase):
    def __init__(self, *args, **kwargs):
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
        unit = MyClass(self.testDate1, self.testDict).toDict()

        self.assertIsDictionary(unit, "toDict should return a dict")
        self.assertProperties(unit, ["a", "b", "type"])
        self.assertEqual(unit["type"], "MyClass", "type should be 'MyClass'")
        self.assertIsInstance(unit["a"], date, "'a' should be a date")
        self.assertEqual(unit["a"], self.testDate1, "'a' should be the expected date")
        self.assertIsDictionary(unit["b"], "'b' should be a dictionary")
        self.assertEqual(unit["b"], self.testDict, "'b' should have the expected properties and values")

    def test_repr(self):
        unit = MyClass(self.testDate1, self.testDict)
        reprStr = unit.__repr__()
        reprDict = json.loads(reprStr)
        self.assertEqual(
            reprDict,
            { "a": self.testDate1String, "b": self.testDictExpected, "type": "MyClass" }
        )

    def test_toJson_1(self):
        unit = MyClass(self.testDate1, self.testDict)
        jsonStr = unit.toJson()
        reprDict = json.loads(jsonStr)
        self.assertEqual(
            reprDict,
            { "a": self.testDate1String, "b": self.testDictExpected, "type": "MyClass" }
        )

    def test_toJson_2(self):
        unit = MyClass(1, self.testDateTime)
        jsonStr = unit.toJson()
        reprDict = json.loads(jsonStr)
        self.assertEqual(
            reprDict,
            { "a": 1, "b": self.testDateTimeString, "type": "MyClass" }
        )

    def _assert_eq_and_ne(self, it, other, expectedEquality, msg):
        self.assertEqual(it == other, expectedEquality,
            "it should "+ ("" if expectedEquality else "not ") +"== " + msg)
        self.assertEqual(it != other, not expectedEquality,
            "it should "+ ("not " if expectedEquality else "") +"!= " + msg)

    def test_eq_and_ne(self):
        unit = MyClass(1, 2)

        self._assert_eq_and_ne(unit, unit, True, "itself")
        self._assert_eq_and_ne(unit, MyClass(1, 2), True,
            "another instance with the same property values")

        self._assert_eq_and_ne(unit, None, False, "None")
        self._assert_eq_and_ne(unit, MyClass(0, 2), False,
            "another instance with a different 'a' value")
        self._assert_eq_and_ne(unit, MyClass(1, 0), False,
            "another instance with a different 'b' value")

    def test_JsonEncoder_defaultTypeError(self):
        unit = JsonEncoder()
        with self.assertRaises(TypeError):
            unit.default(MyUnserializableClass())

    def test_JsonEncoder_toDict(self):
        unit = JsonEncoder()
        self.assertEqual(unit.default(MyClass(1, 2)), {"a": 1, "b": 2, "type": "MyClass"})

    def test_JsonEncoder_date(self):
        unit = JsonEncoder()
        self.assertEqual(unit.default(self.testDate1), self.testDate1String)

    def test_JsonEncoder_datetime(self):
        unit = JsonEncoder()
        self.assertEqual(unit.default(self.testDateTime), self.testDateTimeString)
