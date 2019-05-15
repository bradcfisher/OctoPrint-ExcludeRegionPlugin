# coding=utf-8
"""Unit tests for the processExtendedGcode methods of the ExcludeRegionState class."""

from __future__ import absolute_import
from collections import OrderedDict

import mock
from callee.operators import In as AnyIn

from octoprint_excluderegion.ExcludeRegionState import ExcludeRegionState
from octoprint_excluderegion.ExcludedGcode \
    import EXCLUDE_ALL, EXCLUDE_EXCEPT_FIRST, EXCLUDE_EXCEPT_LAST, EXCLUDE_MERGE

from .utils import TestCase


class ExcludeRegionStateProcessExtendedGcodeTests(
        TestCase
):  # xxpylint: xdisable=too-many-public-methods
    """Unit tests for the processExtendedGcode methods of the ExcludeRegionState class."""

    def test_processExtendedGcodeEntry_EXCLUDE_ALL(self):
        """Test processExtendedGcodeEntry when the mode is EXCLUDE_ALL."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = OrderedDict()

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_ALL,
            "G1 X1 Y2", "G1"
        )

        self.assertEqual(
            unit.pendingCommands, OrderedDict(),
            "pendingCommands should not be updated."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_MERGE_noPendingArgs_noCmdArgs(self):
        """Test processExtendedGcodeEntry / EXCLUDE_MERGE if no pending args and no command args."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = OrderedDict()

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_MERGE,
            "G1", "G1"
        )

        self.assertEqual(
            unit.pendingCommands, OrderedDict([("G1", {})]),
            "pendingCommands should be updated."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_MERGE_noPendingArgs_cmdHasArgs(self):
        """Test processExtendedGcodeEntry / EXCLUDE_MERGE if no pending args, and cmd with args."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = OrderedDict()

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_MERGE,
            "G1 X1 Y2", "G1"
        )

        self.assertEqual(
            unit.pendingCommands, OrderedDict([("G1", {"X": "1", "Y": "2"})]),
            "pendingCommands should be updated with the command arguments."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_MERGE_hasPendingArgs_noCmdArgs(self):
        """Test processExtendedGcodeEntry / EXCLUDE_MERGE if pending args and no command args."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = OrderedDict([("G1", {"X": "10"}), ("M117", "M117 Test")])

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_MERGE,
            "G1", "G1"
        )

        # Order of elements should be updated
        self.assertEqual(
            unit.pendingCommands,
            OrderedDict([
                ("M117", "M117 Test"),
                ("G1", {"X": "10"})
            ]),
            "pendingCommands should be updated with new argument values."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_MERGE_hasPendingArgs_cmdHasArgs(self):
        """Test processExtendedGcodeEntry / EXCLUDE_MERGE if pending args and command with args."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = OrderedDict([
            ("G1", {"X": "10", "Z": "20"}),
            ("M117", "M117 Test")
        ])

        # Use upper and lower case args to test case-sensitivity
        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_MERGE,
            "G1 x1 Y2", "G1"
        )

        # Order of elements and parameter values should be updated
        self.assertEqual(
            unit.pendingCommands,
            OrderedDict([
                ("M117", "M117 Test"),
                ("G1", {"X": "1", "Y": "2", "Z": "20"})
            ]),
            "pendingCommands should be updated with new argument values."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_EXCEPT_FIRST_noYetSeen(self):
        """Test processExtendedGcodeEntry/EXCLUDE_EXCEPT_FIRST for a Gcode not yet seen."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = OrderedDict([("M117", "M117 Test")])

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_EXCEPT_FIRST,
            "G1 X1 Y2", "G1"
        )

        # Should be appended to end
        self.assertEqual(
            unit.pendingCommands,
            OrderedDict([
                ("M117", "M117 Test"),
                ("G1", "G1 X1 Y2")
            ]),
            "pendingCommands should be updated with new command string."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_EXCEPT_FIRST_alreadySeen(self):
        """Test processExtendedGcodeEntry / EXCLUDE_EXCEPT_FIRST for a Gcode already seen."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = OrderedDict([
            ("G1", "G1 E3 Z4"),
            ("M117", "M117 Test")
        ])

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_EXCEPT_FIRST,
            "G1 X1 Y2", "G1"
        )

        # Previous command entry should not be affected
        self.assertEqual(
            unit.pendingCommands,
            OrderedDict([
                ("G1", "G1 E3 Z4"),
                ("M117", "M117 Test")
            ]),
            "pendingCommands should not be updated."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_EXCEPT_LAST_notYetSeen(self):
        """Test processExtendedGcodeEntry / EXCLUDE_EXCEPT_LAST for a Gcode not yet seen."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = OrderedDict([("M117", "M117 Test")])

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_EXCEPT_LAST,
            "G1 X1 Y2", "G1"
        )

        # Command should be appended to end of pendingCommands
        self.assertEqual(
            unit.pendingCommands,
            OrderedDict([
                ("M117", "M117 Test"),
                ("G1", "G1 X1 Y2")
            ]),
            "pendingCommands should be updated with new command string."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcodeEntry_EXCLUDE_EXCEPT_LAST_alreadySeen(self):
        """Test processExtendedGcodeEntry / EXCLUDE_EXCEPT_LAST for a Gcode already seen."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.pendingCommands = OrderedDict([
            ("G1", "G1 E3 Z4"),
            ("M117", "M117 Test")
        ])

        result = unit._processExtendedGcodeEntry(  # pylint: disable=protected-access
            EXCLUDE_EXCEPT_LAST,
            "G1 X1 Y2", "G1"
        )

        # Command should be updated and moved to end of pendingCommands
        self.assertEqual(
            unit.pendingCommands,
            OrderedDict([
                ("M117", "M117 Test"),
                ("G1", "G1 X1 Y2")
            ]),
            "pendingCommands should be updated with new command string."
        )
        self.assertEqual(
            result, (None,),
            "The result should indicate to drop/ignore the command"
        )

    def test_processExtendedGcode_noGcode_excluding(self):
        """Test processExtendedGcode when excluding and no gcode provided."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.object(unit, 'extendedExcludeGcodes') as mockExtendedExcludeGcodes:
            unit.excluding = True

            result = unit.processExtendedGcode("someCommand", None, None)

            mockExtendedExcludeGcodes.get.assert_not_called()
            self.assertIsNone(result, "The return value should be None")

    def test_processExtendedGcode_noGcode_notExcluding(self):
        """Test processExtendedGcode when not excluding and no gcode provided."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.object(unit, 'extendedExcludeGcodes') as mockExtendedExcludeGcodes:
            unit.excluding = False

            result = unit.processExtendedGcode("someCommand", None, None)

            mockExtendedExcludeGcodes.get.assert_not_called()
            self.assertIsNone(result, "The return value should be None")

    def test_processExtendedGcode_excluding_noMatch(self):
        """Test processExtendedGcode when excluding and no entry matches."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.multiple(
            unit,
            extendedExcludeGcodes=mock.DEFAULT,
            _processExtendedGcodeEntry=mock.DEFAULT
        ) as mocks:
            unit.excluding = True
            mocks["extendedExcludeGcodes"].get.return_value = None

            result = unit.processExtendedGcode("G1 X1 Y2", "G1", None)

            mocks["extendedExcludeGcodes"].get.assert_called_with("G1")
            mocks["_processExtendedGcodeEntry"].assert_not_called()
            self.assertIsNone(result, "The return value should be None")

    def test_processExtendedGcode_excluding_matchExists(self):
        """Test processExtendedGcode when excluding and a matching entry exists."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.multiple(
            unit,
            extendedExcludeGcodes=mock.DEFAULT,
            _processExtendedGcodeEntry=mock.DEFAULT
        ) as mocks:
            unit.excluding = True
            mockEntry = mock.Mock(name="entry")
            mockEntry.mode = "expectedMode"
            mocks["extendedExcludeGcodes"].get.return_value = mockEntry
            mocks["_processExtendedGcodeEntry"].return_value = "expectedResult"

            result = unit.processExtendedGcode("G1 X1 Y2", "G1", None)

            mocks["extendedExcludeGcodes"].get.assert_called_with("G1")
            mocks["_processExtendedGcodeEntry"].assert_called_with("expectedMode", "G1 X1 Y2", "G1")
            self.assertEqual(
                result, "expectedResult",
                "The expected result of _processExtendedGcodeEntry should be returned"
            )

    def test_processExtendedGcode_notExcluding_matchExists(self):
        """Test processExtendedGcode when not excluding and a matching entry exists."""
        mockLogger = mock.Mock()
        mockLogger.isEnabledFor.return_value = False  # For coverage of logging condition
        unit = ExcludeRegionState(mockLogger)

        with mock.patch.multiple(
            unit,
            extendedExcludeGcodes=mock.DEFAULT,
            _processExtendedGcodeEntry=mock.DEFAULT
        ) as mocks:
            unit.excluding = False
            mockEntry = mock.Mock(name="entry")
            mockEntry.mode = "expectedMode"
            mocks["extendedExcludeGcodes"].get.return_value = mockEntry

            result = unit.processExtendedGcode(AnyIn(["G1 X1 Y2", "G1 Y2 X1"]), "G1", None)

            mocks["extendedExcludeGcodes"].get.assert_not_called()
            mocks["_processExtendedGcodeEntry"].assert_not_called()
            self.assertIsNone(result, "The return value should be None")
