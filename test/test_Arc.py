# coding=utf-8
"""Unit tests for the Arc class."""

from __future__ import absolute_import

import math

from octoprint_excluderegion.Arc import Arc, normalize_radians, ROUND_PLACES
from octoprint_excluderegion.Rectangle import Rectangle

from .utils import TestCase, FloatAlmostEqual


class ArcTests(TestCase):  # pylint: disable=too-many-public-methods
    """Unit tests for the Arc class."""

    expectedProperties = [
        "cx", "cy", "radius",
        "startAngle", "endAngle", "sweep",
        "clockwise", "major",
        "bounds", "length",
        "x1", "y1", "x2", "y2"
    ]

    def test_constructor_args(self):
        """Test the constructor when passed non-keyword arguments."""
        with self.assertRaises(TypeError):
            Arc(1, 2, 3, 4)  # pylint: disable=too-many-function-args

    def test_default_constructor(self):
        """Test the constructor when passed no arguments."""
        unit = Arc()

        self.assertIsInstance(unit, Arc)
        self.assertEqual(unit.cx, 0, "cx should be 0")
        self.assertEqual(unit.cy, 0, "cy should be 0")
        self.assertEqual(unit.radius, 1, "radius should be 1")
        self.assertEqual(unit.startAngle, 0, "startAngle should be 0")
        self.assertEqual(unit.endAngle, math.pi * 2, "endAngle should be 2 * pi")
        self.assertEqual(unit.sweep, math.pi * 2, "sweep should be 2 * pi")
        self.assertEqual(unit.length, math.pi * 2, "length should be 2 * pi")
        self.assertFalse(unit.clockwise, "clockwise should be false")
        self.assertTrue(unit.major, "major should be true")
        self.assertEqual(1, unit.x1, "The start point x should be 1")
        self.assertEqual(0, unit.y1, "The start point y should be 0")
        self.assertEqual(1, unit.x2, "The end point x should be 1")
        self.assertEqual(0, unit.y2, "The end point y should be 0")
        self.assertEqual(
            Rectangle(x1=-1, y1=-1, x2=1, y2=1),
            unit.bounds,
            "The bounds should be (-1,-1)->(1,1)"
        )

        self.assertProperties(unit, ArcTests.expectedProperties)

    def test_constructor_counter_clockwise_circle(self):
        """Test the constructor for a counterclockwise circle."""
        unit = Arc(cx=1, cy=2, radius=3, startAngle=0, sweep=math.pi * 2)

        self.assertIsInstance(unit, Arc)
        self.assertEqual(unit.cx, 1, "cx should be 1")
        self.assertEqual(unit.cy, 2, "cy should be 2")
        self.assertEqual(unit.radius, 3, "radius should be 3")
        self.assertEqual(unit.startAngle, 0, "startAngle should be 0")
        self.assertEqual(unit.endAngle, math.pi * 2, "endAngle should be 2pi")
        self.assertEqual(unit.sweep, math.pi * 2, "sweep should be 2pi")
        self.assertEqual(unit.length, math.pi * 6, "length should be 6pi")
        self.assertFalse(unit.clockwise, "clockwise should be false")
        self.assertTrue(unit.major, "major should be true")

    def test_constructor_clockwise_circle(self):
        """Test the constructor for a clockwise circle."""
        unit = Arc(cx=1, cy=2, radius=3, startAngle=0, sweep=-math.pi * 2)

        self.assertIsInstance(unit, Arc)
        self.assertEqual(unit.cx, 1, "cx should be 1")
        self.assertEqual(unit.cy, 2, "cy should be 2")
        self.assertEqual(unit.radius, 3, "radius should be 3")
        self.assertEqual(unit.startAngle, 0, "startAngle should be 0")
        self.assertEqual(unit.endAngle, -math.pi * 2, "endAngle should be -2pi")
        self.assertEqual(unit.sweep, -math.pi * 2, "sweep should be -2pi")
        self.assertEqual(unit.length, math.pi * 6, "length should be 6pi")
        self.assertTrue(unit.clockwise, "clockwise should be true")
        self.assertTrue(unit.major, "major should be true")

    def test_constructor_counter_clockwise_Q0(self):
        """Test the constructor for a counterclockwise arc in Q0."""
        unit = Arc(cx=1, cy=2, radius=3, startAngle=0.1, sweep=1)

        self.assertIsInstance(unit, Arc)
        self.assertEqual(unit.cx, 1, "cx should be 1")
        self.assertEqual(unit.cy, 2, "cy should be 2")
        self.assertEqual(unit.radius, 3, "radius should be 3")
        self.assertEqual(unit.startAngle, 0.1, "startAngle should be 0.1")
        self.assertEqual(unit.endAngle, 1.1, "endAngle should be 1.1")
        self.assertEqual(unit.sweep, 1, "sweep should be 1")
        self.assertEqual(unit.length, 3, "length should be 3")
        self.assertFalse(unit.clockwise, "clockwise should be false")
        self.assertFalse(unit.major, "major should be false")

        x1 = math.cos(0.1) * 3 + 1
        y1 = math.sin(0.1) * 3 + 2
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(1.1) * 3 + 1
        y2 = math.sin(1.1) * 3 + 2
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

        self.assertProperties(unit, ArcTests.expectedProperties)

    def test_bounds_contained_in_Q1_CCW(self):
        """Test the bounds calc for a counterclockwise arc in Q1."""
        startAngle = math.pi / 2 + 0.1
        unit = Arc(startAngle=startAngle, sweep=1)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(1 + startAngle)
        y2 = math.sin(1 + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_contained_in_Q2_CCW(self):
        """Test the bounds calc for a counterclockwise arc in Q2."""
        startAngle = math.pi + 0.1
        unit = Arc(startAngle=startAngle, sweep=1)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(1 + startAngle)
        y2 = math.sin(1 + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_contained_in_Q3_CCW(self):
        """Test the bounds calc for a counterclockwise arc in Q3."""
        startAngle = math.pi * 1.5 + 0.1
        unit = Arc(startAngle=startAngle, sweep=1)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(1 + startAngle)
        y2 = math.sin(1 + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_constructor_clockwise_Q3(self):
        """Test the constructor for a clockwise arc in Q3."""
        unit = Arc(sweep=-1)

        self.assertTrue(unit.clockwise, "clockwise should be true")
        self.assertFalse(unit.major, "major should be false")
        self.assertEqual(unit.endAngle, -1, "endAngle should be -1")
        self.assertEqual(unit.sweep, -1, "sweep should be -1")
        self.assertEqual(unit.length, 1, "length should be 1")

        self.assertEqual(1, unit.x1, "The start point x should be 1")
        self.assertEqual(0, unit.y1, "The start point y should be 0")

        x = math.cos(1)
        y = -math.sin(1)
        self.assertEqual(FloatAlmostEqual(x), unit.x2, "The end point x should be " + repr(x))
        self.assertEqual(FloatAlmostEqual(y), unit.y2, "The end point y should be " + repr(y))

    def test_bounds_contained_in_Q0_CW(self):
        """Test the bounds calc for a clockwise arc in Q0."""
        startAngle = math.pi / 2 - 0.1
        unit = Arc(startAngle=startAngle, sweep=-1)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(-1 + startAngle)
        y2 = math.sin(-1 + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_contained_in_Q1_CW(self):
        """Test the bounds calc for a clockwise arc in Q1."""
        startAngle = math.pi - 0.1
        unit = Arc(startAngle=startAngle, sweep=-1)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(-1 + startAngle)
        y2 = math.sin(-1 + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_contained_in_Q2_CW(self):
        """Test the bounds calc for a clockwise arc in Q2."""
        startAngle = math.pi * 1.5 - 0.1
        unit = Arc(startAngle=startAngle, sweep=-1)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(-1 + startAngle)
        y2 = math.sin(-1 + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_crosses_into_Q0_CCW(self):
        """Test the bounds calc for a counterclockwise arc that passes from Q3 to Q0."""
        sweep = math.pi / 2
        startAngle = math.pi * 1.5 + 0.1

        unit = Arc(startAngle=startAngle, sweep=sweep)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(sweep + startAngle)
        y2 = math.sin(sweep + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        x2 = 1
        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_crosses_into_Q1_CCW(self):
        """Test the bounds calc for a counterclockwise arc that passes from Q0 to Q1."""
        sweep = math.pi / 2
        startAngle = 0.1

        unit = Arc(startAngle=startAngle, sweep=sweep)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(sweep + startAngle)
        y2 = math.sin(sweep + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        y2 = 1
        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_crosses_into_Q2_CCW(self):
        """Test the bounds calc for a counterclockwise arc that passes from Q1 to Q2."""
        sweep = math.pi / 2
        startAngle = math.pi / 2 + 0.1

        unit = Arc(startAngle=startAngle, sweep=sweep)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(sweep + startAngle)
        y2 = math.sin(sweep + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        x2 = -1
        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_crosses_into_Q3_CCW(self):
        """Test the bounds calc for a counterclockwise arc that passes from Q2 to Q3."""
        sweep = math.pi / 2
        startAngle = math.pi + 0.1

        unit = Arc(startAngle=startAngle, sweep=sweep)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(sweep + startAngle)
        y2 = math.sin(sweep + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        y2 = -1
        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_crosses_into_Q0_CW(self):
        """Test the bounds calc for a clockwise arc that passes from Q1 to Q0."""
        sweep = -math.pi / 2
        startAngle = math.pi / 2 - 0.1

        unit = Arc(startAngle=startAngle, sweep=sweep)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(sweep + startAngle)
        y2 = math.sin(sweep + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        x2 = 1
        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_crosses_into_Q1_CW(self):
        """Test the bounds calc for a clockwise arc that passes from Q2 to Q1."""
        sweep = -math.pi / 2
        startAngle = math.pi * 1.5 - 0.1

        unit = Arc(startAngle=startAngle, sweep=sweep)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(sweep + startAngle)
        y2 = math.sin(sweep + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        x2 = -1
        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_crosses_into_Q2_CW(self):
        """Test the bounds calc for a clockwise arc that passes from Q3 to Q2."""
        sweep = -math.pi / 2
        startAngle = -0.1

        unit = Arc(startAngle=startAngle, sweep=sweep)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(sweep + startAngle)
        y2 = math.sin(sweep + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        y2 = -1
        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_bounds_crosses_into_Q3_CW(self):
        """Test the bounds calc for a clockwise arc that passes from Q0 to Q3."""
        sweep = -math.pi / 2
        startAngle = math.pi/2 - 0.1

        unit = Arc(startAngle=startAngle, sweep=sweep)

        x1 = math.cos(startAngle)
        y1 = math.sin(startAngle)
        self.assertEqual(FloatAlmostEqual(x1), unit.x1, "The start point x should be " + repr(x1))
        self.assertEqual(FloatAlmostEqual(y1), unit.y1, "The start point y should be " + repr(y1))

        x2 = math.cos(sweep + startAngle)
        y2 = math.sin(sweep + startAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

        x2 = 1
        expected = Rectangle(
            x1=round(x1, ROUND_PLACES), y1=round(y1, ROUND_PLACES),
            x2=round(x2, ROUND_PLACES), y2=round(y2, ROUND_PLACES)
        )
        self.assertEqual(
            expected,
            unit.bounds,
            "The bounds should be ({},{})->({},{})".format(
                expected.x1, expected.y1, expected.x2, expected.y2
            )
        )

    def test_angleToSweep_positive_CCW_lt_start(self):
        """Test angleToSweep for a positive angle lt the startAngle of a CCW arc."""
        angle = 0
        arc = Arc(startAngle=0.1, sweep=1)

        result = arc.angleToSweep(angle)

        self.assertEqual(
            FloatAlmostEqual(2*math.pi - 0.1, places=ROUND_PLACES),
            result,
            "It should equal 2pi-0.1"
        )

    def test_angleToSweep_positive_CCW_gt_start(self):
        """Test angleToSweep for a positive angle gt the startAngle of a CCW arc."""
        angle = 2 * math.pi + 1.1
        arc = Arc(startAngle=0.1, sweep=1)

        result = arc.angleToSweep(angle)

        self.assertEqual(
            FloatAlmostEqual(1, places=ROUND_PLACES),
            result,
            "It should equal 1"
        )

    def test_angleToSweep_negative_CCW_lt_start(self):
        """Test angleToSweep for a negative angle lt the startAngle of a CCW arc."""
        angle = -2 * math.pi
        arc = Arc(startAngle=0.1, sweep=1)

        result = arc.angleToSweep(angle)

        self.assertEqual(
            FloatAlmostEqual(2*math.pi - 0.1, places=ROUND_PLACES),
            result,
            "It should equal 2pi-0.1"
        )

    def test_angleToSweep_negative_CCW_gt_start(self):
        """Test angleToSweep for a negative angle gt the startAngle of a CCW arc."""
        angle = -0.1
        arc = Arc(startAngle=0.1, sweep=1)

        result = arc.angleToSweep(angle)

        self.assertEqual(
            FloatAlmostEqual(2 * math.pi - 0.2, places=ROUND_PLACES),
            result,
            "It should equal 2PI - 0.2"
        )

    def test_angleToSweep_positive_CW_lt_start(self):
        """Test angleToSweep for a positive angle lt the startAngle of a CW arc."""
        angle = 0
        arc = Arc(startAngle=0.1, sweep=-1)

        result = arc.angleToSweep(angle)

        self.assertEqual(
            FloatAlmostEqual(-0.1, places=ROUND_PLACES),
            result,
            "It should equal -0.1"
        )

    def test_angleToSweep_positive_CW_gt_start(self):
        """Test angleToSweep for a positive angle gt the startAngle of a CW arc."""
        angle = 2 * math.pi + 1.1
        arc = Arc(startAngle=0.1, sweep=-1)

        result = arc.angleToSweep(angle)

        self.assertEqual(
            FloatAlmostEqual(-(2*math.pi - 1), places=ROUND_PLACES),
            result,
            "It should equal -(2PI-1)"
        )

    def test_angleToSweep_negative_CW_lt_start(self):
        """Test angleToSweep for a negative angle lt the startAngle of a CW arc."""
        angle = -(2 * math.pi - 0.1)
        arc = Arc(startAngle=0.2, sweep=-1)

        result = arc.angleToSweep(angle)

        self.assertEqual(
            FloatAlmostEqual(-0.1, places=ROUND_PLACES),
            result,
            "It should equal -0.1"
        )

    def test_angleToSweep_negative_CW_gt_start(self):
        """Test angleToSweep for a negative angle gt the startAngle of a CW arc."""
        angle = -(2 * math.pi + 0.1)
        arc = Arc(startAngle=0.1, sweep=-1)

        result = arc.angleToSweep(angle)

        self.assertEqual(
            FloatAlmostEqual(-0.2, places=ROUND_PLACES),
            result,
            "It should equal -0.2"
        )

    def test_normalize_radians_lt_zero(self):
        """Test normalize_radians for an angle less than zero."""
        self.assertEqual(normalize_radians(-(3 * math.pi + 1)), math.pi - 1)

    def test_normalize_radians_eq_zero(self):
        """Test normalize_radians for an angle equal to zero."""
        self.assertEqual(normalize_radians(0), 0)

    def test_normalize_radians_gt_zero(self):
        """Test normalize_radians for an angle greater than zero."""
        self.assertEqual(normalize_radians(3 * math.pi + 1), math.pi + 1)

    def test_arc_fromRadiusP1P2Clockwise_CW_positive_radius(self):
        """Test Arc.fromRadiusP1P2Clockwise with a CW minor arc."""
        unit = Arc.fromRadiusP1P2Clockwise(1, 0, 1, 1, 0, True)

        self.assertEqual(round(unit.cx, ROUND_PLACES), 0, "cx should be 0")
        self.assertEqual(round(unit.cy, ROUND_PLACES), 0, "cy should be 0")
        self.assertEqual(round(unit.radius, ROUND_PLACES), 1, "radius should be 1")
        self.assertEqual(unit.startAngle, FloatAlmostEqual(math.pi/2), "startAngle should be pi/2")
        self.assertEqual(unit.endAngle, FloatAlmostEqual(0), "endAngle should be 0")
        self.assertEqual(unit.sweep, -math.pi/2, "sweep should be -pi/2")
        self.assertTrue(unit.clockwise, "clockwise should be true")
        self.assertFalse(unit.major, "major should be false")
        self.assertEqual(0, unit.x1, "The start point x should be 0")
        self.assertEqual(1, unit.y1, "The start point y should be 1")
        self.assertEqual(1, unit.x2, "The end point x should be 1")
        self.assertEqual(0, unit.y2, "The end point y should be 0")

    def test_arc_fromRadiusP1P2Clockwise_CW_negative_radius(self):
        """Test Arc.fromRadiusP1P2Clockwise with a CW major arc."""
        unit = Arc.fromRadiusP1P2Clockwise(-1, 0, 1, 1, 0, True)

        self.assertEqual(round(unit.cx, ROUND_PLACES), 1, "cx should be 1")
        self.assertEqual(round(unit.cy, ROUND_PLACES), 1, "cy should be 1")
        self.assertEqual(round(unit.radius, ROUND_PLACES), 1, "radius should be 1")
        self.assertEqual(unit.startAngle, math.pi, "startAngle should be pi")
        self.assertEqual(unit.endAngle, -math.pi / 2, "endAngle should be -pi/2")
        self.assertEqual(unit.sweep, -1.5*math.pi, "sweep should be -1.5pi")
        self.assertTrue(unit.clockwise, "clockwise should be true")
        self.assertTrue(unit.major, "major should be true")
        self.assertEqual(0, unit.x1, "The start point x should be 0")
        self.assertEqual(1, unit.y1, "The start point y should be 1")
        self.assertEqual(1, unit.x2, "The end point x should be 1")
        self.assertEqual(0, unit.y2, "The end point y should be 0")

    def test_arc_fromRadiusP1P2Clockwise_CCW_positive_radius(self):
        """Test Arc.fromRadiusP1P2Clockwise with a CCW minor arc."""
        unit = Arc.fromRadiusP1P2Clockwise(1, 0, 1, 1, 0, False)

        self.assertEqual(round(unit.cx, ROUND_PLACES), 1, "cx should be 1")
        self.assertEqual(round(unit.cy, ROUND_PLACES), 1, "cy should be 1")
        self.assertEqual(round(unit.radius, ROUND_PLACES), 1, "radius should be 1")
        self.assertEqual(unit.startAngle, FloatAlmostEqual(math.pi), "startAngle should be pi")
        self.assertEqual(unit.endAngle, FloatAlmostEqual(math.pi*1.5), "endAngle should be 1.5pi")
        self.assertEqual(unit.sweep, math.pi/2, "sweep should be pi/2")
        self.assertFalse(unit.clockwise, "clockwise should be false")
        self.assertFalse(unit.major, "major should be false")
        self.assertEqual(0, unit.x1, "The start point x should be 0")
        self.assertEqual(1, unit.y1, "The start point y should be 1")
        self.assertEqual(1, unit.x2, "The end point x should be 1")
        self.assertEqual(0, unit.y2, "The end point y should be 0")

    def test_arc_fromRadiusP1P2Clockwise_CCW_negative_radius(self):
        """Test Arc.fromRadiusP1P2Clockwise with a CCW major arc."""
        unit = Arc.fromRadiusP1P2Clockwise(-1, 0, 1, 1, 0, False)

        self.assertEqual(round(unit.cx, ROUND_PLACES), 0, "cx should be 0")
        self.assertEqual(round(unit.cy, ROUND_PLACES), 0, "cy should be 0")
        self.assertEqual(round(unit.radius, ROUND_PLACES), 1, "radius should be 1")
        self.assertEqual(
            unit.startAngle, FloatAlmostEqual(math.pi / 2),
            "startAngle should be pi/2"
        )
        self.assertEqual(unit.endAngle, math.pi*2, "endAngle should be 2pi")
        self.assertEqual(unit.sweep, 1.5*math.pi, "sweep should be 1.5pi")
        self.assertFalse(unit.clockwise, "clockwise should be false")
        self.assertTrue(unit.major, "major should be true")
        self.assertEqual(0, unit.x1, "The start point x should be 0")
        self.assertEqual(1, unit.y1, "The start point y should be 1")
        self.assertEqual(1, unit.x2, "The end point x should be 1")
        self.assertEqual(0, unit.y2, "The end point y should be 0")

    def test_arc_fromRadiusP1P2Clockwise_zeroRadius(self):
        """Test Arc.fromRadiusP1P2Clockwise with a radius of 0."""
        with self.assertRaises(ValueError):
            Arc.fromRadiusP1P2Clockwise(0, 0, 1, 1, 0, False)

    def test_arc_fromRadiusP1P2Clockwise_endpoints_same(self):
        """Test Arc.fromRadiusP1P2Clockwise with the same endpoints."""
        with self.assertRaises(ValueError):
            Arc.fromRadiusP1P2Clockwise(1, 0, 1, 0, 1, False)

    def test_arc_fromRadiusP1P2Clockwise_halfDist_gt_radius(self):
        """Test Arc.fromRadiusP1P2Clockwise with the endpoints more than twice radius apart."""
        with self.assertRaises(ValueError):
            Arc.fromRadiusP1P2Clockwise(1, 0, 0, 3, 0, False)

    def test_arc_fromCenterP1P2Clockwise_CW_lenient(self):
        """Test Arc.fromCenterP1P2Clockwise with an invalid CW arc in lenient mode."""
        unit = Arc.fromCenterP1P2Clockwise(0, 0, 1, 0, 0, 2, True)

        self.assertEqual(unit.cx, 0, "cx should be 0")
        self.assertEqual(unit.cy, 0, "cy should be 0")
        self.assertEqual(round(unit.radius, ROUND_PLACES), 1, "radius should be 1")
        self.assertEqual(unit.startAngle, 0, "startAngle should be 0")
        self.assertEqual(unit.endAngle, math.pi * -1.5, "endAngle should be -1.5pi")
        self.assertEqual(unit.sweep, math.pi * -1.5, "sweep should be -1.5pi")
        self.assertTrue(unit.clockwise, "clockwise should be true")
        self.assertTrue(unit.major, "major should be true")
        self.assertEqual(1, unit.x1, "The start point x should be 1")
        self.assertEqual(0, unit.y1, "The start point y should be 0")
        self.assertEqual(0, unit.x2, "The end point x should be 0")
        self.assertEqual(1, unit.y2, "The end point y should be 1")

    def test_arc_fromCenterP1P2Clockwise_CCW_lenient(self):
        """Test Arc.fromCenterP1P2Clockwise with an invalid CCW arc in lenient mode."""
        unit = Arc.fromCenterP1P2Clockwise(0, 0, 1, 0, 0, 2, False)

        self.assertEqual(unit.cx, 0, "cx should be 0")
        self.assertEqual(unit.cy, 0, "cy should be 0")
        self.assertEqual(round(unit.radius, ROUND_PLACES), 1, "radius should be 1")
        self.assertEqual(unit.startAngle, 0, "startAngle should be 0")
        self.assertEqual(unit.endAngle, math.pi / 2, "endAngle should be pi/2")
        self.assertEqual(unit.sweep, math.pi / 2, "sweep should be pi/2")
        self.assertFalse(unit.clockwise, "clockwise should be false")
        self.assertFalse(unit.major, "major should be false")
        self.assertEqual(1, unit.x1, "The start point x should be 1")
        self.assertEqual(0, unit.y1, "The start point y should be 0")
        self.assertEqual(0, unit.x2, "The end point x should be 0")
        self.assertEqual(1, unit.y2, "The end point y should be 1")

    def test_arc_fromCenterP1P2Clockwise_CW_strict(self):
        """Test Arc.fromCenterP1P2Clockwise with a valid CW arc in strict mode."""
        unit = Arc.fromCenterP1P2Clockwise(0, 0, 1, 0, 0, 1, True, False)

        self.assertEqual(unit.cx, 0, "cx should be 0")
        self.assertEqual(unit.cy, 0, "cy should be 0")
        self.assertEqual(round(unit.radius, ROUND_PLACES), 1, "radius should be 1")
        self.assertEqual(unit.startAngle, 0, "startAngle should be 0")
        self.assertEqual(unit.endAngle, math.pi * -1.5, "endAngle should be -1.5pi")
        self.assertEqual(unit.sweep, math.pi * -1.5, "sweep should be -1.5pi")
        self.assertTrue(unit.clockwise, "clockwise should be true")
        self.assertTrue(unit.major, "major should be true")
        self.assertEqual(1, unit.x1, "The start point x should be 1")
        self.assertEqual(0, unit.y1, "The start point y should be 0")
        self.assertEqual(0, unit.x2, "The end point x should be 0")
        self.assertEqual(1, unit.y2, "The end point y should be 1")

    def test_arc_fromCenterP1P2Clockwise_CCW_strict(self):
        """Test Arc.fromCenterP1P2Clockwise with a valid CCW arc in strict mode."""
        unit = Arc.fromCenterP1P2Clockwise(0, 0, 1, 0, 0, 1, False, False)

        self.assertEqual(unit.cx, 0, "cx should be 0")
        self.assertEqual(unit.cy, 0, "cy should be 0")
        self.assertEqual(round(unit.radius, ROUND_PLACES), 1, "radius should be 1")
        self.assertEqual(unit.startAngle, 0, "startAngle should be 0")
        self.assertEqual(unit.endAngle, math.pi / 2, "endAngle should be pi/2")
        self.assertEqual(unit.sweep, math.pi / 2, "sweep should be pi/2")
        self.assertFalse(unit.clockwise, "clockwise should be false")
        self.assertFalse(unit.major, "major should be false")
        self.assertEqual(1, unit.x1, "The start point x should be 1")
        self.assertEqual(0, unit.y1, "The start point y should be 0")
        self.assertEqual(0, unit.x2, "The end point x should be 0")
        self.assertEqual(1, unit.y2, "The end point y should be 1")

    def test_arc_fromCenterP1P2Clockwise_CW_strict_fail(self):
        """Test Arc.fromCenterP1P2Clockwise with an invalid CW arc in strict mode."""
        with self.assertRaises(ValueError):
            Arc.fromCenterP1P2Clockwise(
                0, 0, 1, 0, 0, 2, True, False
            )  # pylint: disable=too-many-function-args

    def test_fromCenterRadiusStartEndClockwise_CW(self):
        """Test Arc.fromCenterRadiusStartEndClockwise with a CW arc."""
        endAngle = -math.pi * 2 + 1
        unit = Arc.fromCenterRadiusStartEndClockwise(0, 0, 1, 0, 1, True)

        self.assertEqual(unit.cx, 0, "cx should be 0")
        self.assertEqual(unit.cy, 0, "cy should be 0")
        self.assertEqual(unit.radius, 1, "radius should be 1")
        self.assertEqual(unit.startAngle, 0, "startAngle should be 0")
        self.assertEqual(unit.endAngle, endAngle, "endAngle should be -2pi+1")
        self.assertEqual(unit.sweep, endAngle, "sweep should be -2pi+1")
        self.assertTrue(unit.clockwise, "clockwise should be true")
        self.assertTrue(unit.major, "major should be true")
        self.assertEqual(1, unit.x1, "The start point x should be 1")
        self.assertEqual(0, unit.y1, "The start point y should be 0")

        x2 = math.cos(endAngle)
        y2 = math.sin(endAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

    def test_fromCenterRadiusStartEndClockwise_CCW(self):
        """Test Arc.fromCenterRadiusStartEndClockwise with a CCW arc."""
        endAngle = 1
        unit = Arc.fromCenterRadiusStartEndClockwise(0, 0, 1, 0, 1, False)

        self.assertEqual(unit.cx, 0, "cx should be 0")
        self.assertEqual(unit.cy, 0, "cy should be 0")
        self.assertEqual(unit.radius, 1, "radius should be 1")
        self.assertEqual(unit.startAngle, 0, "startAngle should be 0")
        self.assertEqual(unit.endAngle, endAngle, "endAngle should be 1")
        self.assertEqual(unit.sweep, endAngle, "sweep should be 1")
        self.assertFalse(unit.clockwise, "clockwise should be false")
        self.assertFalse(unit.major, "major should be false")
        self.assertEqual(1, unit.x1, "The start point x should be 1")
        self.assertEqual(0, unit.y1, "The start point y should be 0")

        x2 = math.cos(endAngle)
        y2 = math.sin(endAngle)
        self.assertEqual(FloatAlmostEqual(x2), unit.x2, "The end point x should be " + repr(x2))
        self.assertEqual(FloatAlmostEqual(y2), unit.y2, "The end point y should be " + repr(y2))

    def test_equal(self):
        """Test the __eq__ method."""
        # pylint: disable=invalid-name
        a = Arc(cx=0, cy=1, radius=2, startAngle=3, sweep=4)
        b = Arc(cx=0, cy=1, radius=2, startAngle=3, sweep=4)

        c = Arc(cx=99, cy=1, radius=2, startAngle=3, sweep=4)
        d = Arc(cx=0, cy=99, radius=2, startAngle=3, sweep=4)
        e = Arc(cx=0, cy=1, radius=99, startAngle=3, sweep=4)
        f = Arc(cx=0, cy=1, radius=2, startAngle=99, sweep=4)
        g = Arc(cx=0, cy=1, radius=2, startAngle=3, sweep=99)

        self.assertTrue(a == b)
        self.assertTrue(b == a)
        self.assertFalse(a == c)
        self.assertFalse(a == d)
        self.assertFalse(a == e)
        self.assertFalse(a == f)
        self.assertFalse(a == g)

    def test_roundValues(self):
        """Test the roundValues method."""
        unit = Arc(
            cx=4.123456789, cy=3.123456789, radius=2.123456789,
            startAngle=1.123456789, sweep=0.123456789
        )

        unit.roundValues(6)

        self.assertEqual(
            Arc(
                cx=4.123457, cy=3.123457, radius=2.123457,
                startAngle=1.123457, sweep=0.123457
            ),
            unit,
            "It should round the values"
        )

    def test_containsAngle_CW(self):
        """Test containsAngle for a CW arc."""
        unit = Arc(cx=0, cy=0, radius=1, startAngle=0, sweep=math.pi)

        self.assertTrue(unit.containsAngle(0))
        self.assertTrue(unit.containsAngle(-math.pi))
        self.assertTrue(unit.containsAngle(math.pi))
        self.assertFalse(unit.containsAngle(-math.pi / 2))
        self.assertTrue(unit.containsAngle(math.pi / 2))

    def test_containsAngle_CCW(self):
        """Test containsAngle for a CCW arc."""
        unit = Arc(cx=0, cy=0, radius=1, startAngle=0, sweep=-math.pi)

        self.assertTrue(unit.containsAngle(0))
        self.assertTrue(unit.containsAngle(-math.pi))
        self.assertTrue(unit.containsAngle(math.pi))
        self.assertTrue(unit.containsAngle(-math.pi / 2))
        self.assertFalse(unit.containsAngle(math.pi / 2))
