# coding=utf-8

from __future__ import absolute_import

import json
from .utils import TestCase
from octoprint_excluderegion.CommonMixin import CommonMixin


class MyClass(CommonMixin):
    def __init__(self, a, b):
        self.a = a
        self.b = b

class CommonMixinTests(TestCase):
    def test_toDict(self):
        unit = MyClass(1, 2).toDict()

        self.assertIsInstance(unit, dict, "toDict should return a dict")
        self.assertProperties(unit, ["a", "b", "type"])
        self.assertEqual(unit["type"], "MyClass", "type should be 'MyClass'")
        self.assertEqual(unit["a"], 1, "'a' should be 1")
        self.assertEqual(unit["b"], 2, "'b' should be 2")

    def test_repr(self):
        unit = MyClass(1, 2)
        reprStr = unit.__repr__()
        reprDict = json.loads(reprStr)
        self.assertEqual(unit.toDict(), reprDict)

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
