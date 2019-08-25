# coding=utf-8
"""Unit tests for the ExcludedGcode class."""

from __future__ import absolute_import

from octoprint_excluderegion.ExcludedGcode import ExcludedGcode, EXCLUDE_ALL
from .utils import TestCase


class ExcludedGcodeTests(TestCase):
    """Unit tests for the ExcludedGcode class."""

    expectedProperties = ["gcode", "mode", "description"]

    def test_constructor(self):
        """Test the constructor when valid arguments are passed."""
        unit = ExcludedGcode("G117", EXCLUDE_ALL, "My description")

        self.assertIsInstance(unit, ExcludedGcode)
        self.assertEqual(unit.gcode, "G117", "gcode should be 'G117'")
        self.assertEqual(unit.mode, EXCLUDE_ALL, "mode should be '" + EXCLUDE_ALL + "'")
        self.assertEqual(
            unit.description, "My description", "description should be 'My description'"
        )
        self.assertProperties(unit, ExcludedGcodeTests.expectedProperties)

    def test_constructor_missingGcode(self):
        """Test the constructor when a non-truthy gcode value is provided."""
        with self.assertRaises(AssertionError):
            ExcludedGcode(None, EXCLUDE_ALL, "My description")

    def test_constructor_invalidMode(self):
        """Test the constructor when an invalid mode value is provided."""
        with self.assertRaises(AssertionError):
            ExcludedGcode("G117", "invalid", "My description")
