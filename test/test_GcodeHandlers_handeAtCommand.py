# coding=utf-8
"""Unit tests for the handleAtCommand method of the GcodeHandlers class."""

from __future__ import absolute_import

import mock

from octoprint_excluderegion.GcodeHandlers import GcodeHandlers
from octoprint_excluderegion.AtCommandAction import ENABLE_EXCLUSION, DISABLE_EXCLUSION

from .utils import TestCase


class GcodeHandlersHandleAtCommandTests(TestCase):
    """Unit tests for the handleAtCommand method of the GcodeHandlers class."""

    def test_handleAtCommand_noHandler(self):
        """Test handleAtCommand when no matching command handler is defined."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockCommInstance = mock.Mock()
        mockEntry = mock.Mock()

        mockState.atCommandActions = mock.Mock(wraps={"NoMatch": [mockEntry]})

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit.handleAtCommand(mockCommInstance, "NotDefined", "params")

        mockState.atCommandActions.get.assert_called_with("NotDefined")
        mockEntry.matches.assert_not_called()
        mockState.enableExclusion.assert_not_called()
        mockState.disableExclusion.assert_not_called()
        mockCommInstance.sendCommand.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handleAtCommand_oneHandler_noParamMatch(self):
        """Test handleAtCommand when one command handler is defined, but the params don't match."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockCommInstance = mock.Mock()
        mockEntry = mock.Mock()
        mockEntry.matches.return_value = None

        mockState.atCommandActions = mock.Mock(wraps={"DefinedCommand": [mockEntry]})

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit.handleAtCommand(mockCommInstance, "DefinedCommand", "params")

        mockState.atCommandActions.get.assert_called_with("DefinedCommand")
        mockEntry.matches.assert_called_with("DefinedCommand", "params")
        mockState.enableExclusion.assert_not_called()
        mockState.disableExclusion.assert_not_called()
        mockCommInstance.sendCommand.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handleAtCommand_multipleHandlers_noParamMatch(self):
        """Test handleAtCommand when multiple command handlers defined, but no param matches."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockCommInstance = mock.Mock()

        mockEntry1 = mock.Mock()
        mockEntry1.matches.return_value = None

        mockEntry2 = mock.Mock()
        mockEntry2.matches.return_value = None

        mockState.atCommandActions = mock.Mock(wraps={"DefinedCommand": [mockEntry1, mockEntry2]})

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit.handleAtCommand(mockCommInstance, "DefinedCommand", "params")

        mockState.atCommandActions.get.assert_called_with("DefinedCommand")
        mockEntry1.matches.assert_called_with("DefinedCommand", "params")
        mockEntry2.matches.assert_called_with("DefinedCommand", "params")
        mockState.enableExclusion.assert_not_called()
        mockState.disableExclusion.assert_not_called()
        mockCommInstance.sendCommand.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handleAtCommand_oneHandler_match_unsupported_action(self):
        """Test handleAtCommand with one matching handler that specifies an unsupported action."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockCommInstance = mock.Mock()
        mockEntry = mock.Mock()
        mockEntry.action = "unsupported"
        mockEntry.matches.return_value = True

        mockState.atCommandActions = mock.Mock(wraps={"DefinedCommand": [mockEntry]})

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit.handleAtCommand(mockCommInstance, "DefinedCommand", "params")

        mockState.atCommandActions.get.assert_called_with("DefinedCommand")
        mockEntry.matches.assert_called_with("DefinedCommand", "params")
        mockState.enableExclusion.assert_not_called()
        mockState.disableExclusion.assert_not_called()
        mockCommInstance.sendCommand.assert_not_called()

        mockLogger.warn.assert_called()

        self.assertIsNone(result, "The result should be None")

    def test_handleAtCommand_oneHandler_match_ENABLE_EXCLUSION(self):
        """Test handleAtCommand with one matching handler that enables exclusion."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockCommInstance = mock.Mock()
        mockEntry = mock.Mock()
        mockEntry.action = ENABLE_EXCLUSION
        mockEntry.matches.return_value = True

        mockState.atCommandActions = mock.Mock(wraps={"DefinedCommand": [mockEntry]})

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit.handleAtCommand(mockCommInstance, "DefinedCommand", "params")

        mockState.atCommandActions.get.assert_called_with("DefinedCommand")
        mockEntry.matches.assert_called_with("DefinedCommand", "params")
        mockState.enableExclusion.assert_called_once()
        mockState.disableExclusion.assert_not_called()
        mockCommInstance.sendCommand.assert_not_called()

        self.assertIsNone(result, "The result should be None")

    def test_handleAtCommand_oneHandler_match_DISABLE_EXCLUSION(self):
        """Test handleAtCommand with one matching handler that disables exclusion."""
        mockLogger = mock.Mock()

        mockState = mock.Mock()
        mockState.disableExclusion.return_value = ["Command1", "Command2"]

        mockCommInstance = mock.Mock()

        mockEntry = mock.Mock()
        mockEntry.action = DISABLE_EXCLUSION
        mockEntry.matches.return_value = True

        mockState.atCommandActions = mock.Mock(wraps={"DefinedCommand": [mockEntry]})

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit.handleAtCommand(mockCommInstance, "DefinedCommand", "params")

        mockState.atCommandActions.get.assert_called_with("DefinedCommand")
        mockEntry.matches.assert_called_with("DefinedCommand", "params")
        mockState.enableExclusion.assert_not_called()
        mockState.disableExclusion.assert_called_once()
        mockCommInstance.sendCommand.assert_has_calls(
            [mock.call("Command1"), mock.call("Command2")]
        )

        self.assertIsNone(result, "The result should be None")

    def test_handleAtCommand_multipleHandlers_match(self):
        """Test handleAtCommand when multiple command handlers are defined and match."""
        mockLogger = mock.Mock()
        mockState = mock.Mock()
        mockCommInstance = mock.Mock()

        mockEntry1 = mock.Mock()
        mockEntry1.action = ENABLE_EXCLUSION
        mockEntry1.matches.return_value = True

        mockEntry2 = mock.Mock()
        mockEntry2.action = ENABLE_EXCLUSION
        mockEntry2.matches.return_value = True

        mockState.atCommandActions = mock.Mock(wraps={"DefinedCommand": [mockEntry1, mockEntry2]})

        unit = GcodeHandlers(mockState, mockLogger)

        result = unit.handleAtCommand(mockCommInstance, "DefinedCommand", "params")

        mockState.atCommandActions.get.assert_called_with("DefinedCommand")
        mockEntry1.matches.assert_called_with("DefinedCommand", "params")
        mockEntry2.matches.assert_called_with("DefinedCommand", "params")
        self.assertEqual(
            mockState.enableExclusion.call_count, 2,
            "enableExclusion should be called twice"
        )
        mockState.disableExclusion.assert_not_called()
        mockCommInstance.sendCommand.assert_not_called()

        self.assertIsNone(result, "The result should be None")
