# coding=utf-8
"""Unit tests for the AtCommandAction class."""

from __future__ import absolute_import

import re

from octoprint_excluderegion.AtCommandAction import AtCommandAction, ENABLE_EXCLUSION
from .utils import TestCase


class AtCommandActionTests(TestCase):
    """Unit tests for the AtCommandAction class."""

    expectedProperties = ["command", "parameterPattern", "action", "description"]

    def test_constructor_noPattern(self):
        """Test the constructor when valid arguments are passed, but no parameter pattern."""
        unit = AtCommandAction("TestCommand", None, ENABLE_EXCLUSION, "My description")

        self.assertIsInstance(unit, AtCommandAction)
        self.assertEqual(unit.command, "TestCommand", "command should be 'TestCommand'")
        self.assertEqual(unit.parameterPattern, None, "parameterPattern should be None")
        self.assertEqual(
            unit.action, ENABLE_EXCLUSION,
            "action should be '" + ENABLE_EXCLUSION + "'"
        )
        self.assertEqual(
            unit.description, "My description", "description should be 'My description'"
        )
        self.assertProperties(unit, AtCommandActionTests.expectedProperties)

    def test_constructor_validPattern(self):
        """Test the constructor when valid arguments are passed, including a parameter pattern."""
        unit = AtCommandAction("TestCommand", "^abc$", ENABLE_EXCLUSION, "My description")

        self.assertEqual(
            unit.parameterPattern, re.compile("^abc$"),
            "parameterPattern should be a regex instance for the specified pattern"
        )
        self.assertProperties(unit, AtCommandActionTests.expectedProperties)

    def test_constructor_missingCommand(self):
        """Test the constructor when a non-truthy command value is provided."""
        with self.assertRaises(AssertionError):
            AtCommandAction(None, "", ENABLE_EXCLUSION, "My description")

    def test_constructor_invalidAction(self):
        """Test the constructor when an invalid action value is provided."""
        with self.assertRaises(AssertionError):
            AtCommandAction(None, "", "invalid", "My description")

    def test_constructor_invalidPattern(self):
        """Test the constructor when an invalid parameter pattern is provided."""
        with self.assertRaises(re.error):
            AtCommandAction("TestCommand", "(invalid", ENABLE_EXCLUSION, "My description")

    def test_matches_command_no_param_pattern(self):
        """Test the matches method when no parameter pattern is defined."""
        unit = AtCommandAction("TestCommand", None, ENABLE_EXCLUSION, "My description")

        self.assertTrue(
            unit.matches("TestCommand", "test parameters"),
            "It should match 'TestCommand' with parameters"
        )
        self.assertTrue(
            unit.matches("TestCommand", None),
            "It should match 'TestCommand' with no parameters"
        )
        self.assertTrue(
            unit.matches("TestCommand", None),
            "It should match 'TestCommand' with no parameters"
        )
        self.assertFalse(
            unit.matches("DifferentCommand", "test parameters"),
            "It should NOT match 'DifferentCommand' with parameters"
        )
        self.assertFalse(
            unit.matches("DifferentCommand", None),
            "It should NOT match 'DifferentCommand' with no parameters"
        )

    def test_matches_command_with_param_pattern(self):
        """Test the matches method when a parameter pattern is defined."""
        unit = AtCommandAction(
            "TestCommand", "^\\s*match(\\s|$)", ENABLE_EXCLUSION, "My description"
        )

        self.assertTrue(
            unit.matches("TestCommand", "match parameters"),
            "It should match 'TestCommand' with parameters starting with 'match'"
        )
        self.assertFalse(
            unit.matches("TestCommand", "bad parameters"),
            "It should NOT match 'TestCommand' with parameters that don't start with 'match'"
        )
        self.assertFalse(
            unit.matches("TestCommand", None),
            "It should NOT match 'TestCommand' with no parameters"
        )

        self.assertFalse(
            unit.matches("DifferentCommand", "match parameters"),
            "It should NOT match 'DifferentCommand' with parameters starting with 'match'"
        )
        self.assertFalse(
            unit.matches("DifferentCommand", "bad parameters"),
            "It should NOT match 'DifferentCommand' with parameters that don't start with 'match'"
        )
        self.assertFalse(
            unit.matches("DifferentCommand", None),
            "It should NOT match 'DifferentCommand' with no parameters"
        )
