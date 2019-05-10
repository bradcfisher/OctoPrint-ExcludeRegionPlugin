# coding=utf-8
"""Unit tests for the octoprint_excluderegion module __init__ code."""

from __future__ import absolute_import

import mock

from octoprint_excluderegion import ExcludeRegionPlugin

from .utils import TestCase


class InitTests(TestCase):
    """Unit tests for the octoprint_excluderegion module __init__ code."""

    def test_global_property_defaults(self):
        """Tests that the expected global properties are defined by default."""
        import octoprint_excluderegion

        expectedGlobalProperties = [
            "__plugin_name__",
            "__plugin_implementation__",
            "__plugin_hooks__",
            "__plugin_load__",
            "ExcludeRegionPlugin"
        ]

        moduleProperties = dir(octoprint_excluderegion)

        for globalProperty in expectedGlobalProperties:
            self.assertIn(
                globalProperty, moduleProperties,
                "The '%s' global property should be defined by the module" % globalProperty
            )

        self.assertIsNone(
            octoprint_excluderegion.__plugin_implementation__,
            "__plugin_implementation__ should default to None"
        )
        self.assertIsNone(
            octoprint_excluderegion.__plugin_hooks__,
            "__plugin_hooks__ should default to None"
        )

    def test_plugin_load(self):
        """Tests that the expected global property values are set when __init__ is called."""
        import octoprint_excluderegion

        octoprint_excluderegion.__plugin_load__()

        checkConfigHookName = "octoprint.plugin.softwareupdate.check_config"
        atCommandQueuingHookName = "octoprint.comm.protocol.atcommand.queuing"
        gcodeQueuingHookName = "octoprint.comm.protocol.gcode.queuing"

        self.assertIsInstance(
            octoprint_excluderegion.__plugin_implementation__,
            ExcludeRegionPlugin,
            "__plugin_implementation__ should be set to an ExcludeRegionPlugin instance"
        )
        self.assertIsDictionary(
            octoprint_excluderegion.__plugin_hooks__,
            "__plugin_hooks__ should be a dict instance"
        )

        pluginObject = octoprint_excluderegion.__plugin_implementation__

        self._assertHook(
            octoprint_excluderegion.__plugin_hooks__,
            checkConfigHookName,
            [],
            pluginObject,
            "getUpdateInformation",
            []
        )

        commInstance = mock.Mock()
        phase = mock.Mock()
        command = mock.Mock()
        parameters = mock.Mock()
        tags = mock.Mock()
        self._assertHook(
            octoprint_excluderegion.__plugin_hooks__,
            atCommandQueuingHookName,
            [commInstance, phase, command, parameters, tags],
            pluginObject,
            "handleAtCommandQueuing",
            [commInstance, phase, command, parameters, tags]
        )

        commInstance = mock.Mock()
        phase = mock.Mock()
        command = mock.Mock()
        commandType = mock.Mock()
        gcode = mock.Mock()
        subcode = mock.Mock()
        tags = mock.Mock()
        self._assertHook(
            octoprint_excluderegion.__plugin_hooks__,
            gcodeQueuingHookName,
            [commInstance, phase, command, commandType, gcode, subcode, tags],
            pluginObject,
            "handleGcodeQueuing",
            [commInstance, phase, command, commandType, gcode, subcode, tags]
        )

    def _assertHook(  # pylint: disable=too-many-arguments
            self, hooks, hookName, hookArgs, impl, implMethodName, methodArgs
    ):
        """
        Ensure that a hook is defined and a named method is called when the hook is invoked.

        Parameters
        ----------
        hooks : dict of hook values
            The defined hooks.
        hookName : string
            The name of the hook to validate.
        hookArgs : list
            List of arguments to pass to the hook function.
        impl : ExcludeRegionPlugin
            The plugin implementation instance.
        implMethodName : string
            The name of the plugin implementation method that should be invoked by the hook.
        methodArgs : list
            List of arguments expected to be passed to the module instance method.
        """
        self.assertIn(
            hookName, hooks,
            "A '%s' hook should be defined" % hookName
        )

        originalImplMethod = getattr(impl, implMethodName)

        with mock.patch.object(impl, implMethodName) as mockImplMethod:
            hookFunction = hooks[hookName]

            if (not callable(hookFunction)):
                self.assertEqual(
                    len(hookFunction), 2,
                    "The hook tuple must contain 2 values"
                )

                hookFunction = hookFunction[0]
                self.assertTrue(callable(hookFunction), "The hook function must be callable")

            if (hookFunction != originalImplMethod):
                hookFunction(*hookArgs)
                mockImplMethod.assert_called_with(*methodArgs)
