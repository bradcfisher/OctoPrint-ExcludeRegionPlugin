# coding=utf-8
"""Unit tests for the ExcludeRegionPlugin class."""

from __future__ import absolute_import

import os
import mock
from callee.strings import String as AnyString
from callee.collections import Mapping as AnyMapping, Sequence as AnySequence
from callee.types import InstanceOf

from octoprint.events import Events
from octoprint.settings import settings as octoprintSettings

from octoprint_excluderegion import \
    ExcludeRegionPlugin, ExcludeRegionState, GcodeHandlers, \
    RectangularRegion, CircularRegion, \
    EXCLUDED_REGIONS_CHANGED

from .utils import TestCase


# Initialize the OctoPrint settings to defaults.
# This specifies a directory under the build folder here so it doesn't find a pre-existing
# configuration yaml file that it pulls unexpected settings from.
octoprintSettings(init=True, basedir=os.path.abspath(os.path.join(os.environ.get("BUILD_PY_DIR"), "test-workspace")))


def create_plugin_instance():
    """Create an ExcludeRegionPlugin instance with a mock logger, plugin manager, and settings."""
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


def simulate_isActivePrintJob(instance, activePrintJob):  # pylint: disable=invalid-name
    """Modify an ExludeRegionPlugin instance to indicate whether a print job is active."""
    instance._activePrintJob = activePrintJob  # pylint: disable=protected-access


class ExcludeRegionPluginTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for the ExcludeRegionPlugin class."""

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

    # ~~ AssetPlugin

    def _test_get_assets(self, testVersion, validationCallback=None):
        """Test the get_assets method under OctoPrint 1.3.9 or older."""
        import octoprint
        originalVersion = octoprint.__version__
        originalDisplayVersion = octoprint.__display_version__
        try:
            octoprint.__version__ = testVersion
            octoprint.__display_version__ = testVersion + "-test"

            unit = create_plugin_instance()

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
        unit = create_plugin_instance()

        result = unit.get_template_configs()

        self.assertEqual(len(result), 1, "The returned list should have one entry")

    # ~~ SimpleApiPlugin

    def test_get_api_commands(self):
        """Test the get_api_commands method."""
        unit = create_plugin_instance()

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

        unit = create_plugin_instance()

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

        unit = create_plugin_instance()

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

        unit = create_plugin_instance()
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

        unit = create_plugin_instance()
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

        unit = create_plugin_instance()
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

        unit = create_plugin_instance()
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

        unit = create_plugin_instance()
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

        unit = create_plugin_instance()
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

        unit = create_plugin_instance()
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

        unit = create_plugin_instance()
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

        unit = create_plugin_instance()
        unit.state.excludedRegions = [testRegion]
        mockRequest = mock.Mock()

        result = unit.on_api_get(mockRequest)

        self.assertEqual(result, "expectedResult", "The expected result should be returned")
        flask.jsonify.assert_called_with(excluded_regions=[testRegion.toDict()])

    # ~~ EventHandlerPlugin

    def test_on_event_unprocessedEvent(self):
        """Test the on_event method when an event is received that shouldn't cause any action."""
        unit = create_plugin_instance()

        mockPayload = mock.Mock()

        result = unit.on_event("ArbitraryEvent", mockPayload)

        self.assertIsNone(result, "The result should be None")

    def test_on_event_FILE_SELECTED(self):
        """Test the on_event method when a FILE_SELECTED event is received."""
        unit = create_plugin_instance()
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
        unit = create_plugin_instance()
        with mock.patch.object(unit, '_handleSettingsUpdated') as handlerMock:
            mockPayload = mock.Mock()
            result = unit.on_event(Events.SETTINGS_UPDATED, mockPayload)

            handlerMock.assert_called()
            self.assertIsNone(result, "The result should be None")

    def test_on_event_PRINT_STARTED(self):
        """Test the on_event method when a PRINT_STARTED event is received."""
        unit = create_plugin_instance()
        with mock.patch.object(unit, 'state') as stateMock:
            simulate_isActivePrintJob(unit, False)

            mockPayload = mock.Mock()

            result = unit.on_event(Events.PRINT_STARTED, mockPayload)

            stateMock.resetState.assert_called_with()
            self.assertTrue(unit.isActivePrintJob, "isActivePrintJob should report True")
            self.assertIsNone(result, "The result should be None")

    def _test_on_event_stopPrinting(self, eventType, clearRegions):
        """Test the on_event method when an event is received that indicates printing stopped."""
        unit = create_plugin_instance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            simulate_isActivePrintJob(unit, True)
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
        unit = create_plugin_instance()

        with self.assertRaises(AttributeError):
            unit.isActivePrintJob = True

    def test_handleAddExcludeRegion_success(self):
        """Test _handleAddExcludeRegion when state.addRegion succeeds."""
        unit = create_plugin_instance()
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
        unit = create_plugin_instance()
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
        unit = create_plugin_instance()
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
        unit = create_plugin_instance()
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
        unit = create_plugin_instance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            unit.mayShrinkRegionsWhilePrinting = True
            simulate_isActivePrintJob(unit, True)
            mocks["state"].deleteRegion.return_value = True

            result = unit._handleDeleteExcludeRegion("someId")  # pylint: disable=protected-access

            mocks["state"].deleteRegion.assert_called_with("someId")
            mocks["_notifyExcludedRegionsChanged"].assert_called()

            self.assertIsNone(result, "The result should be None")

    def test_handleDeleteExcludeRegion_no_del_while_printing(self):
        """Test _handleDeleteExcludeRegion when modification is NOT allowed while printing."""
        unit = create_plugin_instance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            unit.mayShrinkRegionsWhilePrinting = False
            simulate_isActivePrintJob(unit, True)
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
        unit = create_plugin_instance()
        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            unit.mayShrinkRegionsWhilePrinting = False
            simulate_isActivePrintJob(unit, False)

            mockRegion = mock.Mock()

            result = unit._handleUpdateExcludeRegion(mockRegion)  # pylint: disable=protected-access

            mocks["state"].replaceRegion.assert_called_with(mockRegion, False)
            mocks["_notifyExcludedRegionsChanged"].assert_called()

            self.assertIsNone(result, "The result should be None")

    def test_handleUpdateExcludeRegion_ValueError(self):
        """Test _handleUpdateExcludeRegion when a ValueError is raised."""
        unit = create_plugin_instance()

        with mock.patch.multiple(
            unit,
            state=mock.DEFAULT,
            _notifyExcludedRegionsChanged=mock.DEFAULT
        ) as mocks:
            unit.mayShrinkRegionsWhilePrinting = False
            simulate_isActivePrintJob(unit, True)
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
        unit = create_plugin_instance()

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
