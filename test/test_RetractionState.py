# coding=utf-8
"""Unit tests for the RetractionState class."""

from __future__ import absolute_import

import mock

from octoprint_excluderegion.RetractionState import RetractionState
from octoprint_excluderegion.Position import Position
from .utils import TestCase


class RetractionStateTests(TestCase):
    """Unit tests for the RetractionState class."""

    expectedProperties = [
        "recoverExcluded", "allowCombine", "firmwareRetract", "extrusionAmount", "feedRate", "originalCommand"
    ]

    def test_constructor_firmwareRetraction(self):
        """Test the constructor when arguments are passed for a firmware retraction."""
        unit = RetractionState(
            originalCommand="SomeCommand",
            firmwareRetract=True
        )

        self.assertIsInstance(unit, RetractionState)
        self.assertFalse(unit.recoverExcluded, "recoverExcluded should be False")
        self.assertTrue(unit.allowCombine, "allowCombine should be True")
        self.assertTrue(unit.firmwareRetract, "firmwareRetract should be True")
        self.assertIsNone(unit.extrusionAmount, "extrusionAmount should be None")
        self.assertIsNone(unit.feedRate, "feedRate should be None")
        self.assertEqual(
            unit.originalCommand, "SomeCommand",
            "originalCommand should be 'SomeCommand'"
        )
        self.assertProperties(unit, RetractionStateTests.expectedProperties)

    def test_constructor_extrusionAmount_feedRate(self):
        """Test the constructor when arguments are passed for a non-firmware retraction."""
        unit = RetractionState(
            originalCommand="SomeCommand",
            firmwareRetract=False,
            extrusionAmount=1,
            feedRate=100
        )

        self.assertIsInstance(unit, RetractionState)
        self.assertFalse(unit.recoverExcluded, "recoverExcluded should be False")
        self.assertTrue(unit.allowCombine, "allowCombine should be True")
        self.assertFalse(unit.firmwareRetract, "firmwareRetract should be None")
        self.assertEqual(unit.extrusionAmount, 1, "extrusionAmount should be 1")
        self.assertEqual(unit.feedRate, 100, "feedRate should be 100")
        self.assertEqual(
            unit.originalCommand, "SomeCommand",
            "originalCommand should be 'SomeCommand'"
        )
        self.assertProperties(unit, RetractionStateTests.expectedProperties)

    def test_constructor_missing_extrusionAmount(self):
        """Test the constructor when feedRate is passed without extrusionAmount."""
        with self.assertRaises(ValueError):
            RetractionState(
                originalCommand="SomeCommand",
                firmwareRetract=False,
                feedRate=100
            )

    def test_constructor_missing_feedRate(self):
        """Test the constructor when extrusionAmount is passed without feedRate."""
        with self.assertRaises(ValueError):
            RetractionState(
                originalCommand="SomeCommand",
                firmwareRetract=False,
                extrusionAmount=1
            )

    def test_constructor_argumentConflict(self):
        """Test constructor when firmwareRetract is specified with extrusionAmount or feedRate."""
        with self.assertRaises(ValueError):
            RetractionState(
                originalCommand="SomeCommand",
                firmwareRetract=True,
                extrusionAmount=1
            )

        with self.assertRaises(ValueError):
            RetractionState(
                originalCommand="SomeCommand",
                firmwareRetract=True,
                feedRate=100
            )

        with self.assertRaises(ValueError):
            RetractionState(
                originalCommand="SomeCommand",
                firmwareRetract=True,
                extrusionAmount=1,
                feedRate=100
            )

    def test_generateRetractCommands_firmware_noParams(self):
        """Test the generateRetractCommands method on a firmware retraction instance."""
        unit = RetractionState(
            originalCommand="G10",
            firmwareRetract=True
        )
        position = Position()

        returnCommands = unit.generateRetractCommands(position)
        self.assertEqual(returnCommands, ["G10"], "The returned list should be ['G10']")
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

    def test_generateRetractCommands_firmware_withParams(self):
        """Test generateRetractCommands method on a firmware retraction instance with parameters."""
        unit = RetractionState(
            originalCommand="G11 S1",
            firmwareRetract=True
        )
        position = Position()

        returnCommands = unit.generateRetractCommands(position)
        self.assertEqual(returnCommands, ["G10 S1"], "The returned list should be ['G10 S1']")
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

    def test_generateRetractCommands_nonFirmware(self):
        """Test the generateRetractCommands method on a non-firmware retraction instance."""
        unit = RetractionState(
            originalCommand="G1 F100 E1",
            firmwareRetract=False,
            extrusionAmount=1,
            feedRate=100
        )
        position = Position()

        returnCommands = unit.generateRetractCommands(position)
        self.assertEqual(
            returnCommands, ["G92 E1", "G1 F100 E0"],
            "The returned list should be ['G92 E1', 'G1 F100 E0']"
        )
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

    def test_generateRecoverCommands_firmware_noParams(self):
        """Test the generateRecoverCommands method on a firmware retraction instance."""
        unit = RetractionState(
            originalCommand="G10",
            firmwareRetract=True
        )
        position = Position()

        returnCommands = unit.generateRecoverCommands(position)
        self.assertEqual(returnCommands, ["G11"], "The returned list should be ['G11']")
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

    def test_generateRecoverCommands_firmware_withParams(self):
        """Test generateRecoverCommands method on a firmware retraction instance with parameters."""
        unit = RetractionState(
            originalCommand="G10 S1",
            firmwareRetract=True
        )
        position = Position()

        returnCommands = unit.generateRecoverCommands(position)
        self.assertEqual(returnCommands, ["G11 S1"], "The returned list should be ['G11 S1']")
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

    def test_generateRecoverCommands_nonFirmware(self):
        """Test the generateRecoverCommands method on a non-firmware retraction instance."""
        unit = RetractionState(
            originalCommand="G1 F100 E1",
            firmwareRetract=False,
            extrusionAmount=1,
            feedRate=100
        )
        position = Position()

        returnCommands = unit.generateRecoverCommands(position)
        self.assertEqual(
            returnCommands, ["G92 E-1", "G1 F100 E0"],
            "The returned list should be ['G92 E-1', 'G1 F100 E0']"
        )
        self.assertEqual(position.E_AXIS.current, 0, "The extruder axis should not be modified")

    def test_combine_combineAllowed_firmware(self):
        """Test the combine method with two firmware retractions when combine is allowed."""
        mockLogger = mock.Mock()

        unit = RetractionState(
            originalCommand="G10 S1",
            firmwareRetract=True
        )

        toCombine = RetractionState(
            originalCommand="G10 S1",
            firmwareRetract=True
        )

        result = unit.combine(toCombine, mockLogger)

        self.assertIs(result, unit, "The return value should be the instance the method is called on")
        self.assertIsNone(unit.extrusionAmount, "extrusionAmount should be None")
        self.assertTrue(unit.firmwareRetract, "firmwareRetract should be True")
        mockLogger.warn.assert_not_called()

    def test_combine_combineAllowed_nonFirmware(self):
        """Test the combine method with two non-firmware retractions when combine is allowed."""
        mockLogger = mock.Mock()

        unit = RetractionState(
            originalCommand="G1 F100 E-1",
            firmwareRetract=False,
            extrusionAmount=1,
            feedRate=100
        )

        toCombine = RetractionState(
            originalCommand="G1 F200 E-0.5",
            firmwareRetract=False,
            extrusionAmount=0.5,
            feedRate=200
        )

        result = unit.combine(toCombine, mockLogger)

        self.assertIs(result, unit, "The return value should be the instance the method is called on")
        self.assertEqual(unit.extrusionAmount, 1.5, "The extrusionAmount should be updated to 1.5")
        mockLogger.warn.assert_not_called()

    def test_combine_combineNotAllowed_nonFirmware(self):
        """Test the combine method with two non-firmware retractions when combine is not allowed."""
        mockLogger = mock.Mock()

        unit = RetractionState(
            originalCommand="G1 F100 E-1",
            firmwareRetract=False,
            extrusionAmount=1,
            feedRate=100
        )
        unit.allowCombine = False

        toCombine = RetractionState(
            originalCommand="G1 F200 E-0.5",
            firmwareRetract=False,
            extrusionAmount=0.5,
            feedRate=200
        )

        result = unit.combine(toCombine, mockLogger)
        
        self.assertIs(result, unit, "The return value should be the instance the method is called on")
        self.assertEqual(unit.extrusionAmount, 1, "The extrusionAmount should not be modified")
        mockLogger.warn.assert_called()

    def test_combine_combineNotAllowed_firmware(self):
        """Test the combine method with two firmware retractions when combine is not allowed."""
        mockLogger = mock.Mock()

        unit = RetractionState(
            originalCommand="G10 S1",
            firmwareRetract=True
        )
        unit.allowCombine = False

        toCombine = RetractionState(
            originalCommand="G10 S1",
            firmwareRetract=True
        )

        result = unit.combine(toCombine, mockLogger)
        
        self.assertIs(result, unit, "The return value should be the instance the method is called on")
        self.assertTrue(unit.firmwareRetract, "firmwareRetract should be True")
        self.assertIsNone(unit.extrusionAmount, "The extrusionAmount should not be modified")
        mockLogger.warn.assert_called()

    def test_combine_mixedTypes(self):
        """Test the combine method with a non-firmware and firmware retraction."""
        mockLogger = mock.Mock()

        unit = RetractionState(
            originalCommand="G1 F100 E-1",
            firmwareRetract=False,
            extrusionAmount=1,
            feedRate=100
        )

        toCombine = RetractionState(
            originalCommand="G10 S1",
            firmwareRetract=True
        )

        result = unit.combine(toCombine, mockLogger)

        self.assertIs(result, unit, "The return value should be the instance the method is called on")
        self.assertEqual(unit.extrusionAmount, 1, "The extrusionAmount should not be modified")
        mockLogger.warn.assert_called()
