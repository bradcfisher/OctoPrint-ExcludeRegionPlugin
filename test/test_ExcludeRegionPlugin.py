# coding=utf-8
"""Unit tests for the ExcludeRegionPlugin class."""

from __future__ import absolute_import

import mock
from callee.types import InstanceOf

from octoprint.events import Events
from octoprint.settings import settings as octoprintSettings

from octoprint_excluderegion \
    import ExcludeRegionPlugin, ExcludeRegionState, GcodeHandlers, RectangularRegion, CircularRegion

from .utils import TestCase


class ExcludeRegionPluginTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for the ExcludeRegionPlugin class."""

    @classmethod
    def setUpClass(cls):
        """Perform global test initialization for the class."""
        octoprintSettings(True)

    expectedProperties = [
        # SettingsPlugin properties
        "_settings",
        # ExcludeRegionPlugin properties
        "_activePrintJob",
        "clearRegionsAfterPrintFinishes",
        "mayShrinkRegionsWhilePrinting",
        "state",
        "gcodeHandlers",
        "_loggingMode",
        "_pluginLoggingHandler"
    ]

    def test_constructor(self):
        """Test the constructor initialization."""
        unit = ExcludeRegionPlugin()

        self.assertIsInstance(unit, ExcludeRegionPlugin)
        self.assertProperties(unit, ExcludeRegionPluginTests.expectedProperties)
        self.assertIsNone(unit.isActivePrintJob, "isActivePrintJob should be None")
        self.assertIsNone(
            unit.clearRegionsAfterPrintFinishes,
            "clearRegionsAfterPrintFinishes should be None"
        )
        self.assertIsNone(
            unit.mayShrinkRegionsWhilePrinting,
            "mayShrinkRegionsWhilePrinting should be None"
        )
        self.assertIsNone(unit.state, "state should be None")
        self.assertIsNone(unit.gcodeHandlers, "gcodeHandlers should be None")
        self.assertIsNone(unit.loggingMode, "loggingMode should be None")

        self.assertIsNone(
            unit._pluginLoggingHandler,  # pylint: disable=protected-access
            "_pluginLoggingHandler should be None"
        )

    def test_initialize(self):
        """Test the initialize method."""
        unit = ExcludeRegionPlugin()

        # pylint: disable=protected-access
        unit._identifier = "test_excluderegion_identifier"
        unit._logger = mock.Mock()
        unit._plugin_version = "test_version"
        unit._handleSettingsUpdated = mock.Mock()
        unit._notifyExcludedRegionsChanged = mock.Mock()

        unit.initialize()

        self.assertFalse(unit.isActivePrintJob, "isActivePrintJob should be False")
        self.assertIsInstance(
            unit.state, ExcludeRegionState,
            "state should be an ExcludeRegionState instance"
        )
        self.assertIsInstance(
            unit.gcodeHandlers, GcodeHandlers,
            "state should be an GcodeHandlers instance"
        )

        unit._handleSettingsUpdated.assert_called()
        unit._notifyExcludedRegionsChanged.assert_called_with()

    @staticmethod
    def _createPluginInstance():
        from octoprint.plugin import plugin_settings

        unit = ExcludeRegionPlugin()

        # pylint: disable=protected-access
        unit._identifier = "excluderegion"
        unit._logger = mock.Mock()
        unit._plugin_manager = mock.Mock()
        unit._plugin_version = "test_version"

        unit._settings = plugin_settings(
            unit._identifier,
            unit.get_settings_defaults(),
            unit.get_settings_preprocessors()[0],
            unit.get_settings_preprocessors()[1]
        )

        unit.initialize()

        return unit

    def test_getUpdateInformation(self):
        """Test the getUpdateInformation method."""
        unit = self._createPluginInstance()

        result = unit.getUpdateInformation()

        # Should have an entry for the plugin's id
        self.assertProperties(result, ["excluderegion"])

        # Entry should have the expected properties
        self.assertProperties(
            result["excluderegion"],
            ["displayName", "displayVersion", "type", "user", "repo", "current", "pip"]
        )

    # ~~ AssetPlugin

    def _test_get_assets(self, testVersion, validationCallback=None):
        """Test the get_assets method under OctoPrint 1.3.9 or older."""
        import octoprint
        originalVersion = octoprint.__version__
        originalDisplayVersion = octoprint.__display_version__
        try:
            octoprint.__version__ = testVersion
            octoprint.__display_version__ = testVersion + "-test"

            unit = self._createPluginInstance()

            result = unit.get_assets()

            self.assertProperties(result, ["js", "css"])

            if (validationCallback is not None):
                validationCallback(result)
        finally:
            octoprint.__version__ = originalVersion
            octoprint.__display_version__ = originalDisplayVersion

    def test_get_assets_octoprint1_3_9(self):
        """Test the get_assets method under OctoPrint 1.3.9 or older."""
        def additional_validations(result):
            self.assertEqual(len(result["js"]), 2, "Two js assets should be returned")
            self.assertEqual(len(result["css"]), 1, "One CSS asset should be returned")

        self._test_get_assets("1.3.9", additional_validations)

    def test_get_assets_octoprint1_3_10(self):
        """Test the get_assets method under OctoPrint 1.3.10 or newer."""
        def additional_validations(result):
            self.assertEqual(len(result["js"]), 1, "One js asset should be returned")
            self.assertEqual(len(result["css"]), 1, "One CSS asset should be returned")

        self._test_get_assets("1.3.10", additional_validations)

    # ~~ TemplatePlugin

    def test_get_template_configs(self):
        """Test the get_template_configs method."""
        unit = self._createPluginInstance()

        result = unit.get_template_configs()

        self.assertEqual(len(result), 1, "The returned list should have one entry")

    # ~~ SettingsPlugin

    def test_get_settings_defaults(self):
        """Test the get_settings_defaults method."""
        unit = self._createPluginInstance()

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
        unit = self._createPluginInstance()

        result = unit.get_settings_version()

        self.assertEqual(result, 1, "The settings version should be 1")

    def test_get_settings_preprocessors(self):
        """Test the get_settings_preprocessors method."""
        unit = self._createPluginInstance()

        result = unit.get_settings_preprocessors()

        self.assertEqual(len(result), 2, "The returned list should have two items")
        self.assertIsDictionary(result[0], "The first item in the list should be a dictionary")
        self.assertIsDictionary(result[1], "The second item in the list should be a dictionary")

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

    # ~~ SimpleApiPlugin

    def test_get_api_commands(self):
        """Test the get_api_commands method."""
        unit = self._createPluginInstance()

        result = unit.get_api_commands()

        self.assertProperties(
            result,
            [
                "addExcludeRegion",
                "updateExcludeRegion",
                "deleteExcludeRegion"
            ]
        )

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_unauthenticated(self, mockCurrentUser):
        """Test on_api_command when the current user is not authenticated."""
        mockCurrentUser.is_anonymous.return_value = True

        unit = self._createPluginInstance()

        result = unit.on_api_command("deleteExcludeRegion", {"id": "someId"})

        self.assertEqual(len(result), 2, "The result should have two items")
        self.assertEqual(result[1], 403, "A 403 response should be generated")

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_unknownCommand(self, mockCurrentUser):
        """Test on_api_command when an invalid command is provided."""
        mockCurrentUser.is_anonymous.return_value = False

        unit = self._createPluginInstance()

        result = unit.on_api_command("invalidCommand", {"id": "someId"})

        self.assertEqual(len(result), 2, "The result should have two items")
        self.assertEqual(result[1], 400, "A 400 response should be generated")

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_addExcludeRegion_RectangularRegion(self, mockCurrentUser):
        """Test on_api_command for the 'addExcludeRegion' command and a RectangularRegion."""
        mockCurrentUser.is_anonymous.return_value = False
        handlerMock = mock.Mock()
        handlerMock.return_value = "expectedResult"

        unit = self._createPluginInstance()
        unit._handleAddExcludeRegion = handlerMock  # pylint: disable=protected-access

        result = unit.on_api_command(
            "addExcludeRegion",
            {
                "type": "RectangularRegion",
                "x1": 0,
                "y1": 0,
                "x2": 10,
                "y2": 10
            }
        )

        handlerMock.assert_called_with(InstanceOf(RectangularRegion))
        self.assertEqual(result, "expectedResult", "The expected result should be returned")

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_addExcludeRegion_CircularRegion(self, mockCurrentUser):
        """Test on_api_command for the 'addExcludeRegion' command and a CircularRegion."""
        mockCurrentUser.is_anonymous.return_value = False
        handlerMock = mock.Mock()
        handlerMock.return_value = "expectedResult"

        unit = self._createPluginInstance()
        unit._handleAddExcludeRegion = handlerMock  # pylint: disable=protected-access

        result = unit.on_api_command(
            "addExcludeRegion",
            {
                "type": "CircularRegion",
                "cx": 0,
                "cy": 0,
                "radius": 10
            }
        )

        handlerMock.assert_called_with(InstanceOf(CircularRegion))
        self.assertEqual(result, "expectedResult", "The expected result should be returned")

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_addExcludeRegion_unsupportedType(self, mockCurrentUser):
        """Test on_api_command when an invalid type is provided for 'addExcludeRegion'."""
        mockCurrentUser.is_anonymous.return_value = False
        handlerMock = mock.Mock()

        unit = self._createPluginInstance()
        unit._handleAddExcludeRegion = handlerMock  # pylint: disable=protected-access

        result = unit.on_api_command(
            "addExcludeRegion",
            {
                "type": "UnsupportedType"
            }
        )

        handlerMock.assert_not_called()
        self.assertEqual(len(result), 2, "The result should have two items")
        self.assertEqual(result[1], 400, "A 400 response should be generated")

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_updateExcludeRegion_RectangularRegion(self, mockCurrentUser):
        """Test on_api_command for the 'updateExcludeRegion' command and a RectangularRegion."""
        mockCurrentUser.is_anonymous.return_value = False
        handlerMock = mock.Mock()
        handlerMock.return_value = "expectedResult"

        unit = self._createPluginInstance()
        unit._handleUpdateExcludeRegion = handlerMock  # pylint: disable=protected-access

        result = unit.on_api_command(
            "updateExcludeRegion",
            {
                "type": "RectangularRegion",
                "x1": 0,
                "y1": 0,
                "x2": 10,
                "y2": 10
            }
        )

        handlerMock.assert_called_with(InstanceOf(RectangularRegion))
        self.assertEqual(result, "expectedResult", "The expected result should be returned")

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_updateExcludeRegion_CircularRegion(self, mockCurrentUser):
        """Test the on_api_command method for the 'updateExcludeRegion' command."""
        mockCurrentUser.is_anonymous.return_value = False
        handlerMock = mock.Mock()
        handlerMock.return_value = "expectedResult"

        unit = self._createPluginInstance()
        unit._handleUpdateExcludeRegion = handlerMock  # pylint: disable=protected-access

        result = unit.on_api_command(
            "updateExcludeRegion",
            {
                "type": "CircularRegion",
                "cx": 0,
                "cy": 0,
                "radius": 10
            }
        )

        handlerMock.assert_called_with(InstanceOf(CircularRegion))
        self.assertEqual(result, "expectedResult", "The expected result should be returned")

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_updateExcludeRegion_unsupportedType(self, mockCurrentUser):
        """Test on_api_command when an invalid type is provided for 'updateExcludeRegion'."""
        mockCurrentUser.is_anonymous.return_value = False
        handlerMock = mock.Mock()

        unit = self._createPluginInstance()
        unit._handleUpdateExcludeRegion = handlerMock  # pylint: disable=protected-access

        result = unit.on_api_command(
            "updateExcludeRegion",
            {
                "type": "UnsupportedType"
            }
        )

        handlerMock.assert_not_called()
        self.assertEqual(len(result), 2, "The result should have two items")
        self.assertEqual(result[1], 400, "A 400 response should be generated")

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_deleteExcludeRegion(self, mockCurrentUser):
        """Test on_api_command for the 'deleteExcludeRegion' command."""
        mockCurrentUser.is_anonymous.return_value = False
        handlerMock = mock.Mock()
        handlerMock.return_value = "expectedResult"

        unit = self._createPluginInstance()
        unit._handleDeleteExcludeRegion = handlerMock  # pylint: disable=protected-access

        result = unit.on_api_command(
            "deleteExcludeRegion",
            {
                "id": "someId"
            }
        )

        handlerMock.assert_called_with("someId")
        self.assertEqual(result, "expectedResult", "The expected result should be returned")

    @mock.patch.multiple('octoprint_excluderegion', current_user=mock.DEFAULT, flask=mock.DEFAULT)
    def test_on_api_get_unauthenticated(self, current_user, flask):  # pylint: disable=invalid-name
        """Test the on_api_get method for an unauthenticated user."""
        current_user.is_anonymous.return_value = True
        flask.jsonify.return_value = "expectedResult"

        testRegion = CircularRegion(x=0, y=0, radius=10, id="myId")

        unit = self._createPluginInstance()
        unit.state.excludedRegions = [testRegion]
        mockRequest = mock.Mock()

        result = unit.on_api_get(mockRequest)

        self.assertEqual(result, "expectedResult", "The expected result should be returned")
        flask.jsonify.assert_called_with(excluded_regions=[testRegion.toDict()])

    @mock.patch.multiple('octoprint_excluderegion', current_user=mock.DEFAULT, flask=mock.DEFAULT)
    def test_on_api_get_authenticated(self, current_user, flask):  # pylint: disable=invalid-name
        """Test the on_api_get method for an authenticated user."""
        current_user.is_anonymous.return_value = False
        flask.jsonify.return_value = "expectedResult"

        testRegion = CircularRegion(x=0, y=0, radius=10, id="myId")

        unit = self._createPluginInstance()
        unit.state.excludedRegions = [testRegion]
        mockRequest = mock.Mock()

        result = unit.on_api_get(mockRequest)

        self.assertEqual(result, "expectedResult", "The expected result should be returned")
        flask.jsonify.assert_called_with(excluded_regions=[testRegion.toDict()])

    # ~~ EventHandlerPlugin

    def test_on_event_FILE_SELECTED(self):
        """Test the on_event method when a FILE_SELECTED event is received."""
        handlerMock = mock.Mock()

        unit = self._createPluginInstance()
        unit.state = mock.Mock()
        unit._notifyExcludedRegionsChanged = handlerMock  # pylint: disable=protected-access

        mockPayload = mock.Mock()
        unit.on_event(Events.FILE_SELECTED, mockPayload)

        unit.state.resetState.assert_called_with(True)
        handlerMock.assert_called_with()

    def test_on_event_SETTINGS_UPDATED(self):
        """Test the on_event method when a SETTINGS_UPDATED event is received."""
        handlerMock = mock.Mock()

        unit = self._createPluginInstance()
        unit._handleSettingsUpdated = handlerMock  # pylint: disable=protected-access

        mockPayload = mock.Mock()
        unit.on_event(Events.SETTINGS_UPDATED, mockPayload)

        handlerMock.assert_called()

    def test_on_event_PRINT_STARTED(self):
        """Test the on_event method when a PRINT_STARTED event is received."""
        unit = self._createPluginInstance()
        unit._activePrintJob = False  # pylint: disable=protected-access
        unit.state = mock.Mock()

        mockPayload = mock.Mock()
        unit.on_event(Events.PRINT_STARTED, mockPayload)

        unit.state.resetState.assert_called_with()
        self.assertTrue(unit.isActivePrintJob, "isActivePrintJob should report True")

    def _test_on_event_stopPrinting(self, eventType, clearRegions):
        """Test the on_event method when an event is received that indicates printing stopped."""
        handlerMock = mock.Mock()

        unit = self._createPluginInstance()
        unit.state = mock.Mock()
        unit._notifyExcludedRegionsChanged = handlerMock  # pylint: disable=protected-access
        unit._activePrintJob = True  # pylint: disable=protected-access
        unit.clearRegionsAfterPrintFinishes = clearRegions

        mockPayload = mock.Mock()
        unit.on_event(eventType, mockPayload)

        self.assertFalse(unit.isActivePrintJob, "isActivePrintJob should report False")

        if (clearRegions):
            unit.state.resetState.assert_called_with(True)
            handlerMock.assert_called_with()

    def test_on_event_PRINT_DONE(self):
        """Test the on_event method when a PRINT_DONE event is received."""
        self._test_on_event_stopPrinting(Events.PRINT_DONE, False)
        self._test_on_event_stopPrinting(Events.PRINT_DONE, True)

    def test_on_event_PRINT_FAILED(self):
        """Test the on_event method when a PRINT_FAILED event is received."""
        self._test_on_event_stopPrinting(Events.PRINT_FAILED, False)
        self._test_on_event_stopPrinting(Events.PRINT_FAILED, True)

    def test_on_event_PRINT_CANCELLING(self):
        """Test the on_event method when a PRINT_CANCELLING event is received."""
        self._test_on_event_stopPrinting(Events.PRINT_CANCELLING, False)
        self._test_on_event_stopPrinting(Events.PRINT_CANCELLING, True)

    def test_on_event_PRINT_CANCELLED(self):
        """Test the on_event method when a PRINT_CANCELLED event is received."""
        self._test_on_event_stopPrinting(Events.PRINT_CANCELLED, False)
        self._test_on_event_stopPrinting(Events.PRINT_CANCELLED, True)

    def test_on_event_ERROR(self):
        """Test the on_event method when an ERROR event is received."""
        self._test_on_event_stopPrinting(Events.ERROR, False)
        self._test_on_event_stopPrinting(Events.ERROR, True)

    # ~~ ExcludeRegionPlugin

    def test_isActivePrintJob_read_only(self):
        """Tests isActivePrintJob to ensure it is a read-only property."""
        unit = self._createPluginInstance()

        with self.assertRaises(AttributeError):
            unit.isActivePrintJob = True

# TODO: loggingMode setter
#   - When the new mode is the same as the old mode
#   - When an invalid mode is provided
#   - LOG_MODE_DEDICATED: Create _pluginLoggingHandler and register it, propagate = False
#   - LOG_MODE_BOTH: Create _pluginLoggingHandler and register it, propagate = True
#   - LOG_MODE_OCTOPRINT: Remove the _pluginLoggingHandler, propagate = True

# TODO: loggingMode getter

# TODO: _handleAddExcludeRegion
#   - invokes state.addRegion
#   - invokes _notifyExcludedRegionsChanged
#   - returns 409 response if ValueError raised

# TODO: _handleDeleteExcludeRegion
#   - invokes state.deleteRegion
#   - invokes _notifyExcludedRegionsChanged if state.deleteRegion returns true
#   - returns 409 response if not mayShrinkRegionsWhilePrinting and isActivePrintJob

# TODO: _handleUpdateExcludeRegion
#   - invokes state.replaceRegion
#   - invokes _notifyExcludedRegionsChanged if state.replaceRegion succeeds
#   - returns 409 response if ValueError raised

# TODO: _notifyExcludedRegionsChanged

# TODO: _splitGcodeScript

# TODO: _handleSettingsUpdated

# TODO: handleGcodeQueuing

# TODO: handleAtCommandQueuing
