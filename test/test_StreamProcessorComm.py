# coding=utf-8
"""Unit tests for the StreamProcessorComm class."""

from __future__ import absolute_import

from octoprint_excluderegion.StreamProcessor import StreamProcessorComm

from .utils import TestCase


class StreamProcessorCommTests(TestCase):
    """Unit tests for the StreamProcessorComm class."""

    def test_initializer(self):
        """Test the class __init__ method."""
        unit = StreamProcessorComm()
        self.assertEqual(unit.bufferedCommands, [], "bufferedCommands should be an empty list.")

    def test_reset(self):
        """Test the reset method."""
        unit = StreamProcessorComm()
        unit.bufferedCommands = ["command"]

        unit.reset()

        self.assertEqual(unit.bufferedCommands, [], "bufferedCommands should be an empty list.")

    def test_isStreaming(self):
        """Test the isStreaming method."""
        unit = StreamProcessorComm()
        self.assertFalse(unit.isStreaming(), "isStreaming() should return False.")

    def test_sendCommand_none(self):
        """Test sendCommand when passed None."""
        unit = StreamProcessorComm()

        unit.sendCommand(None)

        self.assertEqual(unit.bufferedCommands, [], "bufferedCommands should be an empty list.")

    def test_sendCommand_notNone_emptyBuffer(self):
        """Test sendCommand when passed a non-None value when the buffer is empty."""
        unit = StreamProcessorComm()

        unit.sendCommand("newCommand")

        self.assertEqual(
            unit.bufferedCommands, ["newCommand"],
            "bufferedCommands should have the new command appended."
        )

    def test_sendCommand_notNone_nonEmptyBuffer(self):
        """Test sendCommand when passed a non-None value when the buffer is not empty."""
        unit = StreamProcessorComm()
        unit.bufferedCommands = ["originalCommand"]

        unit.sendCommand("newCommand")

        self.assertEqual(
            unit.bufferedCommands, ["originalCommand", "newCommand"],
            "bufferedCommands should have the new command appended."
        )
