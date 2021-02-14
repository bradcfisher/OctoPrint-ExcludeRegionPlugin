# coding=utf-8

"""Unit tests for the RegionMixin class."""

from __future__ import absolute_import

from octoprint_excluderegion.RegionMixin import RegionMixin
from octoprint_excluderegion.Layer import Layer
from .utils import TestCase


class RegionMixinTests(TestCase):
    """Unit tests for the RegionMixin class."""

    expectedProperties = ["id", "minLayer", "maxLayer"]

    def test_default_constructor(self):
        """Test the constructor when passed no arguments."""
        unit = RegionMixin()

        self.assertIsInstance(unit, RegionMixin)
        self.assertRegex(unit.id, "^[-0-9a-fA-F]{36}$", "id should be a UUID string")
        self.assertEqual(Layer(), unit.minLayer, "minLayer should be set to the default")
        self.assertEqual(None, unit.maxLayer, "maxLayer should not be set")
        self.assertProperties(unit, RegionMixinTests.expectedProperties)

    def test_constructor_kwargs(self):
        """Test the constructor when passed keyword arguments."""
        unit = RegionMixin(
            minLayer=Layer(height=1, number=2),
            maxLayer=Layer(height=3, number=4),
            id="myTestId"
        )

        self.assertIsInstance(unit, RegionMixin)
        self.assertEqual(unit.id, "myTestId", "id should be a UUID string")
        self.assertEqual(Layer(height=1, number=2), unit.minLayer, "minLayer should match")
        self.assertEqual(Layer(height=3, number=4), unit.maxLayer, "maxLayer should match")
        self.assertProperties(unit, RegionMixinTests.expectedProperties)

    def test_copy_constructor_maxLayer_set(self):
        """Test the constructor when passed a RegionMixin instance with a maxLayer set."""
        toCopy = RegionMixin(
            minLayer=Layer(height=1, number=2),
            maxLayer=Layer(height=3, number=4),
            id="myTestId"
        )

        unit = RegionMixin(toCopy)

        self.assertIsInstance(unit, RegionMixin)
        self.assertEqual(unit.id, "myTestId", "id should be a UUID string")
        self.assertEqual(Layer(height=1, number=2), unit.minLayer, "minLayer should match")
        self.assertEqual(Layer(height=3, number=4), unit.maxLayer, "maxLayer should match")
        self.assertProperties(unit, RegionMixinTests.expectedProperties)

    def test_copy_constructor_maxLayer_not_set(self):
        """Test the constructor when passed a RegionMixin instance with a maxLayer of None."""
        toCopy = RegionMixin(
            minLayer=Layer(height=1, number=2),
            id="myTestId"
        )

        unit = RegionMixin(toCopy)

        self.assertIsInstance(unit, RegionMixin)
        self.assertEqual(unit.id, "myTestId", "id should be a UUID string")
        self.assertEqual(Layer(height=1, number=2), unit.minLayer, "minLayer should match")
        self.assertEqual(None, unit.maxLayer, "maxLayer should be None")
        self.assertProperties(unit, RegionMixinTests.expectedProperties)

    def test_constructor_exception(self):
        """Test the constructor when passed a single non-RegionMixin parameter."""
        with self.assertRaises(AssertionError):
            RegionMixin("NotARegionMixinInstance")

    def test_toDict(self):
        """Test toDict."""
        unit = RegionMixin(
            minLayer=Layer(height=1, number=2),
            maxLayer=Layer(height=3, number=4),
            id="myTestId"
        )

        result = unit.toDict()

        self.assertIsDictionary(result, "toDict should return a dict")
        self.assertProperties(result, ["minLayer", "maxLayer", "id", "type"])
        self.assertEqual(result["type"], "RegionMixin", "type should be 'RegionMixin'")

        self.assertIsDictionary(result["minLayer"], "minLayer should be a dict")
        self.assertEqual(
            {"height": 1, "number": 2, "type": "Layer"},
            result["minLayer"],
            "minLayer should have the expected properties and values"
        )
        self.assertIsDictionary(result["maxLayer"], "maxLayer should be a dict")
        self.assertEqual(
            {"height": 3, "number": 4, "type": "Layer"},
            result["maxLayer"],
            "maxLayer should have the expected properties and values"
        )

    def test_toDict_min_max_layer_none(self):
        """Test toDict when minLayer and maxLayer are None."""
        unit = RegionMixin()
        unit.minLayer = None

        result = unit.toDict()

        self.assertIsDictionary(result, "toDict should return a dict")
        self.assertProperties(result, ["minLayer", "maxLayer", "id", "type"])
        self.assertEqual(result["type"], "RegionMixin", "type should be 'RegionMixin'")

        self.assertEqual(None, result["minLayer"], "minLayer should be None")
        self.assertEqual(None, result["maxLayer"], "maxLayer should be None")

    def test_getMinHeight_minLayer_set(self):
        """Test getMinHeight."""
        unit = RegionMixin(
            minLayer=Layer(height=1, number=2),
            maxLayer=Layer(height=3, number=4)
        )

        result = unit.getMinHeight()

        self.assertEqual(result, 1, "The minHeight should be 1")

    def test_getMinHeight_minLayer_not_set(self):
        """Test getMinHeight."""
        unit = RegionMixin()
        unit.minLayer = None

        result = unit.getMinHeight()

        self.assertEqual(result, 0, "The minHeight should be 0")

    def test_getMaxHeight(self):
        """Test getMaxHeight."""
        unit = RegionMixin(
            minLayer=Layer(height=1, number=2),
            maxLayer=Layer(height=3, number=4)
        )

        result = unit.getMaxHeight()

        self.assertEqual(result, 3, "The maxHeight should be 3")

    def test_inHeightRange_max_set(self):
        """Test inHeightRange when the maxLayer is set."""
        unit = RegionMixin(
            minLayer=Layer(height=1, number=2),
            maxLayer=Layer(height=3, number=4)
        )

        self.assertFalse(unit.inHeightRange(0.9))
        self.assertTrue(unit.inHeightRange(1))
        self.assertTrue(unit.inHeightRange(2))
        self.assertTrue(unit.inHeightRange(3))
        self.assertFalse(unit.inHeightRange(3.1))

    def test_inHeightRange_max_not_set(self):
        """Test inHeightRange when the maxLayer is None."""
        unit = RegionMixin(minLayer=Layer(height=1, number=2))

        self.assertFalse(unit.inHeightRange(0.9))
        self.assertTrue(unit.inHeightRange(1))
        self.assertTrue(unit.inHeightRange(2))
        self.assertTrue(unit.inHeightRange(123456789))
