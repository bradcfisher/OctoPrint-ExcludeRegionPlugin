# coding=utf-8
"""Unit tests for the basic functionality of the ExcludeRegionState class."""

from __future__ import absolute_import

import mock
from callee.strings import Regex as RegexMatcher

from octoprint_excluderegion.ExcludeRegionState \
    import ExcludeRegionState, build_command, IGNORE_GCODE_CMD
from octoprint_excluderegion.Position import Position
from octoprint_excluderegion.RectangularRegion import RectangularRegion
from octoprint_excluderegion.CircularRegion import CircularRegion

from .utils import TestCase


class ExcludeRegionStateBasicTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for the basic functionality of the ExcludeRegionState class."""

    expectedProperties = [
        "_logger", "g90InfluencesExtruder", "enteringExcludedRegionGcode",
        "exitingExcludedRegionGcode", "extendedExcludeGcodes", "atCommandActions",
        "excludedRegions", "position", "feedRate", "feedRateUnitMultiplier", "_exclusionEnabled",
        "excluding", "excludeStartTime", "numCommands", "numExcludedCommands", "lastRetraction",
        "lastPosition", "pendingCommands"
    ]

    def test_build_command_no_kwargs(self):
        """Test the build_command utility method when passed a GCode command and no kwargs."""
        cmd = build_command("G0")
        self.assertEqual(cmd, "G0", "The returned command should be 'G0'")

    def test_build_command_one_kwarg(self):
        """Test the build_command utility method when passed a GCode command and one kwargs."""
        cmd = build_command("G0", X=10)
        self.assertEqual(cmd, "G0 X10", "The returned command should be 'G0 X10'")

    def test_build_command_two_kwargs(self):
        """Test the build_command utility method when passed a GCode command and two kwargs."""
        cmd = build_command("G0", X=10, Y=20)

        self.assertRegexpMatches(cmd, "^G0 ", "The returned command should start with 'G0 '")
        # Due to kwargs, order of arguments is not guaranteed, and also is not required
        self.assertRegexpMatches(cmd, " X10( |$)", "The returned command should contain ' X10'")
        self.assertRegexpMatches(cmd, " Y20( |$)", "The returned command should contain ' Y20'")

    def _assert_default_resetState_properties(self, unit):
        """Test the value of properties that are always reset by the resetState method."""
        self.assertEqual(
            unit.position, Position(),
            "poosition should be a default Position instance"
        )
        self.assertEqual(unit.feedRate, 0, "feedRate should default to 0")
        self.assertEqual(
            unit.feedRateUnitMultiplier, 1,
            "feedRateUnitMultiplier should default to 1"
        )
        self.assertTrue(unit.isExclusionEnabled, "isExclusionEnabled should default to True")
        self.assertFalse(unit.excluding, "excluding should default to False")
        self.assertIsNone(unit.excludeStartTime, "excludeStartTime should default to None")
        self.assertEqual(unit.numExcludedCommands, 0, "numExcludedCommands should default to 0")
        self.assertEqual(unit.numCommands, 0, "numCommands should default to 0")
        self.assertIsNone(unit.lastRetraction, "lastRetraction should default to None")
        self.assertIsNone(unit.lastPosition, "lastPosition should default to None")
        self.assertEqual(
            unit.pendingCommands, {},
            "pendingCommands should default to an empty dict"
        )

    def test_constructor(self):
        """Test the constructor when passed a logger."""
        # pylint: disable=protected-access
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        self.assertIsInstance(unit, ExcludeRegionState)
        self.assertIs(unit._logger, mockLogger, "The logger should match the instance passed in")
        self.assertFalse(
            unit.g90InfluencesExtruder,
            "g90InfluencesExtruder should default to False"
        )
        self.assertIsNone(
            unit.enteringExcludedRegionGcode,
            "enteringExcludedRegionGcode should default to None"
        )
        self.assertIsNone(
            unit.exitingExcludedRegionGcode,
            "exitingExcludedRegionGcode should default to None"
        )
        self.assertEqual(
            unit.extendedExcludeGcodes, {},
            "extendedExcludeGcodes should default to an empty dict"
        )
        self.assertEqual(
            unit.atCommandActions, {},
            "atCommandActions should default to an empty dict"
        )

        self.assertEqual(
            unit.excludedRegions, [],
            "excludedRegions should default to an empty list"
        )

        self._assert_default_resetState_properties(unit)

        self.assertProperties(unit, ExcludeRegionStateBasicTests.expectedProperties)

    def test_constructor_no_logger(self):
        """Test the constructor when no logger is provided."""
        with self.assertRaises(AssertionError):
            ExcludeRegionState(None)

    @staticmethod
    def _resetStateSetup():
        """Create and initialize the instance to test the resetState method on."""
        # pylint: disable=protected-access
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.excludedRegions = ["abc"]
        unit.position.X_AXIS.current = 100
        unit.feedRate = 100
        unit.feedRateUnitMultiplier = 1234
        unit._exclusionEnabled = False
        unit.excluding = True
        unit.excludeStartTime = None
        unit.numExcludedCommands = 4321
        unit.numCommands = 6789
        unit.lastRetraction = "abc"
        unit.lastPosition = "123"
        unit.pendingCommands = {"a": 1}

        return unit

    def test_resetState_True(self):
        """Test the resetState method when passed true."""
        unit = self._resetStateSetup()

        unit.resetState(True)

        self.assertEqual(unit.excludedRegions, [], "excludedRegions should be an empty list")

        self._assert_default_resetState_properties(unit)

    def test_resetState_False(self):
        """Test the resetState method when passed false."""
        unit = self._resetStateSetup()

        unit.resetState(False)

        self.assertEqual(unit.excludedRegions, ["abc"], "excludedRegions should not be modified")

        self._assert_default_resetState_properties(unit)

    def test_getRegion_notExists(self):
        """Test the getRegion method when no such region is defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        self.assertIsNone(
            unit.getRegion("someId"),
            "getRegion return None when the region isn't defined"
        )

    def test_getRegion_exists(self):
        """Test the getRegion method when a matching region has been defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        aRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="anId")
        otherRegion = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="otherId")

        unit.addRegion(aRegion)
        unit.addRegion(otherRegion)

        self.assertIs(
            unit.getRegion("anId"),
            aRegion,
            "getRegion return the region matching the id when such a region is defined"
        )

        self.assertIs(
            unit.getRegion("otherId"),
            otherRegion,
            "getRegion return the region matching the id when such a region is defined"
        )

    def test_addRegion_newId(self):
        """Test the addRegion method when the ID has not yet been added."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        aRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="anId")
        otherRegion = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="otherId")

        unit.addRegion(aRegion)

        self.assertEqual(
            unit.excludedRegions, [aRegion],
            "The list of excluded regions should contain the new region"
        )

        unit.addRegion(otherRegion)

        self.assertEqual(
            unit.excludedRegions, [aRegion, otherRegion],
            "The list of excluded regions should contain both regions"
        )

    def test_addRegion_idExists(self):
        """Test the addRegion method when the ID already exists."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        aRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="anId")
        conflictingRegion = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="anId")

        unit.addRegion(aRegion)

        with self.assertRaises(ValueError):
            unit.addRegion(conflictingRegion)

    def test_deleteRegion_noRegions(self):
        """Test the deleteRegion method when no regions are defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        self.assertFalse(
            unit.deleteRegion("notFound"),
            "deleteRegion should return False when the region is not found (no regions defined)"
        )

    def test_deleteRegion_notFound(self):
        """Test the deleteRegion method when the specified region is not found."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        aRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="anId")
        unit.addRegion(aRegion)

        self.assertFalse(
            unit.deleteRegion("notFound"),
            "deleteRegion should return False when the region is not found"
        )
        self.assertEqual(
            unit.excludedRegions, [aRegion],
            "The excluded regions should not be modified by deleteRegion if the ID was not found"
        )

    def test_deleteRegion_found_single(self):
        """Test the deleteRegion method when the specified region is the only one defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        findRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="findId")
        unit.addRegion(findRegion)

        self.assertTrue(
            unit.deleteRegion("findId"),
            "deleteRegion should return True when the region is found and removed (single)"
        )
        self.assertEqual(
            unit.excludedRegions, [],
            "The excluded regions should be updated by deleteRegion if the ID is found (single)"
        )

    def test_deleteRegion_found_first(self):
        """Test the deleteRegion method when the specified region is first in the list."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        findRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="findId")
        otherRegion = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="otherId")

        unit.addRegion(findRegion)
        unit.addRegion(otherRegion)

        self.assertTrue(
            unit.deleteRegion("findId"),
            "deleteRegion should return True when the region is found and removed (first)"
        )
        self.assertEqual(
            unit.excludedRegions, [otherRegion],
            "The excluded regions should be updated by deleteRegion if the ID is found (first)"
        )

    def test_deleteRegion_found_last(self):
        """Test the deleteRegion method when the specified region is last in the list."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        findRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="findId")
        otherRegion = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="otherId")

        unit.addRegion(otherRegion)
        unit.addRegion(findRegion)

        self.assertTrue(
            unit.deleteRegion("findId"),
            "deleteRegion should return True when the region is found and removed (last)"
        )
        self.assertEqual(
            unit.excludedRegions, [otherRegion],
            "The excluded regions should be updated by deleteRegion if the ID is found (last)"
        )

    def test_deleteRegion_found_middle(self):
        """Test the deleteRegion method when the region is neither first nor last in the list."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        firstRegion = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="firstId")
        findRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="findId")
        lastRegion = RectangularRegion(x1=20, y1=20, x2=30, y2=30, id="lastId")

        unit.addRegion(firstRegion)
        unit.addRegion(findRegion)
        unit.addRegion(lastRegion)

        self.assertTrue(
            unit.deleteRegion("findId"),
            "deleteRegion should return True when the region is found and removed (middle)"
        )
        self.assertEqual(
            unit.excludedRegions, [firstRegion, lastRegion],
            "The excluded regions should be updated by deleteRegion if the ID is found (middle)"
        )

    def test_replaceRegion_missingId(self):
        """Test the replaceRegion method when the region procided doesn't have an assigned ID."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        newRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100)
        newRegion.id = None

        with self.assertRaises(ValueError):
            unit.replaceRegion(newRegion)

    def test_replaceRegion_noRegions(self):
        """Test the replaceRegion method when no regions are defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        newRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="someId")

        with self.assertRaises(ValueError):
            unit.replaceRegion(newRegion)

    def test_replaceRegion_notFound(self):
        """Test the replaceRegion method when the region is not found."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        existingRegion = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="otherId")
        newRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="someId")

        unit.addRegion(existingRegion)

        with self.assertRaises(ValueError):
            unit.replaceRegion(newRegion)

    def test_replaceRegion_found_single(self):
        """Test the replaceRegion method when the region matches the only one defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        regionToMatch = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="matchId")
        newRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="matchId")

        unit.addRegion(regionToMatch)

        unit.replaceRegion(newRegion)

        self.assertEqual(
            unit.excludedRegions, [newRegion],
            "The excluded regions should be updated by replaceRegion if the ID is found (single)"
        )

    def test_replaceRegion_found_first(self):
        """Test the replaceRegion method when the region matches the first in the list."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        regionToMatch = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="matchId")
        otherRegion = RectangularRegion(x1=20, y1=20, x2=30, y2=30, id="otherId")
        newRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="matchId")

        unit.addRegion(regionToMatch)
        unit.addRegion(otherRegion)

        unit.replaceRegion(newRegion)

        self.assertEqual(
            unit.excludedRegions, [newRegion, otherRegion],
            "The excluded regions should be updated by replaceRegion if the ID is found (first)"
        )

    def test_replaceRegion_found_last(self):
        """Test the replaceRegion method when the region matches the last in the list."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        regionToMatch = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="matchId")
        otherRegion = RectangularRegion(x1=20, y1=20, x2=30, y2=30, id="otherId")
        newRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="matchId")

        unit.addRegion(otherRegion)
        unit.addRegion(regionToMatch)

        unit.replaceRegion(newRegion)

        self.assertEqual(
            unit.excludedRegions, [otherRegion, newRegion],
            "The excluded regions should be updated by replaceRegion if the ID is found (last)"
        )

    def test_replaceRegion_found_middle(self):
        """Test the replaceRegion method when the matched region not first nor last in the list."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        firstRegion = RectangularRegion(x1=20, y1=20, x2=30, y2=30, id="firstId")
        regionToMatch = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="matchId")
        lastRegion = RectangularRegion(x1=30, y1=30, x2=40, y2=40, id="lastId")
        newRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="matchId")

        unit.addRegion(firstRegion)
        unit.addRegion(regionToMatch)
        unit.addRegion(lastRegion)

        unit.replaceRegion(newRegion)

        self.assertEqual(
            unit.excludedRegions, [firstRegion, newRegion, lastRegion],
            "The excluded regions should be updated by replaceRegion if the ID is found (last)"
        )

    def test_replaceRegion_found_mustContain_contained(self):
        """Test the replaceRegion method when mustContainOldRegion is True and a match is found."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        regionToMatch = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="matchId")
        newRegion = RectangularRegion(x1=0, y1=0, x2=100, y2=100, id="matchId")

        unit.addRegion(regionToMatch)

        unit.replaceRegion(newRegion, True)

        self.assertEqual(
            unit.excludedRegions, [newRegion],
            "The excluded regions should be updated by replaceRegion if the ID is found (contained)"
        )

    def test_replaceRegion_found_mustContain_notContained(self):
        """Test the replaceRegion method when mustContainOldRegion is True and no match is found."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        regionToMatch = RectangularRegion(x1=10, y1=10, x2=20, y2=20, id="matchId")
        newRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5, id="matchId")

        unit.addRegion(regionToMatch)

        with self.assertRaises(ValueError):
            unit.replaceRegion(newRegion, True)

        self.assertEqual(
            unit.excludedRegions, [regionToMatch],
            "The excluded regions should not be modified by replaceRegion (match, not contained)"
        )

    def test_isPointExcluded_noRegions(self):
        """Test the isPointExcluded method when no regions are defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        self.assertFalse(
            unit.isPointExcluded(0, 0),
            "(0,0) should NOT be excluded when no regions are defined"
        )
        self.assertFalse(
            unit.isPointExcluded(10, 10),
            "(10,10) should NOT be excluded when no regions are defined"
        )

    def test_isPointExcluded_oneRegion(self):
        """Test the isPointExcluded method when one region is defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        aRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5)
        unit.addRegion(aRegion)

        self.assertTrue(unit.isPointExcluded(0, 0), "(0,0) should be excluded (one region)")
        self.assertFalse(
            unit.isPointExcluded(10, 10),
            "(10,10) should NOT be excluded (one region)"
        )

    def test_isPointExcluded_multipleRegions(self):
        """Test the isPointExcluded method when multiple regions are defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        aRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5)
        anotherRegion = CircularRegion(cx=20, cy=20, r=10)

        unit.addRegion(aRegion)
        unit.addRegion(anotherRegion)

        self.assertTrue(unit.isPointExcluded(0, 0), "(0,0) should be excluded (mult regions)")
        self.assertFalse(
            unit.isPointExcluded(10, 10),
            "(10,10) should NOT be excluded (mult regions)"
        )

        self.assertTrue(unit.isPointExcluded(20, 20), "(20,20) should be excluded (mult regions)")
        self.assertFalse(
            unit.isPointExcluded(30, 10),
            "(30,10) should NOT be excluded (mult regions)"
        )

    def test_isPointExcluded_exclusionDisabled(self):
        """Test the isPointExcluded method when exclusion is diabled."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        aRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5)
        unit.addRegion(aRegion)
        unit.disableExclusion("Disable for test")

        self.assertFalse(
            unit.isPointExcluded(0, 0),
            "(0,0) should NOT be excluded (exclusion disabled)"
        )
        self.assertFalse(
            unit.isPointExcluded(10, 10),
            "(10,10) should NOT be excluded (exclusion disabled)"
        )

    # TODO: Test that isPointExcluded is not affected by the logical coordinate units in effect
    # TODO: Test that isAnyPointExcluded _IS_ affected by the logical coordinate units in effect

    def test_isAnyPointExcluded_noArguments(self):
        """Test the isAnyPointExcluded method when no arguments are provided."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        aRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5)
        unit.addRegion(aRegion)

        self.assertFalse(
            unit.isAnyPointExcluded(),
            "isAnyPointExcluded should return false when passed no arguments"
        )

    def test_isAnyPointExcluded_unmatchedPairs(self):
        """Test the isAnyPointExcluded method when an odd number of arguments are provided."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        aRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5)
        unit.addRegion(aRegion)

        with self.assertRaises(IndexError):
            unit.isAnyPointExcluded(0)

    def test_isAnyPointExcluded_noRegions(self):
        """Test the isAnyPointExcluded method when no regions are defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        self.assertFalse(
            unit.isAnyPointExcluded(0, 0),
            "(0,0) should NOT be excluded when no regions are defined"
        )
        self.assertFalse(
            unit.isAnyPointExcluded(10, 10),
            "(10,10) should NOT be excluded when no regions are defined"
        )
        self.assertFalse(
            unit.isAnyPointExcluded(0, 0, 10, 10),
            "Neither (0,0) nor (10,10) should be excluded when no regions are defined"
        )

    def test_isAnyPointExcluded_oneRegion(self):
        """Test the isAnyPointExcluded method when one region is defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        aRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5)
        unit.addRegion(aRegion)

        self.assertTrue(unit.isAnyPointExcluded(0, 0), "(0,0) should be excluded (one region)")
        self.assertFalse(
            unit.isAnyPointExcluded(10, 10),
            "(10,10) should NOT be excluded (one region)"
        )

    def test_isAnyPointExcluded_multRegions(self):
        """Test the isAnyPointExcluded method when multiple regions are defined."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        aRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5)
        anotherRegion = CircularRegion(cx=20, cy=20, r=10)

        unit.addRegion(aRegion)
        unit.addRegion(anotherRegion)

        self.assertTrue(unit.isAnyPointExcluded(0, 0), "(0,0) should be excluded (mult regions)")
        self.assertFalse(
            unit.isAnyPointExcluded(10, 10),
            "(10,10) should NOT be excluded (mult regions)"
        )

        self.assertTrue(
            unit.isAnyPointExcluded(20, 20),
            "(20,20) should be excluded (mult regions)"
        )
        self.assertFalse(
            unit.isAnyPointExcluded(30, 10),
            "(30,10) should NOT be excluded (mult regions)"
        )

        self.assertFalse(
            unit.isAnyPointExcluded(10, 10, 30, 10),
            "Neither (10,10) nor (30,10) should be excluded (mult regions)"
        )

    def test_isAnyPointExcluded_firstExcluded(self):
        """Test the isAnyPointExcluded method when the first point is excluded."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        aRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5)
        unit.addRegion(aRegion)

        self.assertTrue(unit.isAnyPointExcluded(0, 0, 10, 10), "(0,0) should be excluded (first)")

    def test_isAnyPointExcluded_lastExcluded(self):
        """Test the isAnyPointExcluded method when only the last point is excluded."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        aRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5)
        unit.addRegion(aRegion)

        self.assertTrue(unit.isAnyPointExcluded(10, 10, 0, 0), "(0,0) should be excluded (last)")

    def test_isAnyPointExcluded_middleExcluded(self):
        """Test the isAnyPointExcluded method a point other than the first or last is excluded."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        aRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5)
        unit.addRegion(aRegion)

        self.assertTrue(
            unit.isAnyPointExcluded(10, 10, 0, 0, 20, 20),
            "(0,0) should be excluded (middle)"
        )

    def test_isAnyPointExcluded_exclusionDisabled(self):
        """Test the isAnyPointExcluded method when exclusion is disabled."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        aRegion = RectangularRegion(x1=0, y1=0, x2=5, y2=5)
        unit.addRegion(aRegion)
        unit.disableExclusion("Disable for test")

        self.assertFalse(
            unit.isAnyPointExcluded(0, 0),
            "(0,0) should NOT be excluded (exclusion disabled)"
        )
        self.assertFalse(
            unit.isAnyPointExcluded(10, 10),
            "(10,10) should NOT be excluded (exclusion disabled)"
        )

    def test_isExclusionEnabled_enabled(self):
        """Test the isExclusionEnabled method when exclusion is enabled."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        self.assertTrue(unit.isExclusionEnabled(), "isExclusionEnabled should report True")

    def test_isExclusionEnabled_disabled(self):
        """Test the isExclusionEnabled method when exclusion is disabled."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.disableExclusion("Disable for test")

        self.assertFalse(unit.isExclusionEnabled(), "isExclusionEnabled should report False")

    @mock.patch.object(ExcludeRegionState, "exitExcludedRegion")
    def test_disableExclusion_exclusionDisabled(self, mockExitExcludeRegion):
        """Test the disableExclusion method when exclusion is already disabled."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.disableExclusion("Initial disable for test")
        mockLogger.reset_mock()

        returnedCommands = unit.disableExclusion("Second disable call, should be ignored")

        mockLogger.debug.assert_called_with(
            RegexMatcher("^Exclusion already disabled"),
            mock.ANY
        )
        mockExitExcludeRegion.assert_not_called()
        self.assertFalse(unit.isExclusionEnabled(), "isExclusionEnabled should report False")
        self.assertEqual(returnedCommands, [], "An empty list of commands should be returned")

    @mock.patch.object(ExcludeRegionState, "exitExcludedRegion")
    def test_disableExclusion_exclusionEnabled_notExcluding(self, mockExitExcludeRegion):
        """Test the disableExclusion method when exclusion is enabled and not excluding."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        returnedCommands = unit.disableExclusion("Disable for test")

        self.assertFalse(unit.isExclusionEnabled(), "isExclusionEnabled should report False")
        mockExitExcludeRegion.assert_not_called()
        self.assertEqual(returnedCommands, [], "An empty list of commands should be returned")

    @mock.patch.object(ExcludeRegionState, "exitExcludedRegion")
    def test_disableExclusion_exclusionEnabled_excluding(self, mockExitExcludeRegion):
        """Test the disableExclusion method when exclusion is enabled and currently excluding."""
        mockExitExcludeRegion.return_value = ["ABC"]
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.excluding = True

        returnedCommands = unit.disableExclusion("Redundant disable for test")

        self.assertFalse(unit.isExclusionEnabled(), "isExclusionEnabled should report False")
        mockExitExcludeRegion.assert_called_with(
            "Redundant disable for test",
            []
        )
        self.assertEqual(
            returnedCommands, ["ABC"],
            "The commands returned by exitExcludeRegion should be returned"
        )

    def test_enableExclusion_exclusionEnabled(self):
        """Test the enableExclusion method when exclusion is already enabled."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.enableExclusion("Redundant enable for test")

        mockLogger.debug.assert_called_with(
            RegexMatcher("^Exclusion already enabled"),
            mock.ANY
        )
        self.assertTrue(unit.isExclusionEnabled(), "isExclusionEnabled should report True")

    def test_enableExclusion_exclusionDisabled(self):
        """Test the enableExclusion method when exclusion is disabled."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.disableExclusion("Disable for test")

        unit.enableExclusion("Re-enable for test")

        self.assertTrue(unit.isExclusionEnabled(), "isExclusionEnabled should report True")

    def _assertUnitMultiplier(self, obj, unitMultiplier):
        """Assert that the specified unit multiplier is applied to all axes and the feed rate."""
        self.assertEqual(
            obj.feedRateUnitMultiplier, unitMultiplier,
            "The feedRateUnitMultiplier should be %s" % unitMultiplier
        )
        self.assertEqual(
            obj.position.X_AXIS.unitMultiplier, unitMultiplier,
            "The X_AXIS unitMultiplier should be %s" % unitMultiplier
        )
        self.assertEqual(
            obj.position.Y_AXIS.unitMultiplier, unitMultiplier,
            "The Y_AXIS unitMultiplier should be %s" % unitMultiplier
        )
        self.assertEqual(
            obj.position.Z_AXIS.unitMultiplier, unitMultiplier,
            "The Z_AXIS unitMultiplier should be %s" % unitMultiplier
        )
        self.assertEqual(
            obj.position.E_AXIS.unitMultiplier, unitMultiplier,
            "The E_AXIS unitMultiplier should be %s" % unitMultiplier
        )

    def test_setUnitMultiplier(self):
        """Test the setUnitMultiplier method."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)

        unit.setUnitMultiplier(10)
        self._assertUnitMultiplier(unit, 10)

        unit.setUnitMultiplier(1)
        self._assertUnitMultiplier(unit, 1)

    def _assertAbsoluteMode(self, obj, xyzAbsoluteMode, eAbsoluteMode):
        """Assert that the specified absolute mode is applied to all position axes."""
        self.assertEqual(
            obj.position.X_AXIS.absoluteMode, xyzAbsoluteMode,
            "The X_AXIS absoluteMode should be %s" % xyzAbsoluteMode
        )
        self.assertEqual(
            obj.position.Y_AXIS.absoluteMode, xyzAbsoluteMode,
            "The Y_AXIS absoluteMode should be %s" % xyzAbsoluteMode
        )
        self.assertEqual(
            obj.position.Z_AXIS.absoluteMode, xyzAbsoluteMode,
            "The Z_AXIS absoluteMode should be %s" % xyzAbsoluteMode
        )
        self.assertEqual(
            obj.position.E_AXIS.absoluteMode, eAbsoluteMode,
            "The E_AXIS absoluteMode should be %s" % eAbsoluteMode
        )

    def test_setAbsoluteMode_True(self):
        """Test the setAbsoluteMode method when passed True and g90InfluencesExtruder is False."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.g90InfluencesExtruder = False
        unit.position.setPositionAbsoluteMode(False)
        unit.position.setExtruderAbsoluteMode(False)

        unit.setAbsoluteMode(True)

        self._assertAbsoluteMode(unit, True, False)

    def test_setAbsoluteMode_True_g90InfluencesExtruder(self):
        """Test the setAbsoluteMode method when passed True and g90InfluencesExtruder is True."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.g90InfluencesExtruder = True
        unit.position.setPositionAbsoluteMode(False)
        unit.position.setExtruderAbsoluteMode(False)

        unit.setAbsoluteMode(True)

        self._assertAbsoluteMode(unit, True, True)

    def test_setAbsoluteMode_False(self):
        """Test the setAbsoluteMode method when passed False and g90InfluencesExtruder is False."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.g90InfluencesExtruder = False
        unit.position.setPositionAbsoluteMode(True)
        unit.position.setExtruderAbsoluteMode(True)

        unit.setAbsoluteMode(False)

        self._assertAbsoluteMode(unit, False, True)

    def test_setAbsoluteMode_False_g90InfluencesExtruder(self):
        """Test the setAbsoluteMode method when passed False and g90InfluencesExtruder is True."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.g90InfluencesExtruder = True
        unit.position.setPositionAbsoluteMode(True)
        unit.position.setExtruderAbsoluteMode(True)

        unit.setAbsoluteMode(False)

        self._assertAbsoluteMode(unit, False, False)

    def test_ignoreGcodeCommand(self):
        """Test the ignoreGcodeCommand method."""
        mockLogger = mock.Mock()
        unit = ExcludeRegionState(mockLogger)
        unit.numExcludedCommands = 10

        result = unit.ignoreGcodeCommand()

        self.assertEqual(
            result, IGNORE_GCODE_CMD,
            "ignoreGcodeCommand should return IGNORE_GCODE_CMD"
        )
        self.assertEqual(
            unit.numExcludedCommands, 11,
            "ignoreGcodeCommand should increment numExcludedCommands"
        )
