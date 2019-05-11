# coding=utf-8
"""Unit tests for the RetractionState class."""

from __future__ import absolute_import

from octoprint_excluderegion.RetractionState import RetractionState
from octoprint_excluderegion.Position import Position
from .utils import TestCase


class RetractionStateTests(TestCase):
    """Unit tests for the RetractionState class."""

    expectedProperties = [
        "recoverExcluded", "firmwareRetract", "extrusionAmount", "feedRate", "originalCommand"
    ]

    def test_constructor_no_args(self):
        """Test the constructor when no arguments are passed."""
        with self.assertRaises(ValueError):
            RetractionState()

    def test_constructor_firmwareRetraction(self):
        """Test the constructor when arguments are passed for a firmware retraction."""
        unit = RetractionState(firmwareRetract=True, originalCommand="SomeCommand")

        self.assertIsInstance(unit, RetractionState)
        self.assertEqual(unit.recoverExcluded, False, "recoverExcluded should be False")
        self.assertEqual(unit.firmwareRetract, True, "firmwareRetract should be True")
        self.assertEqual(unit.extrusionAmount, None, "extrusionAmount should be None")
        self.assertEqual(unit.feedRate, None, "feedRate should be None")
        self.assertEqual(
            unit.originalCommand, "SomeCommand", "originalCommand should be 'SomeCommand'"
        )
        self.assertProperties(unit, RetractionStateTests.expectedProperties)

    def test_constructor_extrusionAmount_feedRate(self):
        """Test the constructor when arguments are passed for a non-firmware retraction."""
        unit = RetractionState(extrusionAmount=1, feedRate=100, originalCommand="SomeCommand")

        self.assertIsInstance(unit, RetractionState)
        self.assertEqual(unit.recoverExcluded, False, "recoverExcluded should be False")
        self.assertEqual(unit.firmwareRetract, None, "firmwareRetract should be None")
        self.assertEqual(unit.extrusionAmount, 1, "extrusionAmount should be 1")
        self.assertEqual(unit.feedRate, 100, "feedRate should be 100")
        self.assertEqual(
            unit.originalCommand, "SomeCommand", "originalCommand should be 'SomeCommand'"
        )
        self.assertProperties(unit, RetractionStateTests.expectedProperties)

    def test_constructor_missing_extrusionAmount(self):
        """Test the constructor when feedRate is passed without extrusionAmount."""
        with self.assertRaises(ValueError):
            RetractionState(feedRate=100)

    def test_constructor_missing_feedRate(self):
        """Test the constructor when extrusionAmount is passed without feedRate."""
        with self.assertRaises(ValueError):
            RetractionState(extrusionAmount=1)

    def test_constructor_argumentConflict(self):
        """Test constructor when firmwareRetract is specified with extrusionAmount or feedRate."""
        with self.assertRaises(ValueError):
            RetractionState(firmwareRetract=True, extrusionAmount=1)

        with self.assertRaises(ValueError):
            RetractionState(firmwareRetract=True, feedRate=100)

        with self.assertRaises(ValueError):
            RetractionState(firmwareRetract=True, extrusionAmount=1, feedRate=100)

    def test_addRetractCommands_firmware_noParams(self):
        """Test the addRetractCommands method on a firmware retraction instance."""
        unit = RetractionState(firmwareRetract=True, originalCommand="G10")
        position = Position()

        returnCommands = unit.addRetractCommands(position, None)
        self.assertEqual(returnCommands, ["G10"], "The returned list should be ['G10']")
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

        returnCommands = unit.addRetractCommands(position, ["ABC"])
        self.assertEqual(
            returnCommands, ["ABC", "G10"], "The returned list should be ['ABC', 'G10']"
        )
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

    def test_addRetractCommands_firmware_withParams(self):
        """Test the addRetractCommands method on a firmware retraction instance with parameters."""
        unit = RetractionState(firmwareRetract=True, originalCommand="G11 S1")
        position = Position()

        returnCommands = unit.addRetractCommands(position, None)
        self.assertEqual(returnCommands, ["G10 S1"], "The returned list should be ['G10 S1']")
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

        returnCommands = unit.addRetractCommands(position, ["ABC"])
        self.assertEqual(
            returnCommands, ["ABC", "G10 S1"], "The returned list should be ['ABC', 'G10 S1']"
        )
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

    def test_addRecoverCommands_firmware_noParams(self):
        """Test the addRecoverCommands method on a firmware retraction instance."""
        unit = RetractionState(firmwareRetract=True, originalCommand="G10")
        position = Position()

        returnCommands = unit.addRecoverCommands(position, None)
        self.assertEqual(returnCommands, ["G11"], "The returned list should be ['G11']")
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

        returnCommands = unit.addRecoverCommands(position, ["ABC"])
        self.assertEqual(
            returnCommands, ["ABC", "G11"], "The returned list should be ['ABC', 'G11']"
        )
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

    def test_addRecoverCommands_firmware_withParams(self):
        """Test the addRecoverCommands method on a firmware retraction instance with parameters."""
        unit = RetractionState(firmwareRetract=True, originalCommand="G10 S1")
        position = Position()

        returnCommands = unit.addRecoverCommands(position, None)
        self.assertEqual(returnCommands, ["G11 S1"], "The returned list should be ['G11 S1']")
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

        returnCommands = unit.addRecoverCommands(position, ["ABC"])
        self.assertEqual(
            returnCommands, ["ABC", "G11 S1"], "The returned list should be ['ABC', 'G11 S1']"
        )
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

    def test_addRetractCommands_nonFirmware(self):
        """Test the addRetractCommands method on a non-firmware retraction instance."""
        unit = RetractionState(extrusionAmount=1, feedRate=100)
        position = Position()

        returnCommands = unit.addRetractCommands(position, None)
        self.assertEqual(
            returnCommands, ["G92 E1", "G1 F100 E0"],
            "The returned list should be ['G92 E1', 'G1 F100 E0']"
        )
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

        returnCommands = unit.addRetractCommands(position, ["ABC"])
        self.assertEqual(
            returnCommands, ["ABC", "G92 E1", "G1 F100 E0"],
            "The returned list should be ['ABC', 'G92 E1', 'G1 F100 E0']"
        )
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

    def test_addRecoverCommands_nonFirmware(self):
        """Test the addRecoverCommands method on a non-firmware retraction instance."""
        unit = RetractionState(extrusionAmount=1, feedRate=100)
        position = Position()

        returnCommands = unit.addRecoverCommands(position, None)
        self.assertEqual(
            returnCommands, ["G92 E-1", "G1 F100 E0"],
            "The returned list should be ['G92 E-1', 'G1 F100 E0']"
        )
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

        returnCommands = unit.addRecoverCommands(position, ["ABC"])
        self.assertEqual(
            returnCommands, ["ABC", "G92 E-1", "G1 F100 E0"],
            "The returned list should be ['ABC', 'G92 E-1', 'G1 F100 E0']"
        )
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")
