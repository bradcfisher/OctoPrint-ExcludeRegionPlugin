# coding=utf-8
"""OctoPrint plugin adding the ability to prevent printing in rectangular or circular regions."""

# Thoughts on improvements:
# - Add a way to persist the defined regions for the selected file and restore them if the file
#   is selected again later
#   - Perhaps add comments into the gcode file itself to define the regions?
#     Could possibly add comments that could be used by the cancelobject plugin
#   - If stored as metadata, make sure to compare file hash to ensure it's the same file data

# TODO: Setting to specify a Gcode to look for to indicate we've reached the end script and should
#       no longer exclude moves?  Or comment pattern to search for? (but how to see the comments?)
#       Likewise, a similar setting for determining when the start gcode has finished.

# TODO: Is a setting needed for controlling how big a retraction is recorded as one that needs to be
#       recovered after exiting an excluded region (e.g. ignore small retractions like E-0.03)?
#       What could a reasonable limit be for the default?
# --
# The minimum retraction distance needed to trigger retraction/recovery processing while excluding
# minimumRetractionDistance = 0.1,
# --
#

# TODO: Add support for multiple extruders? (gcode cmd: "T#" - selects tool #)  Each tool should
#       have its own extruder position/axis.  What about the other axes?
# Each tool has its own offsets and x axis position
# From Marlin source (Marlin_main.cpp:11201):
#   current_position[Y_AXIS] -=
#       hotend_offset[Y_AXIS][active_extruder] - hotend_offset[Y_AXIS][tmp_extruder];
#   current_position[Z_AXIS] -=
#       hotend_offset[Z_AXIS][active_extruder] - hotend_offset[Z_AXIS][tmp_extruder];

from __future__ import absolute_import

import logging

import flask
from flask_login import current_user

import pkg_resources

import octoprint.plugin
from octoprint.events import Events
from octoprint.settings import settings

from .GcodeHandlers import GcodeHandlers
from .RectangularRegion import RectangularRegion
from .CircularRegion import CircularRegion
from .ExcludedGcode import ExcludedGcode, EXCLUDE_ALL, EXCLUDE_MERGE


__plugin_name__ = "Exclude Region"
__plugin_implementation__ = None
__plugin_hooks__ = None

EXCLUDED_REGIONS_CHANGED = "ExcludedRegionsChanged"


# pylint: disable=global-statement
def __plugin_load__():
    """Initialize OctoPrint plugin meta properties."""
    global __plugin_implementation__
    __plugin_implementation__ = ExcludeRegionPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config":
            __plugin_implementation__.getUpdateInformation,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.handleGcodeQueuing
    }


class ExcludeRegionPlugin(
        octoprint.plugin.StartupPlugin,
        octoprint.plugin.AssetPlugin,
        octoprint.plugin.SimpleApiPlugin,
        octoprint.plugin.EventHandlerPlugin,
        octoprint.plugin.SettingsPlugin,
        octoprint.plugin.TemplatePlugin
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
    gcodeHandlers : GcodeHandlers
        GcodeHandlers instance providing the actual Gcode processing
    """

    def __init__(self):
        """
        Declare plugin-specific properties to satisfy pylint.

        The actual initialization is performed by the initialize method.
        """
        self._activePrintJob = None
        self.clearRegionsAfterPrintFinishes = None
        self.mayShrinkRegionsWhilePrinting = None
        self.gcodeHandlers = None
        super(ExcludeRegionPlugin, self).__init__()

    def initialize(self):
        """
        Perform plugin initialization.

        This method is automatically invoked by OctoPrint when the plugin is loaded, and is called
        after all injected properties are populated.
        """
        self._activePrintJob = False
        self.gcodeHandlers = GcodeHandlers(self._logger)
        self.handleSettingsUpdated()
        self.notifyExcludedRegionsChanged()
        self._logger.debug("Plugin initialization complete")

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

    def get_template_configs(self):
        """Register the custom settings interface with OctoPrint."""
        return [
            dict(type="settings", custom_bindings=True)
        ]

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

    def get_settings_defaults(self):
        """Return a dictionary of the default plugin settings."""
        return dict(
            clearRegionsAfterPrintFinishes=False,
            mayShrinkRegionsWhilePrinting=False,
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
            ]
        )

    def get_settings_version(self):
        """Return the plugin settings version supported by this version of the plugin."""
        return 1

    def on_settings_migrate(self, target, current):
        """
        Migrate settings from current (old) version to target (new) version.

        Parameters
        ----------
        target : int
            The settings version to migrate to (should be identical to get_settings_version())
        current : int | None
            The settings version to migrate from (or None if there are no current settings)
        """
        # TODO: Migrate settings from current (old) version to target (new) version
        return

    def isActivePrintJob(self):
        """Whether a print is currently in progress or not."""
        return self._activePrintJob

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
            self.handleDeleteExcludeRegion(data.get("id"))
        else:
            regionType = data.get("type")

            if (regionType == "RectangularRegion"):
                region = RectangularRegion(**data)
            elif (regionType == "CircularRegion"):
                region = CircularRegion(**data)
            else:
                raise ValueError("invalid type")

            if (command == "addExcludeRegion"):
                self.handleAddExcludeRegion(region)
            elif (command == "updateExcludeRegion"):
                self.handleUpdateExcludeRegion(region)
            else:
                raise ValueError("invalid command")

        return None

    def handleAddExcludeRegion(self, region):
        """
        Add a new exclusion region.

        Parameters
        ----------
        region : Region
            The new region to add

        Raises
        ------
        ValueError
            If the specified region has the same id as an existing region.
        """
        self.gcodeHandlers.addRegion(region)
        self.notifyExcludedRegionsChanged()

    def handleDeleteExcludeRegion(self, idToDelete):
        """
        Remove the region with the specified id.

        Parameters
        ----------
        idToDelete : string
            The id of the region to remove.

        Raises
        ------
        ValueError
            If a print is currently in progress.
        """
        if (not self.mayShrinkRegionsWhilePrinting and self.isActivePrintJob()):
            raise ValueError("cannot delete region while printing")

        if (self.gcodeHandlers.deleteRegion(idToDelete)):
            self.notifyExcludedRegionsChanged()

    def handleUpdateExcludeRegion(self, newRegion):
        """
        Replace an existing region with a new one.

        Parameters
        ----------
        region : Region
            The new region to use as a replacement for an existing one with a matching id.

        Raises
        ------
        ValueError
            If the new region does not have an assigned id or a print job is active and the
            old region is not fully contained in the new region.
        """
        self.gcodeHandlers.replaceRegion(
            newRegion,
            not self.mayShrinkRegionsWhilePrinting and self.isActivePrintJob()
        )
        self.notifyExcludedRegionsChanged()

    def notifyExcludedRegionsChanged(self):
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
                excluded_regions=[region.toDict() for region in self.gcodeHandlers.excludedRegions]
            )
        )

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
            excluded_regions=[region.toDict() for region in self.gcodeHandlers.excludedRegions]
        )

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
            self.gcodeHandlers.resetInternalPrintState(True)
            self.notifyExcludedRegionsChanged()
        elif (event == Events.SETTINGS_UPDATED):
            self.handleSettingsUpdated()
        elif (event == Events.PRINT_STARTED):
            self._logger.info("Printing started")
            self.gcodeHandlers.resetInternalPrintState()
            self._activePrintJob = True
        elif (
                (event == Events.PRINT_DONE)
                or (event == Events.PRINT_FAILED)
                or (event == Events.PRINT_CANCELLING)
                or (event == Events.PRINT_CANCELLED)
                or (event == Events.ERROR)
        ):
            self._logger.info("Printing stopped")
            self._activePrintJob = False
            if (self.clearRegionsAfterPrintFinishes):
                self.gcodeHandlers.resetInternalPrintState(True)
                self.notifyExcludedRegionsChanged()

    def handleSettingsUpdated(self):
        """Update internal state when a settings change is detected."""
        self.clearRegionsAfterPrintFinishes = \
            self._settings.getBoolean(["clearRegionsAfterPrintFinishes"])

        self.mayShrinkRegionsWhilePrinting = \
            self._settings.getBoolean(["mayShrinkRegionsWhilePrinting"])

        self.gcodeHandlers.g90InfluencesExtruder = \
            settings().getBoolean(["feature", "g90InfluencesExtruder"])

        self.gcodeHandlers.enteringExcludedRegionGcode = \
            self._settings.get(["enteringExcludedRegionGcode"])

        self.gcodeHandlers.exitingExcludedRegionGcode = \
            self._settings.get(["exitingExcludedRegionGcode"])

        extendedExcludeGcodes = {}
        for val in self._settings.get(["extendedExcludeGcodes"]):
            val = ExcludedGcode(
                val["gcode"],
                val["mode"],
                val["description"]
            )
            self._logger.debug("copy extended gcode entry: %s", val)
            extendedExcludeGcodes[val.gcode] = val
        self.gcodeHandlers.extendedExcludeGcodes = extendedExcludeGcodes

        self._logger.info(
            "Setting update detected: g90InfluencesExtruder=%s, " +
            "clearRegionsAfterPrintFinishes=%s, mayShrinkRegionsWhilePrinting=%s," +
            "enteringExcludedRegionGcode=%s, exitingExcludedRegionGcode=%s, " +
            "extendedExcludeGcodes=%s",
            self.gcodeHandlers.g90InfluencesExtruder,
            self.clearRegionsAfterPrintFinishes, self.mayShrinkRegionsWhilePrinting,
            self.gcodeHandlers.enteringExcludedRegionGcode,
            self.gcodeHandlers.exitingExcludedRegionGcode,
            extendedExcludeGcodes
        )

    # pylint: disable=invalid-name,too-many-arguments,unused-argument
    def handleGcodeQueuing(
            self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None
    ):
        """Gcode processing handler for octoprint.comm.protocol.gcode.queuing plugin hook."""
        if (gcode):
            gcode = gcode.upper()

        if (self._logger.isEnabledFor(logging.DEBUG)):
            self._logger.debug(
                "handleGcodeQueuing: " +
                "phase=%s, cmd=%s, cmd_type=%s, gcode=%s, subcode=%s, tags=%s, " +
                "(isActivePrintJob=%s, excluding=%s)",
                phase, cmd, cmd_type, gcode, subcode, tags,
                self.isActivePrintJob(), self.gcodeHandlers.excluding
            )

        if (gcode and self.isActivePrintJob()):
            return self.gcodeHandlers.handleGcode(cmd, gcode, subcode)

        return None
