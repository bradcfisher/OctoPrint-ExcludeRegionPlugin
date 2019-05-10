# coding=utf-8
"""Unit tests for the ExcludeRegionPlugin class."""

from __future__ import absolute_import

import os
import mock
from callee.strings import String as AnyString
from callee.collections import Mapping as AnyMapping, Sequence as AnySequence
from callee.functions import Callable as AnyCallable
from callee.types import InstanceOf

from octoprint.events import Events
from octoprint.settings import settings as octoprintSettings, Settings

from octoprint_excluderegion import \
    ExcludeRegionPlugin, ExcludeRegionState, GcodeHandlers, \
    RectangularRegion, CircularRegion, \
    LOG_MODE_OCTOPRINT, LOG_MODE_DEDICATED, LOG_MODE_BOTH, \
    EXCLUDED_REGIONS_CHANGED

from octoprint_excluderegion.ExcludedGcode import ExcludedGcode, EXCLUDE_ALL
from octoprint_excluderegion.AtCommandAction \
    import AtCommandAction, ENABLE_EXCLUSION, DISABLE_EXCLUSION

from .utils import TestCase


class ExcludeRegionPluginTests(TestCase):  # pylint: disable=too-many-public-methods,too-many-lines
    """Unit tests for the ExcludeRegionPlugin class."""

    @classmethod
    def setUpClass(cls):
        """Perform global test initialization for the class."""
        # Initialize the OctoPrint settings to defaults.
        # This specifies a directory under the build folder here so it doesn't find a pre-existing
        # configuration yaml file that it pulls unexpected settings from.
        baseDir = os.path.abspath(os.path.join("build", "test-workspace"))
        octoprintSettings(init=True, basedir=baseDir)

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

    @staticmethod
    def _simulateIsActivePrintJob(instance, activePrintJob):
        """Modify an ExludeRegionPlugin instance to indicate whether a print job is active."""
        instance._activePrintJob = activePrintJob  # pylint: disable=protected-access

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

        with mock.patch.multiple(
            unit,
            create=True,
            _logger=mock.DEFAULT,
            _handleSettingsUpdated=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            # pylint: disable=protected-access
            unit._identifier = "test_excluderegion_identifier"
            unit._plugin_version = "test_version"

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

            mocks["_handleSettingsUpdated"].assert_called()
            mocks["_notifyExcludedRegionsChanged"].assert_called_with()

    @staticmethod
    def _createPluginInstance():
        from octoprint.plugin import plugin_settings

        unit = ExcludeRegionPlugin()

        # pylint: disable=protected-access
        unit._identifier = "excluderegion"
        unit._logger = mock.Mock(name="_logger")
        unit._plugin_manager = mock.Mock(name="_plugin_manager")
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

        self.assertEqual(
            result,
            (AnyString(), 403),
            "A 403 response should be generated"
        )

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_unknownCommand(self, mockCurrentUser):
        """Test on_api_command when an invalid command is provided."""
        mockCurrentUser.is_anonymous.return_value = False

        unit = self._createPluginInstance()

        result = unit.on_api_command("invalidCommand", {"type": "CircularRegion"})

        self.assertEqual(
            result,
            (AnyString(), 400),
            "A 400 response should be generated"
        )

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_addExcludeRegion_RectangularRegion(self, mockCurrentUser):
        """Test on_api_command for the 'addExcludeRegion' command and a RectangularRegion."""
        mockCurrentUser.is_anonymous.return_value = False

        unit = self._createPluginInstance()
        with mock.patch.object(unit, '_handleAddExcludeRegion') as handlerMock:
            handlerMock.return_value = "expectedResult"

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

        unit = self._createPluginInstance()
        with mock.patch.object(unit, '_handleAddExcludeRegion') as handlerMock:
            handlerMock.return_value = "expectedResult"

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

        unit = self._createPluginInstance()
        with mock.patch.object(unit, '_handleAddExcludeRegion') as handlerMock:
            result = unit.on_api_command(
                "addExcludeRegion",
                {
                    "type": "UnsupportedType"
                }
            )

            handlerMock.assert_not_called()
            self.assertEqual(
                result,
                (AnyString(), 400),
                "A 400 response should be generated"
            )

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_updateExcludeRegion_RectangularRegion(self, mockCurrentUser):
        """Test on_api_command for the 'updateExcludeRegion' command and a RectangularRegion."""
        mockCurrentUser.is_anonymous.return_value = False

        unit = self._createPluginInstance()
        with mock.patch.object(unit, '_handleUpdateExcludeRegion') as handlerMock:
            handlerMock.return_value = "expectedResult"

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

        unit = self._createPluginInstance()
        with mock.patch.object(unit, '_handleUpdateExcludeRegion') as handlerMock:
            handlerMock.return_value = "expectedResult"

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

        unit = self._createPluginInstance()
        with mock.patch.object(unit, '_handleUpdateExcludeRegion') as handlerMock:
            result = unit.on_api_command(
                "updateExcludeRegion",
                {
                    "type": "UnsupportedType"
                }
            )

            handlerMock.assert_not_called()
            self.assertEqual(
                result,
                (AnyString(), 400),
                "A 400 response should be generated"
            )

    @mock.patch('octoprint_excluderegion.current_user')
    def test_on_api_command_deleteExcludeRegion(self, mockCurrentUser):
        """Test on_api_command for the 'deleteExcludeRegion' command."""
        mockCurrentUser.is_anonymous.return_value = False

        unit = self._createPluginInstance()
        with mock.patch.object(unit, '_handleDeleteExcludeRegion') as handlerMock:
            handlerMock.return_value = "expectedResult"

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

    def test_on_event_unprocessedEvent(self):
        """Test the on_event method when an event is received that shouldn't cause any action."""
        unit = self._createPluginInstance()

        mockPayload = mock.Mock()

        result = unit.on_event("ArbitraryEvent", mockPayload)

        self.assertIsNone(result, "The result should be None")

    def test_on_event_FILE_SELECTED(self):
        """Test the on_event method when a FILE_SELECTED event is received."""
        unit = self._createPluginInstance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            mockPayload = mock.Mock()

            result = unit.on_event(Events.FILE_SELECTED, mockPayload)

            mocks["state"].resetState.assert_called_with(True)
            mocks["_notifyExcludedRegionsChanged"].assert_called_with()

            self.assertIsNone(result, "The result should be None")

    def test_on_event_SETTINGS_UPDATED(self):
        """Test the on_event method when a SETTINGS_UPDATED event is received."""
        unit = self._createPluginInstance()
        with mock.patch.object(unit, '_handleSettingsUpdated') as handlerMock:
            mockPayload = mock.Mock()
            result = unit.on_event(Events.SETTINGS_UPDATED, mockPayload)

            handlerMock.assert_called()
            self.assertIsNone(result, "The result should be None")

    def test_on_event_PRINT_STARTED(self):
        """Test the on_event method when a PRINT_STARTED event is received."""
        unit = self._createPluginInstance()
        with mock.patch.object(unit, 'state') as stateMock:
            self._simulateIsActivePrintJob(unit, False)

            mockPayload = mock.Mock()

            result = unit.on_event(Events.PRINT_STARTED, mockPayload)

            stateMock.resetState.assert_called_with()
            self.assertTrue(unit.isActivePrintJob, "isActivePrintJob should report True")
            self.assertIsNone(result, "The result should be None")

    def _test_on_event_stopPrinting(self, eventType, clearRegions):
        """Test the on_event method when an event is received that indicates printing stopped."""
        unit = self._createPluginInstance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            self._simulateIsActivePrintJob(unit, True)
            unit.clearRegionsAfterPrintFinishes = clearRegions

            mockPayload = mock.Mock()

            result = unit.on_event(eventType, mockPayload)

            self.assertFalse(unit.isActivePrintJob, "isActivePrintJob should report False")
            self.assertIsNone(result, "The result should be None")

            if (clearRegions):
                mocks['state'].resetState.assert_called_with(True)
                mocks['_notifyExcludedRegionsChanged'].assert_called_with()
            else:
                mocks['state'].resetState.assert_not_called()
                mocks['_notifyExcludedRegionsChanged'].assert_not_called()

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
        """Test isActivePrintJob to ensure it is a read-only property."""
        unit = self._createPluginInstance()

        with self.assertRaises(AttributeError):
            unit.isActivePrintJob = True

    def test_loggingMode_default(self):
        """Test the loggingMode default value."""
        unit = self._createPluginInstance()

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
        unit = self._createPluginInstance()

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
        unit = self._createPluginInstance()

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
        unit = self._createPluginInstance()
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
        unit = self._createPluginInstance()

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
        unit = self._createPluginInstance()
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
        unit = self._createPluginInstance()

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

    def test_handleAddExcludeRegion_success(self):
        """Test _handleAddExcludeRegion when state.addRegion succeeds."""
        unit = self._createPluginInstance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            mockRegion = mock.Mock()

            result = unit._handleAddExcludeRegion(mockRegion)  # pylint: disable=protected-access

            mocks["state"].addRegion.assert_called_with(mockRegion)
            mocks["_notifyExcludedRegionsChanged"].assert_called()

            self.assertIsNone(result, "The result should be None")

    def test_handleAddExcludeRegion_ValueError(self):
        """Test _handleAddExcludeRegion when state.addRegion raises a ValueError."""
        unit = self._createPluginInstance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            mocks["state"].addRegion.side_effect = ValueError("ExpectedError")

            mockRegion = mock.Mock()

            result = unit._handleAddExcludeRegion(mockRegion)  # pylint: disable=protected-access

            mocks["state"].addRegion.assert_called_with(mockRegion)
            mocks["_notifyExcludedRegionsChanged"].assert_not_called()

            self.assertEqual(
                result, ("ExpectedError", 409),
                "A 409 error response tuple should be returned"
            )

    def test_handleDeleteExcludeRegion_success_deleted(self):
        """Test _handleDeleteExcludeRegion when state.deleteRegion returns True."""
        unit = self._createPluginInstance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            mocks["state"].deleteRegion.return_value = True

            result = unit._handleDeleteExcludeRegion("someId")  # pylint: disable=protected-access

            mocks["state"].deleteRegion.assert_called_with("someId")
            mocks["_notifyExcludedRegionsChanged"].assert_called()

            self.assertIsNone(result, "The result should be None")

    def test_handleDeleteExcludeRegion_success_not_found(self):
        """Test _handleDeleteExcludeRegion when state.deleteRegion returns False."""
        unit = self._createPluginInstance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            mocks["state"].deleteRegion.return_value = False

            result = unit._handleDeleteExcludeRegion("someId")  # pylint: disable=protected-access

            mocks["state"].deleteRegion.assert_called_with("someId")
            mocks["_notifyExcludedRegionsChanged"].assert_not_called()

            self.assertIsNone(result, "The result should be None")

    def test_handleDeleteExcludeRegion_may_del_while_printing(self):
        """Test _handleDeleteExcludeRegion when modification is allowed while printing."""
        unit = self._createPluginInstance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            unit.mayShrinkRegionsWhilePrinting = True
            self._simulateIsActivePrintJob(unit, True)
            mocks["state"].deleteRegion.return_value = True

            result = unit._handleDeleteExcludeRegion("someId")  # pylint: disable=protected-access

            mocks["state"].deleteRegion.assert_called_with("someId")
            mocks["_notifyExcludedRegionsChanged"].assert_called()

            self.assertIsNone(result, "The result should be None")

    def test_handleDeleteExcludeRegion_no_del_while_printing(self):
        """Test _handleDeleteExcludeRegion when modification is NOT allowed while printing."""
        unit = self._createPluginInstance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            unit.mayShrinkRegionsWhilePrinting = False
            self._simulateIsActivePrintJob(unit, True)
            mocks["_notifyExcludedRegionsChanged"] = mock.Mock()

            result = unit._handleDeleteExcludeRegion("someId")  # pylint: disable=protected-access

            mocks["state"].deleteRegion.assert_not_called()
            mocks["_notifyExcludedRegionsChanged"].assert_not_called()

            self.assertEqual(
                result,
                (AnyString(), 409),
                "The result should be a Tuple indicating a 409 error"
            )

    def test_handleUpdateExcludeRegion_success(self):
        """Test _handleUpdateExcludeRegion when state.replaceRegion succeeds."""
        unit = self._createPluginInstance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            unit.mayShrinkRegionsWhilePrinting = False
            self._simulateIsActivePrintJob(unit, False)

            mockRegion = mock.Mock()

            result = unit._handleUpdateExcludeRegion(mockRegion)  # pylint: disable=protected-access

            mocks["state"].replaceRegion.assert_called_with(mockRegion, False)
            mocks["_notifyExcludedRegionsChanged"].assert_called()

            self.assertIsNone(result, "The result should be None")

    def test_handleUpdateExcludeRegion_ValueError(self):
        """Test _handleUpdateExcludeRegion when a ValueError is raised."""
        unit = self._createPluginInstance()

        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            unit.mayShrinkRegionsWhilePrinting = False
            self._simulateIsActivePrintJob(unit, True)
            mocks["state"].replaceRegion.side_effect = ValueError("ExpectedError")

            mockRegion = mock.Mock()

            result = unit._handleUpdateExcludeRegion(mockRegion)  # pylint: disable=protected-access

            mocks["state"].replaceRegion.assert_called_with(mockRegion, True)
            mocks["_notifyExcludedRegionsChanged"].assert_not_called()

            self.assertEqual(
                result, ("ExpectedError", 409),
                "A 409 error response tuple should be returned"
            )

    def test_notifyExcludedRegionsChanged(self):
        """Test the _notifyExcludedRegionsChanged method."""
        unit = self._createPluginInstance()

        # pylint: disable=protected-access
        result = unit._notifyExcludedRegionsChanged()

        unit._plugin_manager.send_plugin_message.assert_called_with(
            unit._identifier,  # pylint: disable=protected-access
            {
                "event": EXCLUDED_REGIONS_CHANGED,
                "excluded_regions": AnySequence(of=AnyMapping())
            }
        )

        self.assertIsNone(result, "The return value should be None")

    def test_splitGcodeScript_None(self):
        """Test _splitGcodeScript when None is provided."""
        unit = self._createPluginInstance()

        result = unit._splitGcodeScript(None)  # pylint: disable=protected-access

        self.assertIsNone(result, "The result should be None")

    def test_splitGcodeScript_empty(self):
        """Test _splitGcodeScript when an empty string is provided."""
        unit = self._createPluginInstance()

        result = unit._splitGcodeScript("")  # pylint: disable=protected-access

        self.assertIsNone(result, "The result should be None")

    def test_splitGcodeScript_ignore_comments_and_whitespace(self):
        """Test _splitGcodeScript when only comments and whitespace are provided."""
        unit = self._createPluginInstance()

        result = unit._splitGcodeScript(  # pylint: disable=protected-access
            ";This is a\n"
            "    \n" +
            "\n" +
            "   ;whitespace and comment TEST   "
        )

        self.assertIsNone(result, "The result should be None")

    def test_splitGcodeScript_lineBreaks(self):
        """Test _splitGcodeScript splits lines on CR, LF and CRLF."""
        unit = self._createPluginInstance()

        result = unit._splitGcodeScript(  # pylint: disable=protected-access
            "CR\r"
            "LF\n" +
            "CRLF\r\n" +
            "END"
        )

        self.assertEqual(result, ["CR", "LF", "CRLF", "END"])

    def test_splitGcodeScript_single_line(self):
        """Test _splitGcodeScript splits a single line (no EOL)."""
        unit = self._createPluginInstance()

        result = unit._splitGcodeScript("No EOL")  # pylint: disable=protected-access

        self.assertEqual(result, ["No EOL"])

    def test_splitGcodeScript_command_lines_with_comments_and_whitespace(self):
        """Test _splitGcodeScript when lines contain a combination of command, ws and comment."""
        unit = self._createPluginInstance()

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
        unit = self._createPluginInstance()

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

    def test_handleGcodeQueuing_notPrinting(self):
        """Test handleGcodeQueuing doesn't filter if not printing."""
        unit = self._createPluginInstance()
        with mock.patch.object(unit, 'gcodeHandlers') as mockGcodeHandlers:
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

            mockGcodeHandlers.handleGcode.assert_not_called()
            self.assertIsNone(result, "The result should be None")

    def test_handleGcodeQueuing_falsyGcode(self):
        """Test handleGcodeQueuing doesn't filter if the gcode parameter is falsy."""
        unit = self._createPluginInstance()
        with mock.patch.object(unit, 'gcodeHandlers') as mockGcodeHandlers:
            self._simulateIsActivePrintJob(unit, True)
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

            mockGcodeHandlers.handleGcode.assert_not_called()
            self.assertIsNone(result, "The result should be None")

    def test_handleGcodeQueuing_printing(self):
        """Test handleGcodeQueuing does filter when printing."""
        unit = self._createPluginInstance()
        with mock.patch.object(unit, 'gcodeHandlers') as mockGcodeHandlers:
            self._simulateIsActivePrintJob(unit, True)
            mockGcodeHandlers.handleGcode.return_value = "ExpectedResult"
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

            mockGcodeHandlers.handleGcode.assert_called_with("G0 X1 Y2", "G0", "subcode")
            self.assertEqual(result, "ExpectedResult", "The expected result should be returned")

    def test_handleAtCommandQueuing_notPrinting(self):
        """Test handleAtCommandQueuing won't execute the command if not printing."""
        unit = self._createPluginInstance()
        with mock.patch.object(unit, 'gcodeHandlers') as mockGcodeHandlers:
            self._simulateIsActivePrintJob(unit, False)

            mockCommInstance = mock.Mock(name="commInstance")

            result = unit.handleAtCommandQueuing(
                mockCommInstance,
                "queuing",
                "command",
                "parameters",
                "tags"
            )

            mockGcodeHandlers.handleAtCommand.assert_not_called()
            self.assertIsNone(result, "The result should be None")

    def test_handleAtCommandQueuing_printing(self):
        """Test handleAtCommandQueuing will execute the command if printing."""
        unit = self._createPluginInstance()
        with mock.patch.object(unit, 'gcodeHandlers') as mockGcodeHandlers:
            self._simulateIsActivePrintJob(unit, True)

            mockCommInstance = mock.Mock(name="commInstance")

            result = unit.handleAtCommandQueuing(
                mockCommInstance,
                "queuing",
                "command",
                "parameters",
                "tags"
            )

            mockGcodeHandlers.handleAtCommand.assert_called_with(
                mockCommInstance,
                "command",
                "parameters"
            )
            self.assertIsNone(result, "The result should be None")
