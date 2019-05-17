# coding=utf-8
"""Unit tests for the hook methods in the ExcludeRegionPlugin class."""

from __future__ import absolute_import

import mock

from .utils import TestCase
from .test_ExcludeRegionPlugin import create_plugin_instance, simulate_isActivePrintJob


class ExcludeRegionPluginHookTests(TestCase):  # xxpylint: disable=too-many-public-methods
    """Unit tests for the hook methods in the ExcludeRegionPlugin class."""

    def test_getUpdateInformation(self):
        """Test the getUpdateInformation method."""
        unit = create_plugin_instance()

        result = unit.getUpdateInformation()

        # Should have an entry for the plugin's id
        self.assertProperties(result, ["excluderegion"])

        # Entry should have the expected properties
        self.assertProperties(
            result["excluderegion"],
            ["displayName", "displayVersion", "type", "user", "repo", "current", "pip"]
        )

    def test_handleGcodeQueuing_notPrinting(self):
        """Test handleGcodeQueuing doesn't filter if not printing."""
        unit = create_plugin_instance()
        with mock.patch.object(unit.gcodeHandlers, 'handleGcode') as mockHandleGcode:
            mockCommInstance = mock.Mock(name="commInstance")

            # This is to cover an otherwise missed branch
            unit._logger.isEnabledFor.return_value = False  # pylint: disable=protected-access

            result = unit.handleGcodeQueuing(
                mockCommInstance,
                "queuing",
                "G0 X1 Y2",
                "cmdType",
                "G0",
                "subcode",
                "tags"
            )

            mockHandleGcode.assert_not_called()
            self.assertIsNone(result, "The result should be None")

    def test_handleGcodeQueuing_falsyGcode(self):
        """Test handleGcodeQueuing doesn't filter if the gcode parameter is falsy."""
        unit = create_plugin_instance()
        with mock.patch.object(unit.gcodeHandlers, 'handleGcode') as mockHandleGcode:
            simulate_isActivePrintJob(unit, True)
            mockCommInstance = mock.Mock(name="commInstance")

            result = unit.handleGcodeQueuing(
                mockCommInstance,
                "queuing",
                "not a gcode command",
                "cmdType",
                None,
                "subcode",
                "tags"
            )

            mockHandleGcode.assert_not_called()
            self.assertIsNone(result, "The result should be None")

    def test_handleGcodeQueuing_printing(self):
        """Test handleGcodeQueuing does filter when printing."""
        unit = create_plugin_instance()
        with mock.patch.object(unit.gcodeHandlers, 'handleGcode') as mockHandleGcode:
            simulate_isActivePrintJob(unit, True)
            mockHandleGcode.return_value = "ExpectedResult"
            mockCommInstance = mock.Mock(name="commInstance")

            result = unit.handleGcodeQueuing(
                mockCommInstance,
                "queuing",
                "G0 X1 Y2",
                "cmdType",
                "G0",
                "subcode",
                "tags"
            )

            mockHandleGcode.assert_called_with("G0 X1 Y2", "G0", "subcode")
            self.assertEqual(result, "ExpectedResult", "The expected result should be returned")

    def test_handleAtCommandQueuing_notPrinting(self):
        """Test handleAtCommandQueuing won't execute the command if not printing."""
        unit = create_plugin_instance()
        with mock.patch.object(unit.gcodeHandlers, 'handleAtCommand') as mockHandleAtCommand:
            simulate_isActivePrintJob(unit, False)

            mockCommInstance = mock.Mock(name="commInstance")

            result = unit.handleAtCommandQueuing(
                mockCommInstance,
                "queuing",
                "command",
                "parameters",
                "tags"
            )

            mockHandleAtCommand.assert_not_called()
            self.assertIsNone(result, "The result should be None")

    def test_handleAtCommandQueuing_printing(self):
        """Test handleAtCommandQueuing will execute the command if printing."""
        unit = create_plugin_instance()
        with mock.patch.object(unit.gcodeHandlers, 'handleAtCommand') as mockHandleAtCommand:
            simulate_isActivePrintJob(unit, True)

            mockCommInstance = mock.Mock(name="commInstance")

            result = unit.handleAtCommandQueuing(
                mockCommInstance,
                "queuing",
                "command",
                "parameters",
                "tags"
            )

            mockHandleAtCommand.assert_called_with(
                mockCommInstance,
                "command",
                "parameters"
            )
            self.assertIsNone(result, "The result should be None")

    def test_handleScriptHook_afterPrintDone_notPrinting_excluding(self):
        """Test handleScriptHook/afterPrintDone when not printing to ensure it does nothing."""
        unit = create_plugin_instance()
        with mock.patch.object(unit.state, 'exitExcludedRegion') as mockExitExcludedRegion:
            simulate_isActivePrintJob(unit, False)
            unit.state.excluding = True

            mockCommInstance = mock.Mock(name="commInstance")

            result = unit.handleScriptHook(
                mockCommInstance,
                "gcode",
                "afterPrintDone"
            )

            mockExitExcludedRegion.assert_not_called()
            self.assertIsNone(result, "The result should be None")

    def test_handleScriptHook_afterPrintDone_printing_notExcluding(self):
        """Test handleScriptHook/afterPrintDone when printing but not excluding."""
        unit = create_plugin_instance()
        with mock.patch.object(unit.state, 'exitExcludedRegion') as mockExitExcludedRegion:
            simulate_isActivePrintJob(unit, True)
            unit.state.excluding = False

            mockCommInstance = mock.Mock(name="commInstance")

            result = unit.handleScriptHook(
                mockCommInstance,
                "gcode",
                "afterPrintDone"
            )

            mockExitExcludedRegion.assert_not_called()
            self.assertIsNone(result, "The result should be None")

    def test_handleScriptHook_afterPrintDone_printing_excluding(self):
        """Test handleScriptHook/afterPrintDone when printing and excluding."""
        unit = create_plugin_instance()
        with mock.patch.object(unit.state, 'exitExcludedRegion') as mockExitExcludedRegion:
            simulate_isActivePrintJob(unit, True)
            unit.state.excluding = True
            mockExitExcludedRegion.return_value = ["expectedResult"]

            mockCommInstance = mock.Mock(name="commInstance")

            result = unit.handleScriptHook(
                mockCommInstance,
                "gcode",
                "afterPrintDone"
            )

            mockExitExcludedRegion.assert_called()
            self.assertEqual(
                result,
                (["expectedResult"], None),
                "The result should be a tuple containing the list returned by exitExcludedRegion"
            )

    def test_handleScriptHook_scriptTypeNoMatch(self):
        """Test handleScriptHook when the scriptType isn't 'gcode'."""
        unit = create_plugin_instance()
        with mock.patch.object(unit.state, 'exitExcludedRegion') as mockExitExcludedRegion:
            simulate_isActivePrintJob(unit, True)
            unit.state.excluding = True
            mockExitExcludedRegion.return_value = ["expectedResult"]

            mockCommInstance = mock.Mock(name="commInstance")

            result = unit.handleScriptHook(
                mockCommInstance,
                "notAMatch",
                "afterPrintDone"
            )

            mockExitExcludedRegion.assert_not_called()
            self.assertIsNone(result, "The result should be None")

    def test_handleScriptHook_scriptNameNoMatch(self):
        """Test handleScriptHook when the scriptName isn't 'afterPrintDone'."""
        unit = create_plugin_instance()
        with mock.patch.object(unit.state, 'exitExcludedRegion') as mockExitExcludedRegion:
            simulate_isActivePrintJob(unit, True)
            unit.state.excluding = True
            mockExitExcludedRegion.return_value = ["expectedResult"]

            mockCommInstance = mock.Mock(name="commInstance")

            result = unit.handleScriptHook(
                mockCommInstance,
                "gcode",
                "notAMatch"
            )

            mockExitExcludedRegion.assert_not_called()
            self.assertIsNone(result, "The result should be None")
