# coding=utf-8
"""Unit tests for the Layer class."""

from __future__ import absolute_import

from octoprint_excluderegion.Layer import Layer
from .utils import TestCase


class LayerTests(TestCase):
    """Unit tests for the Layer class."""

    expectedProperties = ["height", "number"]

    def test_default_constructor(self):
        """Test the constructor when passed no arguments."""
        unit = Layer()

        self.assertIsInstance(unit, Layer)
        self.assertEqual(unit.height, 0, "height should be 0")
        self.assertEqual(unit.number, 0, "number should be 0")
        self.assertProperties(unit, LayerTests.expectedProperties)

    def test_constructor_kwargs(self):
        """Test the constructor when passed keyword arguments."""
        unit = Layer(height=2, number=1)

        self.assertIsInstance(unit, Layer)
        self.assertEqual(unit.height, 2, "height should be 2")
        self.assertEqual(unit.number, 1, "number should be 1")
        self.assertProperties(unit, LayerTests.expectedProperties)

    def test_copy_constructor(self):
        """Test the constructor when passed a Layer instance."""
        toCopy = Layer(height=2, number=1)

        unit = Layer(toCopy)

        self.assertIsInstance(unit, Layer)
        self.assertEqual(unit.height, 2, "height should be 2")
        self.assertEqual(unit.number, 1, "number should be 1")
        self.assertProperties(unit, LayerTests.expectedProperties)
