# coding=utf-8
"""Unit tests for settings functionality of the ExcludeRegionPlugin class."""

from __future__ import absolute_import

from callee.strings import String as AnyString
from callee.collections import Mapping as AnyMapping, Sequence as AnySequence
from callee.functions import Callable as AnyCallable

from octoprint.settings import settings as octoprintSettings, Settings

from octoprint_excluderegion import \
    LOG_MODE_OCTOPRINT, LOG_MODE_DEDICATED, LOG_MODE_BOTH

from octoprint_excluderegion.ExcludedGcode import ExcludedGcode, EXCLUDE_ALL
from octoprint_excluderegion.AtCommandAction \
    import AtCommandAction, ENABLE_EXCLUSION, DISABLE_EXCLUSION

from .utils import TestCase
from .test_ExcludeRegionPlugin import create_plugin_instance


class ExcludeRegionPluginSettingTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for settings functionality of the ExcludeRegionPlugin class."""

    # ~~ SettingsPlugin

    def test_get_settings_defaults(self):
        """Test the get_settings_defaults method."""
        unit = create_plugin_instance()

        result = unit.get_settings_defaults()

        self.assertProperties(
            result,
            [
                "clearRegionsAfterPrintFinishes",
                "mayShrinkRegionsWhilePrinting",
                "loggingMode",
                "enteringExcludedRegionGcode",
                "exitingExcludedRegionGcode",
                "extendedExcludeGcodes",
                "atCommandActions"
            ]
        )

    def test_get_settings_version(self):
        """Test the get_settings_version method."""
        unit = create_plugin_instance()

        result = unit.get_settings_version()

        self.assertEqual(result, 1, "The settings version should be 1")

    def test_get_settings_preprocessors(self):
        """Test the get_settings_preprocessors method."""
        unit = create_plugin_instance()

        result = unit.get_settings_preprocessors()

        self.assertEqual(
            result,
            AnySequence(of=AnyMapping(AnyString(), AnyCallable())),
            "The returned sequence should only contain dictionaries of string->callable"
        )
        self.assertEqual(len(result), 2, "The returned sequence should contain 2 items")

        self.assertIn(
            "extendedExcludeGcodes", result[0],
            "There should be a 'extendedExcludeGcodes' setter preprocessor"
        )
        self.assertEqual(
            result[0]["extendedExcludeGcodes"]([{"gcode": "b"}, {"gcode": "C"}, {"gcode": "a"}]),
            [{"gcode": "a"}, {"gcode": "b"}, {"gcode": "C"}],
            "The 'extendedExcludeGcodes' preprocessor should sort by the 'gcode' property."
        )

        self.assertIn(
            "atCommandActions", result[0],
            "There should be a 'atCommandActions' setter preprocessor"
        )
        self.assertEqual(
            result[0]["atCommandActions"]([{"command": "b"}, {"command": "C"}, {"command": "a"}]),
            [{"command": "a"}, {"command": "b"}, {"command": "C"}],
            "The 'atCommandActions' preprocessor should sort by the 'command' property."
        )

    def test_loggingMode_default(self):
        """Test the loggingMode default value."""
        unit = create_plugin_instance()

        mockLogger = unit._logger  # pylint: disable=protected-access
        mockLogger.addHandler.assert_not_called()
        mockLogger.removeHandler.assert_not_called()
        self.assertTrue(mockLogger.propagate, "The logger should propagate up to the parent.")

        self.assertIsNone(
            unit._pluginLoggingHandler,  # pylint: disable=protected-access
            "No logging handler should have been created"
        )

        self.assertEqual(
            unit.loggingMode, LOG_MODE_OCTOPRINT,
            "The default logging mode should be LOG_MODE_OCTOPRINT."
        )

    def test_loggingMode_invalidMode(self):
        """Test the loggingMode setter raises an AttributeError when assigned an invalid mode."""
        unit = create_plugin_instance()

        with self.assertRaises(AttributeError):
            unit.loggingMode = "invalidMode"

        mockLogger = unit._logger  # pylint: disable=protected-access
        mockLogger.addHandler.assert_not_called()
        mockLogger.removeHandler.assert_not_called()
        self.assertTrue(mockLogger.propagate, "The logger should propagate up to the parent.")

        self.assertIsNone(
            unit._pluginLoggingHandler,  # pylint: disable=protected-access
            "No logging handler should have been created"
        )

        self.assertEqual(
            unit.loggingMode, LOG_MODE_OCTOPRINT,
            "The logging mode should be LOG_MODE_OCTOPRINT."
        )

    def test_loggingMode_LOG_MODE_OCTOPRINT_noChange(self):
        """Test the loggingMode setter when the assigned value is the same as the current value."""
        unit = create_plugin_instance()

        unit.loggingMode = LOG_MODE_OCTOPRINT

        mockLogger = unit._logger  # pylint: disable=protected-access
        mockLogger.addHandler.assert_not_called()
        mockLogger.removeHandler.assert_not_called()
        self.assertTrue(mockLogger.propagate, "The logger should propagate up to the parent.")

        self.assertIsNone(
            unit._pluginLoggingHandler,  # pylint: disable=protected-access
            "No logging handler should have been created"
        )

        self.assertEqual(
            unit.loggingMode, LOG_MODE_OCTOPRINT,
            "The logging mode should be LOG_MODE_OCTOPRINT."
        )

    def test_loggingMode_LOG_MODE_OCTOPRINT_change(self):
        """Test the loggingMode setter when assigned LOG_MODE_OCTOPRINT."""
        unit = create_plugin_instance()
        unit.loggingMode = LOG_MODE_DEDICATED

        loggingHandler = unit._pluginLoggingHandler  # pylint: disable=protected-access
        mockLogger = unit._logger  # pylint: disable=protected-access
        mockLogger.reset_mock()

        # Change the logging mode back
        unit.loggingMode = LOG_MODE_OCTOPRINT

        mockLogger.addHandler.assert_not_called()
        mockLogger.removeHandler.assert_called_with(loggingHandler)
        self.assertTrue(mockLogger.propagate, "The logger should propagate up to the parent.")

        self.assertIsNotNone(
            loggingHandler,
            "A new logging handler should have been created"
        )

        self.assertEqual(
            unit.loggingMode, LOG_MODE_OCTOPRINT,
            "The logging mode should be LOG_MODE_OCTOPRINT."
        )

    def test_loggingMode_LOG_MODE_DEDICATED_from_default(self):
        """Test the loggingMode setter when assigned LOG_MODE_DEDICATED."""
        unit = create_plugin_instance()

        unit.loggingMode = LOG_MODE_DEDICATED

        mockLogger = unit._logger  # pylint: disable=protected-access
        loggingHandler = unit._pluginLoggingHandler  # pylint: disable=protected-access

        mockLogger.addHandler.assert_called_with(loggingHandler)
        mockLogger.removeHandler.assert_not_called()
        self.assertFalse(mockLogger.propagate, "The logger should NOT propagate up to the parent.")

        self.assertIsNotNone(
            loggingHandler,
            "A new logging handler should have been created"
        )

        self.assertEqual(
            unit.loggingMode, LOG_MODE_DEDICATED,
            "The logging mode should be LOG_MODE_DEDICATED."
        )

    def test_loggingMode_LOG_MODE_DEDICATED_from_LOG_MODE_BOTH(self):
        """Test loggingMode when changing the mode from LOG_MODE_BOTH to LOG_MODE_DEDICATED."""
        unit = create_plugin_instance()
        unit.loggingMode = LOG_MODE_BOTH

        originalLoggingHandler = unit._pluginLoggingHandler  # pylint: disable=protected-access
        mockLogger = unit._logger  # pylint: disable=protected-access
        mockLogger.reset_mock()

        # Change the logging mode to dedicated
        unit.loggingMode = LOG_MODE_DEDICATED

        mockLogger.addHandler.assert_not_called()
        mockLogger.removeHandler.assert_not_called()
        self.assertFalse(mockLogger.propagate, "The logger should NOT propagate up to the parent.")

        self.assertIs(
            unit._pluginLoggingHandler,  # pylint: disable=protected-access
            originalLoggingHandler,
            "No new logging handler should be created"
        )

        self.assertEqual(
            unit.loggingMode, LOG_MODE_DEDICATED,
            "The logging mode should be LOG_MODE_DEDICATED."
        )

    def test_loggingMode_LOG_MODE_BOTH(self):
        """Test the loggingMode setter when assigned LOG_MODE_BOTH."""
        unit = create_plugin_instance()

        unit.loggingMode = LOG_MODE_BOTH

        mockLogger = unit._logger  # pylint: disable=protected-access
        loggingHandler = unit._pluginLoggingHandler  # pylint: disable=protected-access

        mockLogger.addHandler.assert_called_with(loggingHandler)
        mockLogger.removeHandler.assert_not_called()
        self.assertTrue(mockLogger.propagate, "The logger should propagate up to the parent.")

        self.assertIsNotNone(
            loggingHandler,
            "A new logging handler should have been created"
        )

        self.assertEqual(
            unit.loggingMode, LOG_MODE_BOTH,
            "The logging mode should be LOG_MODE_BOTH."
        )

    def test_splitGcodeScript_None(self):
        """Test _splitGcodeScript when None is provided."""
        unit = create_plugin_instance()

        result = unit._splitGcodeScript(None)  # pylint: disable=protected-access

        self.assertIsNone(result, "The result should be None")

    def test_splitGcodeScript_empty(self):
        """Test _splitGcodeScript when an empty string is provided."""
        unit = create_plugin_instance()

        result = unit._splitGcodeScript("")  # pylint: disable=protected-access

        self.assertIsNone(result, "The result should be None")

    def test_splitGcodeScript_ignore_comments_and_whitespace(self):
        """Test _splitGcodeScript when only comments and whitespace are provided."""
        unit = create_plugin_instance()

        result = unit._splitGcodeScript(  # pylint: disable=protected-access
            ";This is a\n"
            "    \n" +
            "\n" +
            "   ;whitespace and comment TEST   "
        )

        self.assertIsNone(result, "The result should be None")

    def test_splitGcodeScript_lineBreaks(self):
        """Test _splitGcodeScript splits lines on CR, LF and CRLF."""
        unit = create_plugin_instance()

        result = unit._splitGcodeScript(  # pylint: disable=protected-access
            "CR\r"
            "LF\n" +
            "CRLF\r\n" +
            "END"
        )

        self.assertEqual(result, ["CR", "LF", "CRLF", "END"])

    def test_splitGcodeScript_single_line(self):
        """Test _splitGcodeScript splits a single line (no EOL)."""
        unit = create_plugin_instance()

        result = unit._splitGcodeScript("No EOL")  # pylint: disable=protected-access

        self.assertEqual(result, ["No EOL"])

    def test_splitGcodeScript_command_lines_with_comments_and_whitespace(self):
        """Test _splitGcodeScript when lines contain a combination of command, ws and comment."""
        unit = create_plugin_instance()

        result = unit._splitGcodeScript(  # pylint: disable=protected-access
            "   Line   1; Ignore me\n" +
            "Line 2     ; Also ignore me\n"
        )

        self.assertEqual(result, ["Line   1", "Line 2"])

    def _test_handleSettingsUpdated(
            self,
            settingPath,
            settingValues,
            propertyPath,
            propertyValues
    ):
        """
        Test handleSettingsUpdated for setting changes affecting a specific property.

        Parameters
        ----------
        settingPath : list of string
            If the first element is a string, this is the property path under the plugin settings
            to assign the settingValues to.  If the first element is a Settings object, then the
            remaining items will be treated as a path to update under that object (e.g. for global
            settings).
        settingValues : list
            The sequence of values to assign to the setting specified by settingPath.
        propertyPath : list of string
            Property path under the 'unit' to test the value of after updating the setting.
        propertyValues : list
            The sequence of values to expect for each corresponding setting value.
        """
        unit = create_plugin_instance()

        def get_attr_by_path(propertyPath):
            """
            Retrieve the value of the attribute at the specified path under the 'unit' object.

            Parameters
            ----------
            propertyPath : list of string
                Each element of this list is a property name to follow.  The first property name
                will be retrieved from the 'unit' object, and each subsequent property name will be
                retrieved from the previous property's value.
            """
            result = unit
            for propertyName in propertyPath:
                result = getattr(result, propertyName)
            return result

        if (isinstance(settingPath[0], Settings)):
            settingsObj = settingPath[0]
            del settingPath[0]
        else:
            settingsObj = unit._settings  # pylint: disable=protected-access

        for index, settingValue in enumerate(settingValues):
            settingsObj.set(settingPath, settingValue)

            unit._handleSettingsUpdated()  # pylint: disable=protected-access

            self.assertEqual(
                get_attr_by_path(propertyPath),
                propertyValues[index],
                "Property '%s' should be set to '%s'" % (propertyPath, propertyValues[index])
            )

    def test_handleSettingsUpdated_clearRegionsAfterPrintFinishes(self):
        """Test handleSettingsUpdated when the clearRegionsAfterPrintFinishes setting changes."""
        self._test_handleSettingsUpdated(
            ["clearRegionsAfterPrintFinishes"],
            [True, False],
            ["clearRegionsAfterPrintFinishes"],
            [True, False]
        )

    def test_handleSettingsUpdated_mayShrinkRegionsWhilePrinting(self):
        """Test handleSettingsUpdated when the mayShrinkRegionsWhilePrinting setting changes."""
        self._test_handleSettingsUpdated(
            ["mayShrinkRegionsWhilePrinting"],
            [True, False],
            ["mayShrinkRegionsWhilePrinting"],
            [True, False]
        )

    def test_handleSettingsUpdated_loggingMode(self):
        """Test handleSettingsUpdated when the loggingMode setting changes."""
        self._test_handleSettingsUpdated(
            ["loggingMode"],
            [LOG_MODE_BOTH, LOG_MODE_DEDICATED, LOG_MODE_OCTOPRINT],
            ["loggingMode"],
            [LOG_MODE_BOTH, LOG_MODE_DEDICATED, LOG_MODE_OCTOPRINT]
        )

    def test_handleSettingsUpdated_g90InfluencesExtruder(self):
        """Test handleSettingsUpdated when the feature.g90InfluencesExtruder setting changes."""
        self._test_handleSettingsUpdated(
            [octoprintSettings(), "feature", "g90InfluencesExtruder"],
            [True, False],
            ["state", "g90InfluencesExtruder"],
            [True, False]
        )

    def test_handleSettingsUpdated_enteringExcludedRegionGcode(self):
        """Test handleSettingsUpdated when the enteringExcludedRegionGcode setting changes."""
        self._test_handleSettingsUpdated(
            ["enteringExcludedRegionGcode"],
            [None, "Some Gcode Script ;With a comment"],
            ["state", "enteringExcludedRegionGcode"],
            [None, ["Some Gcode Script"]]
        )

    def test_handleSettingsUpdated_exitingExcludedRegionGcode(self):
        """Test handleSettingsUpdated when the exitingExcludedRegionGcode setting changes."""
        self._test_handleSettingsUpdated(
            ["exitingExcludedRegionGcode"],
            [None, "Some Gcode Script ;With a comment"],
            ["state", "exitingExcludedRegionGcode"],
            [None, ["Some Gcode Script"]]
        )

    def test_handleSettingsUpdated_extendedExcludeGcodes(self):
        """Test handleSettingsUpdated when the extendedExcludeGcodes setting changes."""
        self._test_handleSettingsUpdated(
            ["extendedExcludeGcodes"],
            [
                [],
                [
                    {
                        "gcode": "G0",
                        "mode": EXCLUDE_ALL,
                        "description": None
                    },
                    {
                        "gcode": "G10",
                        "mode": EXCLUDE_ALL,
                        "description": "some description"
                    }
                ]
            ],
            ["state", "extendedExcludeGcodes"],
            [
                {},
                {
                    "G0": ExcludedGcode("G0", EXCLUDE_ALL, None),
                    "G10": ExcludedGcode("G10", EXCLUDE_ALL, "some description")
                }
            ]
        )

    def test_handleSettingsUpdated_atCommandActions(self):
        """Test handleSettingsUpdated when the atCommandActions setting changes."""
        self._test_handleSettingsUpdated(
            ["atCommandActions"],
            [
                [],
                [
                    {
                        "command": "TestCommand",
                        "parameterPattern": None,
                        "action": ENABLE_EXCLUSION,
                        "description": None
                    },
                    {
                        "command": "TestCommand",
                        "parameterPattern": "parameters",
                        "action": DISABLE_EXCLUSION,
                        "description": None
                    }
                ]
            ],
            ["state", "atCommandActions"],
            [
                {},
                {
                    "TestCommand": [
                        AtCommandAction("TestCommand", None, ENABLE_EXCLUSION, None),
                        AtCommandAction("TestCommand", "parameters", DISABLE_EXCLUSION, None)
                    ]
                }
            ]
        )
