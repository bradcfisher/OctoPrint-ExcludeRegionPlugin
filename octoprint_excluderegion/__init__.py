# coding=utf-8
"""OctoPrint plugin adding the ability to prevent printing in rectangular or circular regions."""

# Thoughts on improvements:
# - Persist the defined regions for the selected file and restore them if the file
#   is selected again later?
#   - Add @-commands into the gcode file itself to define the regions? (assuming the regions should be modifiable)
#   - Store the regions as metadata?  May want to compare file hash to make sure the file hasn't been updated since the regions were defined.
#   - Simply create a copy of the file with the excluded Gcode removed?  This would probably print the cleanest,
#     but would not allow restoring previously excluded regions without going back to the original file.
#
# - Preprocess the file to add @-commands to mark the begin/end Gcode scripts based on comments,
#   similar to the Cancel Object plugin?
#
# - Is a setting needed for controlling how big a retraction is recorded as one that needs to be
#   recovered after exiting an excluded region (e.g. ignore small retractions like E-0.03)?
#   What could a reasonable limit be for the default?
#
# - Interpret M207 / M208 - Firmware retraction settings?
#
# - Add support for multiple extruders? (gcode cmd: "T#" - selects tool #)  Each tool should
#   have its own extruder position/axis.  What about the other axes?
# Each tool has its own offsets and x axis position
# From Marlin source (Marlin_main.cpp:11201):
#   current_position[Y_AXIS] -=
#       hotend_offset[Y_AXIS][active_extruder] - hotend_offset[Y_AXIS][tmp_extruder];
#   current_position[Z_AXIS] -=
#       hotend_offset[Z_AXIS][active_extruder] - hotend_offset[Z_AXIS][tmp_extruder];

from __future__ import absolute_import

import logging
import re

import flask
from flask_login import current_user

import pkg_resources

import octoprint.plugin
from octoprint.events import Events
from octoprint.settings import settings

from .GcodeHandlers import GcodeHandlers
from .ExcludeRegionState import ExcludeRegionState
from .RectangularRegion import RectangularRegion
from .CircularRegion import CircularRegion
from .ExcludedGcode import ExcludedGcode, EXCLUDE_ALL, EXCLUDE_MERGE
from .AtCommandAction import AtCommandAction, ENABLE_EXCLUSION, DISABLE_EXCLUSION


__plugin_name__ = "Exclude Region"
__plugin_implementation__ = None
__plugin_hooks__ = None

EXCLUDED_REGIONS_CHANGED = "ExcludedRegionsChanged"

LOG_MODE_OCTOPRINT = "octoprint"
LOG_MODE_DEDICATED = "dedicated"
LOG_MODE_BOTH = "both"


# pylint: disable=global-statement
def __plugin_load__():
    """Initialize OctoPrint plugin meta properties."""
    global __plugin_implementation__
    __plugin_implementation__ = ExcludeRegionPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config":
            __plugin_implementation__.getUpdateInformation,
        "octoprint.comm.protocol.scripts":
            (__plugin_implementation__.handleScriptHook, 0),
        "octoprint.comm.protocol.atcommand.queuing":
            __plugin_implementation__.handleAtCommandQueuing,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.handleGcodeQueuing
    }


class ExcludeRegionPlugin(  # pylint: disable=too-many-instance-attributes
        octoprint.plugin.AssetPlugin,
        octoprint.plugin.TemplatePlugin,
        octoprint.plugin.SettingsPlugin,
        octoprint.plugin.SimpleApiPlugin,
        octoprint.plugin.EventHandlerPlugin
):  # pylint: disable=too-many-ancestors
    """
    OctoPrint plugin adding the ability to prevent printing in rectangular or circular regions.

    Attributes
    ----------
    clearRegionsAfterPrintFinishes : boolean
        Whether to clear the exclusion regions after the next print completes or not.  Populated
        from the setting of the same name.
    mayShrinkRegionsWhilePrinting : boolean
        Whether exclude regions may be deleted or reduced in size when actively printing. Populated
        from the setting of the same name.
    _activePrintJob : boolean
        Whether a print is currently in progress or not.
    state : ExcludeRegionState
        ExcludeRegionState instance for managing the current plugin state
    gcodeHandlers : GcodeHandlers
        GcodeHandlers instance providing the actual Gcode processing
    """

    def __init__(self):
        """
        Declare plugin-specific properties to satisfy pylint.

        The actual initialization is performed by the initialize method.
        """
        super(ExcludeRegionPlugin, self).__init__()

        self._activePrintJob = None
        self._loggingMode = None
        self._pluginLoggingHandler = None
        self.clearRegionsAfterPrintFinishes = None
        self.mayShrinkRegionsWhilePrinting = None
        self.state = None
        self.gcodeHandlers = None

    def initialize(self):
        """
        Perform plugin initialization.

        This method is automatically invoked by OctoPrint when the plugin is loaded, and is called
        after all injected properties are populated.
        """
        self._activePrintJob = False
        self.state = ExcludeRegionState(self._logger)
        self.gcodeHandlers = GcodeHandlers(self.state, self._logger)
        self._handleSettingsUpdated()
        self._notifyExcludedRegionsChanged()

        self._logger.debug(
            "Initialization complete: Installed plugin version=%s",
            self._plugin_version
        )

    def getUpdateInformation(self):
        """Return the information necessary for OctoPrint to check for new plugin versions."""
        return dict(
            excluderegion=dict(
                displayName=__plugin_name__,
                displayVersion=self._plugin_version,

                type="github_release",
                user="bradcfisher",
                repo="OctoPrint-ExcludeRegionPlugin",
                current=self._plugin_version,

                pip="https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/archive/{target_version}.zip"  # nopep8
            )
        )

    # ~~ AssetPlugin

    def get_assets(self):
        """Define the static assets the plugin offers."""
        octoprintVersion = pkg_resources.parse_version(octoprint.__version__)

        jsFiles = ["js/excluderegion.js"]

        # The modified gcode renderer is not needed for 1.3.10rc1 and above
        if (octoprintVersion < pkg_resources.parse_version("1.3.10rc1")):
            self._logger.info(
                "Octoprint {} is pre 1.3.10rc1, including renderer.js to override gcode viewer",
                octoprint.__display_version__
            )
            jsFiles.insert(0, "js/renderer.js")

        return dict(
            js=jsFiles,
            css=["css/excluderegion.css"]
        )

    # ~~ TemplatePlugin

    def get_template_configs(self):
        """Register the custom settings interface with OctoPrint."""
        return [
            dict(type="settings", custom_bindings=True)
        ]

    # ~~ SettingsPlugin

    def get_settings_defaults(self):
        """Return a dictionary of the default plugin settings."""
        return dict(
            clearRegionsAfterPrintFinishes=False,
            mayShrinkRegionsWhilePrinting=False,
            loggingMode=LOG_MODE_OCTOPRINT,
            enteringExcludedRegionGcode=None,
            exitingExcludedRegionGcode=None,
            extendedExcludeGcodes=[
                {
                    "gcode": "G4",
                    "mode": EXCLUDE_ALL,
                    "description": "Ignore all dwell commands in an excluded area to reduce " +
                                   "delays while excluding"
                },
                {
                    "gcode": "M204",
                    "mode": EXCLUDE_MERGE,
                    "description": "Record default acceleration changes while excluding and " +
                                   "apply the most recent values in a single command after " +
                                   "exiting the excluded area"
                },
                {
                    "gcode": "M205",
                    "mode": EXCLUDE_MERGE,
                    "description": "Record advanced setting changes while excluding and apply " +
                                   "the most recent values in a single command after exiting the " +
                                   "excluded area"
                }
            ],
            atCommandActions=[
                {
                    "command": "ExcludeRegion",
                    "parameterPattern": "^\\s*(enable|on)(\\s|$)",
                    "action": ENABLE_EXCLUSION,
                    "description": "Default action to enable exclusion"
                },
                {
                    "command": "ExcludeRegion",
                    "parameterPattern": "^\\s*(disable|off)(\\s|$)",
                    "action": DISABLE_EXCLUSION,
                    "description": "Default action to disable exclusion"
                }
            ]
        )

    def get_settings_version(self):
        """Return the plugin settings version supported by this version of the plugin."""
        return 1

    def get_settings_preprocessors(self):
        """
        Return setting preprocessors to invoke when setting/getting setting values.

        This method defines preprocessors for setting the 'extendedExcludeGcodes' and
        'atCommandActions' settings to ensure the lists are stored in sorted order.
        """
        return (
            # preprocessors for setters
            {
                "extendedExcludeGcodes":
                    lambda value: sorted(value, key=lambda item: item["gcode"].upper()),
                "atCommandActions":
                    lambda value: sorted(value, key=lambda item: item["command"].upper())
            },
            # preprocessors for getters
            {}
        )

    # ~~ SimpleApiPlugin

    def get_api_commands(self):
        """
        Define the POST command API endpoints for the plugin.

        The following endpoints are defined:

        /api/plugin/excluderegion/addExcludeRegion
        ------------------------------------------

        Defines a new excluded region.

        Example POST data to add a rectangular region:

        .. code-block:: javascript
           {
             "type" : "RectangularRegion",
             "x1" : 1,
             "y1" : 1,
             "x2" : 2,
             "y2" : 2
           }

        Example POST data to add a circular region:

        .. code-block:: javascript
           {
             "type" : "CircularRegion",
             "cx" : 1,
             "cy" : 1,
             "r" : 1
           }

        /api/plugin/excluderegion/updateExcludeRegion
        ---------------------------------------------

        Replaces an existing exclusion region with a new region.  An error will be returned if
        the specified id doesn't match an existing region.

        Example POST data to update a region:

        .. code-block:: javascript
           {
             "id" : "...uuid...",
             "type" : "CircularRegion",
             "cx" : 2,
             "cy" : 2,
             "r" : 1
           }

        /api/plugin/excluderegion/deleteExcludeRegion
        ---------------------------------------------

        Delete the region with the specified id.

        Example POST data to delete a region:

        .. code-block:: javascript
           {
             "id" : "...uuid..."
           }
        """
        return dict(
            addExcludeRegion=["type"],
            updateExcludeRegion=["type", "id"],
            deleteExcludeRegion=["id"],
        )

    def on_api_command(self, command, data):
        """Route API requests to their implementations."""
        if current_user.is_anonymous():
            return "Insufficient rights", 403

        self._logger.debug("API command received: %s", data)

        if (command == "deleteExcludeRegion"):
            return self._handleDeleteExcludeRegion(data.get("id"))
        else:
            regionType = data.get("type")

            if (regionType == "RectangularRegion"):
                region = RectangularRegion(**data)
            elif (regionType == "CircularRegion"):
                region = CircularRegion(**data)
            else:
                return "Invalid type", 400

            if (command == "addExcludeRegion"):
                return self._handleAddExcludeRegion(region)
            elif (command == "updateExcludeRegion"):
                return self._handleUpdateExcludeRegion(region)

            return "Invalid command", 400

    def on_api_get(self, request):
        """
        Generate response to GET request '/api/plugin/excluderegion'.

        The response is encoded in JSON and has the following structure:

        .. code-block:: javascript
           {
             "excluded_regions": [
               {
                 "type": "RectangularRegion",
                 "id": "...uuid...",
                 "x1": 1, "y1": 1, "x2": 2, "y2": 2
               },
               {
                 "type": "CircularRegion",
                 "id": "...uuid...",
                 "cx": 1, "cy": 1, "r": 2
               }
               // etc ...
             ]
           }
        """
        return flask.jsonify(
            excluded_regions=[region.toDict() for region in self.state.excludedRegions]
        )

    # ~~ EventHandlerPlugin

    def on_event(self, event, payload):
        """
        Intercept server events and perform any processing necessary.

        Actions taken include:
          - Remove all excluded regions when a new Gcode file is selected
          - Reset the internal state when a new print is started
          - Respond to setting updates
          - Remove all excluded regions when printing completes (if configured to do so)

        Parameters
        ----------
        event : string
            The event that occurred

        payload : dict
            Additional event data
        """
        self._logger.debug("Event received: event=%s payload=%s", event, payload)

        if (event == Events.FILE_SELECTED):
            self._logger.info("File selected, resetting internal state")
            self.state.resetState(True)
            self._notifyExcludedRegionsChanged()
        elif (event == Events.SETTINGS_UPDATED):
            self._handleSettingsUpdated()
        elif (event == Events.PRINT_STARTED):
            self._logger.info("Printing started")
            self.state.resetState()
            self._activePrintJob = True
        elif (event in (
                Events.PRINT_DONE,
                Events.PRINT_FAILED,
                Events.PRINT_CANCELLING,
                Events.PRINT_CANCELLED,
                Events.ERROR
        )):
            self._logger.info("Printing stopped: event=%s", event)
            self._activePrintJob = False
            if (self.clearRegionsAfterPrintFinishes):
                self.state.resetState(True)
                self._notifyExcludedRegionsChanged()

    # ~~ ExcludeRegionPlugin

    @property
    def isActivePrintJob(self):
        """Whether a print is currently in progress or not."""
        return self._activePrintJob

    @property
    def loggingMode(self):
        """Return the current logging mode."""
        return self._loggingMode

    @loggingMode.setter
    def loggingMode(self, loggingMode):
        """
        Set a new logging mode for the plugin.

        Parameters
        ----------
        loggingMode : String
            The new logging mode to apply.  May be one of LOG_MODE_OCTOPRINT, LOG_MODE_DEDICATED,
            or LOG_MODE_BOTH.
        """
        if (self._loggingMode == loggingMode):
            return

        if (loggingMode not in (LOG_MODE_DEDICATED, LOG_MODE_OCTOPRINT, LOG_MODE_BOTH)):
            raise AttributeError("Invalid mode value")

        if (self._loggingMode is not None):
            # Write a message to the previous log if a mode has been previously set
            self._logger.info(
                "Changing logging mode from '%s' to '%s'",
                self._loggingMode, loggingMode
            )

        if (loggingMode in (LOG_MODE_DEDICATED, LOG_MODE_BOTH)):
            if (self._pluginLoggingHandler is None):
                self._pluginLoggingHandler = logging.handlers.RotatingFileHandler(
                    self._settings.get_plugin_logfile_path(),
                    maxBytes=2*1024*1024,
                    backupCount=3
                )
                self._pluginLoggingHandler.setFormatter(
                    logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
                )
                self._pluginLoggingHandler.setLevel(logging.DEBUG)

            if (self._loggingMode == LOG_MODE_OCTOPRINT):
                # Any other mode means the handler is already added
                self._logger.addHandler(self._pluginLoggingHandler)

            self._logger.propagate = (loggingMode == LOG_MODE_BOTH)
        elif (self._pluginLoggingHandler is not None):  # LOG_MODE_OCTOPRINT
            self._logger.removeHandler(self._pluginLoggingHandler)
            self._logger.propagate = True

        self._loggingMode = loggingMode

        # Write a message to the new log
        self._logger.info("Logging mode set to '%s'", self._loggingMode)

    def _handleAddExcludeRegion(self, region):
        """
        Add a new exclusion region.

        Parameters
        ----------
        region : Region
            The new region to add

        Returns
        -------
        None | Tuple(string, status_code)
            Returns None if the operation was successful, and an error status tuple if the specified
            region has the same id as an existing region.
        """
        try:
            self.state.addRegion(region)
            self._notifyExcludedRegionsChanged()
            return None
        except ValueError as err:
            return err.args[0], 409

    def _handleDeleteExcludeRegion(self, idToDelete):
        """
        Remove the region with the specified id.

        Parameters
        ----------
        idToDelete : string
            The id of the region to remove.

        Returns
        -------
        None | Tuple(string, status_code)
            Returns None if the operation was successful, and an error status tuple if the region
            cannot be deleted.
        """
        if (not self.mayShrinkRegionsWhilePrinting and self.isActivePrintJob):
            return "Cannot delete region while printing", 409

        if (self.state.deleteRegion(idToDelete)):
            self._notifyExcludedRegionsChanged()

        return None

    def _handleUpdateExcludeRegion(self, newRegion):
        """
        Replace an existing region with a new one.

        Parameters
        ----------
        region : Region
            The new region to use as a replacement for an existing one with a matching id.

        Returns
        -------
        None | Tuple(string, status_code)
            Returns None if the operation was successful, and an error status tuple if the new
            region does not have an id or the modified region is required to fully contain the
            original area.
        """
        try:
            self.state.replaceRegion(
                newRegion,
                not self.mayShrinkRegionsWhilePrinting and self.isActivePrintJob
            )
            self._notifyExcludedRegionsChanged()
            return None
        except ValueError as err:
            return err.args[0], 409

    def _notifyExcludedRegionsChanged(self):
        """
        Send an 'excludedRegionsChanged' event to any interested listeners.

        The event sent has the following structure:

        .. code-block:: javascript
           {
             "event": "excludedRegionsChanged",
             "excluded_regions": [
               {
                 "type": "RectangularRegion",
                 "id": "...uuid...",
                 "x1": 1, "y1": 1, "x2": 2, "y2": 2
               },
               {
                 "type": "CircularRegion",
                 "id": "...uuid...",
                 "cx": 1, "cy": 1, "r": 2
               }
               // etc ...
             ]
           }
        """
        self._plugin_manager.send_plugin_message(
            self._identifier,
            dict(
                event=EXCLUDED_REGIONS_CHANGED,
                excluded_regions=[region.toDict() for region in self.state.excludedRegions]
            )
        )

    def _splitGcodeScript(self, gcodeString):
        """
        Split multiple lines of Gcode at line breaks and remove comments and blank lines.

        Parameters
        ----------
        gcodeString : string
            The Gcode string to split and sanitize

        Returns
        -------
        List of string
            The sanitized list of Gcode commands
        """
        if (gcodeString is None):
            return None

        gcodeCommands = []

        for gcode in self.gcodeHandlers.gcodeParser.parseLines(gcodeString):
            line = gcode.stringify(
                includeLeadingWhitespace=False,
                includeLineNumber=False,
                includeComment=False,
                includeEol=False
            )
            # "0" is falsy, but should be added as a line below, hence the pylint exception
            if (line is not None) and len(line):  # pylint: disable=len-as-condition
                gcodeCommands.append(line)

        if (not gcodeCommands):
            gcodeCommands = None

        return gcodeCommands

    def _handleSettingsUpdated(self):
        """Update internal state when a settings change is detected."""
        self.clearRegionsAfterPrintFinishes = \
            self._settings.getBoolean(["clearRegionsAfterPrintFinishes"])

        self.mayShrinkRegionsWhilePrinting = \
            self._settings.getBoolean(["mayShrinkRegionsWhilePrinting"])

        self.state.g90InfluencesExtruder = \
            settings().getBoolean(["feature", "g90InfluencesExtruder"])

        self.state.enteringExcludedRegionGcode = \
            self._splitGcodeScript(self._settings.get(["enteringExcludedRegionGcode"]))

        self.state.exitingExcludedRegionGcode = \
            self._splitGcodeScript(self._settings.get(["exitingExcludedRegionGcode"]))

        extendedExcludeGcodes = {}
        for val in self._settings.get(["extendedExcludeGcodes"]):
            val = ExcludedGcode(
                val["gcode"],
                val["mode"],
                val["description"]
            )
            extendedExcludeGcodes[val.gcode] = val
        self.state.extendedExcludeGcodes = extendedExcludeGcodes

        atCommandActions = {}
        for val in self._settings.get(["atCommandActions"]):
            val = AtCommandAction(
                val["command"],
                val["parameterPattern"],
                val["action"],
                val["description"]
            )
            entry = atCommandActions.get(val.command)
            if (entry is None):
                atCommandActions[val.command] = [val]
            else:
                entry.append(val)
        self.state.atCommandActions = atCommandActions

        self.loggingMode = self._settings.get(["loggingMode"])

        self._logger.info(
            "Setting update detected: g90InfluencesExtruder=%s, " +
            "clearRegionsAfterPrintFinishes=%s, mayShrinkRegionsWhilePrinting=%s, " +
            "loggingMode=%s, " +
            "enteringExcludedRegionGcode=%s, exitingExcludedRegionGcode=%s, " +
            "extendedExcludeGcodes=%s, atCommandActions=%s",
            self.state.g90InfluencesExtruder,
            self.clearRegionsAfterPrintFinishes, self.mayShrinkRegionsWhilePrinting,
            self._loggingMode,
            self.state.enteringExcludedRegionGcode,
            self.state.exitingExcludedRegionGcode,
            extendedExcludeGcodes, atCommandActions
        )

    def handleGcodeQueuing(  # pylint: disable=too-many-arguments,unused-argument
            self, commInstance, phase, cmd, cmdType, gcode, subcode=None, tags=None
    ):
        """Gcode processing handler for octoprint.comm.protocol.gcode.queuing plugin hook."""
        if (self._logger.isEnabledFor(logging.DEBUG)):
            self._logger.debug(
                "handleGcodeQueuing: " +
                "phase=%s, cmd=%s, cmdType=%s, gcode=%s, subcode=%s, tags=%s, " +
                "(isActivePrintJob=%s, isExclusionEnabled=%s, excluding=%s)",
                phase, cmd, cmdType, gcode, subcode, tags,
                self.isActivePrintJob, self.state.isExclusionEnabled(), self.state.excluding
            )

        if (gcode and self.isActivePrintJob):
            return self.gcodeHandlers.handleGcode(cmd, gcode, subcode)

        return None

    def handleAtCommandQueuing(self, commInstance, phase, cmd, parameters, tags=None):
        """Command processing handler for octoprint.comm.protocol.atcommand.queuing plugin hook."""
        self._logger.debug(
            "handleAtCommandQueuing: " +
            "phase=%s, command=%s, parameters=%s, tags=%s, " +
            "(isActivePrintJob=%s, isExclusionEnabled=%s, excluding=%s)",
            phase, cmd, parameters, tags,
            self.isActivePrintJob, self.state.isExclusionEnabled(), self.state.excluding
        )

        if (self.isActivePrintJob):
            self.gcodeHandlers.handleAtCommand(commInstance, cmd, parameters)

    def handleScriptHook(  # pylint: disable=unused-argument
            self, commInstance, scriptType, scriptName
    ):
        """Prepend exit region Gcode to the afterPrintDone script if currently excluding."""
        self._logger.debug(
            "handleScriptHook: scriptType=%s, scriptName=%s " +
            "(isActivePrintJob=%s, isExclusionEnabled=%s, excluding=%s)",
            scriptType, scriptName,
            self.isActivePrintJob, self.state.isExclusionEnabled(), self.state.excluding
        )

        if (scriptType == "gcode") and (scriptName == "afterPrintDone"):
            if (self.isActivePrintJob and self.state.excluding):
                self._logger.info("Still excluding at end of print.  Sending exit region commands.")
                return (self.state.exitExcludedRegion("Print done"), None)

        return None
