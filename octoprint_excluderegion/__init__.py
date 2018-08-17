# coding=utf-8
#
# OctoPrint plugin that adds the ability to prevent printing within rectangular or circular
# regions of the currently active gcode file.
#

# Thoughts on improvements:
# - Add a way to persist the defined regions for the selected file and restore them if the file is selected again later
#   - Perhaps add comments into the gcode file itself to define the regions?
#     Could possibly add comments that could be used by the cancelobject plugin
#   - If stored as metadata, make sure to compare file hash to ensure it's the same file data

# - Add setting to configure default behavior for retaining/clearing excluded regions when a print completes
#   - Also add checkbox to Gcode viewer UI
# - Add a way to define custom Gcodes to ignore when excluding.  Could be 4 modes:
#   1) Exclude completely (e.g. G4)
#   2) First (only the first command encountered is executed when leaving excluded area)
#   3) Last (only the last command encountered is executed when leaving excluded area)
#   4) Merge (args of each command found are are merged, retaining last value for each arg) and execute one combined command when leaving excluded area (e.g. M204)
# - Setting for GCode to execute when entering an excluded region
# - Setting for GCode to execute when exiting an excluded region

# TODO: Setting to specify a Gcode to look for to indicate we've reached the end script and should no longer exclude moves?  Or comment pattern to search for? (but how to see the comments?)

# TODO: Is a setting needed for control how big a retraction is recorded as one that needs to be recovered after exiting an excluded region (e.g. ignore small retractions like E-0.03)?  What could a reasonable limit be for the default?
#--
# The minimum retraction distance needed to trigger retraction/recovery processing while excluding
# minimumRetractionDistance = 0.1,
#--
# 

# TODO: Add support for multiple extruders? (gcode cmd: "T#" - selects tool #)  Each tool should have its own extruder position/axis.  What about the other axes?
# Each tool has its own offsets and x axis position
# From Marlin source (Marlin_main.cpp:11201):
#   current_position[Y_AXIS] -= hotend_offset[Y_AXIS][active_extruder] - hotend_offset[Y_AXIS][tmp_extruder];
#   current_position[Z_AXIS] -= hotend_offset[Z_AXIS][active_extruder] - hotend_offset[Z_AXIS][tmp_extruder];



from __future__ import absolute_import

import octoprint.plugin

import flask
import re
import math
import logging

from flask.ext.login import current_user
from octoprint.events import Events
from octoprint.settings import settings

from .RectangularRegion import RectangularRegion
from .CircularRegion import CircularRegion
from .AxisPosition import AxisPosition
from .Position import Position
from .RetractionState import RetractionState

__plugin_name__ = "Exclude Region"


regex_float_pattern = "[-+]?[0-9]*\.?[0-9]+"
regex_floatArg = re.compile("^(?P<label>[A-Za-z])(?P<value>%s)" % regex_float_pattern)
regex_split = re.compile("\s+")

EXCLUDED_REGIONS_CHANGED = "ExcludedRegionsChanged"
MM_PER_ARC_SEGMENT = 1
INCHES_PER_MM = 25.4

TWO_PI = 2 * math.pi
IGNORE_GCODE_CMD = None,

EXCLUDE_ALL = "exclude"
EXCLUDE_EXCEPT_FIRST = "first"
EXCLUDE_EXCEPT_LAST = "last"
EXCLUDE_MERGE = "merge"

def __plugin_load__():
  global __plugin_implementation__
  __plugin_implementation__ = ExcludeRegionPlugin()

  global __plugin_hooks__
  __plugin_hooks__ = {
    "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
    "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.handle_gcode_queuing
    #"octoprint.filemanager.preprocessor": __plugin_implementation__.modify_file
  }

class ExcludeRegionPlugin(
  octoprint.plugin.StartupPlugin,
  octoprint.plugin.AssetPlugin,
  octoprint.plugin.SimpleApiPlugin,
  octoprint.plugin.EventHandlerPlugin,
  octoprint.plugin.SettingsPlugin,
  octoprint.plugin.TemplatePlugin
):
  def __init__(self):
    self.g90InfluencesExtruder = False # Will be reset later, based on configured OctoPrint setting
    self.clearRegionsAfterPrintFinishes = False
    self.extendedExcludeGcodes = {}
    self.enteringExcludedRegionGcode = None # GCode to execute when entering an excluded region
    self.exitingExcludedRegionGcode = None  # GCode to execute when leaving an excluded region
    self.activePrintJob = False        # Whether printing or not
    self.resetInternalPrintState(True)

  def resetInternalPrintState(self, clearExcludedRegions = False):
    if (clearExcludedRegions):
        self.excluded_regions = []    # The set of excluded regions

    # Current axis position, home offsets (M206), offsets (G92) and absolute or relative mode
    self.position = Position()

    self.feedRate = 0                 # Current feed rate
    self.feedRate_unitMultiplier = 1  # Unit multiplier to apply to feed rate
    self.excluding = False            # Whether currently in an excluded area or not
    self.lastRetraction = None        # Retraction that may need to be recovered
    self.lastPosition = None          # Last position before entering an excluded area

    # Storage for pending commands to execute when exiting an excluded area
    self.pendingCommands = {}

  def on_after_startup(self):
    self.handle_settings_updated()
    self.notifyExcludedRegionsChanged()

  def get_assets(self):
    return dict(
      js=["js/renderer.js", "js/excluderegion.js"],
      css=["css/excluderegion.css"]
    )

  def get_template_configs(self):
    return [
      dict(type="settings", custom_bindings=True)
    ]

  def get_update_information(self):
    return dict(
      excluderegion=dict(
        displayName=__plugin_name__,
        displayVersion=self._plugin_version,

        type="github_release",
        user="bradcfisher",
        repo="OctoPrint-ExcludeRegionPlugin",
        current=self._plugin_version,

        pip="https://github.com/bradcfisher/OctoPrint-ExcludeRegionPlugin/archive/{target_version}.zip"
      )
    )

  def get_settings_defaults(self):
    return dict(
      clearRegionsAfterPrintFinishes = False,
      enteringExcludedRegionGcode = None,
      exitingExcludedRegionGcode = None,
      extendedExcludeGcodes = [
        {"gcode":"G4", "mode":EXCLUDE_ALL, "description":"Ignore all dwell commands in an excluded area to reduce delays while excluding"},
        {"gcode":"M204", "mode":EXCLUDE_MERGE, "description":"Record default accelleration changes while excluding and apply the most recent values in a single command after exiting the excluded area"},
        {"gcode":"M205", "mode":EXCLUDE_MERGE, "description":"Record advanced setting changes while excluding and apply the most recent values in a single command after exiting the excluded area"}
      ]
    )

  def get_settings_version(self):
    return 1

  def on_settings_migrate(self, target, current):
    # TODO: Migrate settings from current (old) version to target (new) version
    return

  def isActivePrintJob(self):
    return self.activePrintJob

  # Defines POST command endpoints under: /api/plugin/<plugin identifier>/
  def get_api_commands(self):
    return dict(
      addExcludeRegion=["type"],
      updateExcludeRegion=["type", "id"],
      deleteExcludeRegion=["id"],
    )

  def on_api_command(self, command, data):
    if current_user.is_anonymous():
      return "Insufficient rights", 403

    self._logger.info("API command received: %s", data)

    if (command == "deleteExcludeRegion"):
      self.deleteRegion(data.get("id"))
    else:
      type = data.get("type")

      if (type == "RectangularRegion"):
        region = RectangularRegion(**data)
      elif (type == "CircularRegion"):
        region = CircularRegion(**data)
      else:
        raise ValueError("invalid type")

      if (command == "addExcludeRegion"):
        self.addRegion(region)
      elif (command == "updateExcludeRegion"):
        self.replaceRegion(region)
      else:
        raise ValueError("invalid command")

  # Defines response to GET request: /api/plugin/<plugin identifier>
  def on_api_get(self, request):
    return flask.jsonify(
      excluded_regions=[region.toDict() for region in self.excluded_regions]
    )

  def on_event(self, event, payload):
    self._logger.info("Event received: event=%s payload=%s", event, payload)
    if (event == Events.FILE_SELECTED):
      self._logger.info("File selected, resetting internal state")
      self.resetInternalPrintState(True)
      self.notifyExcludedRegionsChanged()
    elif (event == Events.SETTINGS_UPDATED):
      self.handle_settings_updated()
    elif (event == Events.PRINT_STARTED):
      self._logger.info("Printing started")
      self.resetInternalPrintState()
      self.activePrintJob = True
    elif (
      (event == Events.PRINT_DONE)
      or (event == Events.PRINT_FAILED)
      or (event == Events.PRINT_CANCELLING)
      or (event == Events.PRINT_CANCELLED)
      or (event == Events.ERROR)
    ):
      self._logger.info("Printing stopped")
      self.activePrintJob = False
      if (self.clearRegionsAfterPrintFinishes):
        self.resetInternalPrintState(True)
        self.notifyExcludedRegionsChanged()

  def handle_settings_updated(self):
    self.g90InfluencesExtruder = settings().getBoolean(["feature", "g90InfluencesExtruder"])
    self.clearRegionsAfterPrintFinishes = self._settings.getBoolean(["clearRegionsAfterPrintFinishes"])
    self.enteringExcludedRegionGcode = self._settings.get(["enteringExcludedRegionGcode"])
    self.exitingExcludedRegionGcode = self._settings.get(["exitingExcludedRegionGcode"])

    self.extendedExcludeGcodes = {}
    for val in self._settings.get(["extendedExcludeGcodes"]):
      self._logger.info("copy extended gcode entry: %s", val)
      self.extendedExcludeGcodes[val.get("gcode")] = val

    self._logger.info(
      "Setting update detected: g90InfluencesExtruder=%s, clearRegionsAfterPrintFinishes=%s, enteringExcludedRegionGcode=%s, exitingExcludedRegionGcode=%s, extendedExcludeGcodes=%s",
      self.g90InfluencesExtruder, self.clearRegionsAfterPrintFinishes,
      self.enteringExcludedRegionGcode, self.exitingExcludedRegionGcode,
      self.extendedExcludeGcodes
    )

  def handle_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
    if (gcode):
      gcode = gcode.upper()

    if (self._logger.isEnabledFor(logging.DEBUG)):
      self._logger.debug(
        "handle_gcode_queuing: phase=%s, cmd=%s, cmd_type=%s, gcode=%s, subcode=%s, tags=%s, args=%s, kwargs=%s (isActivePrintJob=%s, excluding=%s)",
        phase, cmd, cmd_type, gcode, subcode, tags, args, kwargs, self.activePrintJob, self.excluding
      )

    if (gcode and self.isActivePrintJob()):
      method = getattr(self, "handle_"+ gcode, self.handle_other_gcode)
      return method(comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs)

  def handle_other_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
    if (self._logger.isEnabledFor(logging.DEBUG)):
      self._logger.debug(
        "handle_other_gcode: phase=%s, cmd=%s, cmd_type=%s, gcode=%s, subcode=%s, tags=%s, args=%s, kwargs=%s (isActivePrintJob=%s, excluding=%s, extendedExcludeGcodes=%s)",
        phase, cmd, cmd_type, gcode, subcode, tags, args, kwargs, self.activePrintJob, self.excluding, self.extendedExcludeGcodes
      )

    if (gcode and self.excluding):
      entry = self.extendedExcludeGcodes.get(gcode)
      if (entry != None):
        mode = entry.get("mode")
        if (mode != None):
          self._logger.debug("handle_other_gcode: gcode excluded by extended configuration: mode=%s, cmd=%s", mode, cmd)

          if (mode == EXCLUDE_MERGE):
            pendingArgs = self.pendingCommands.get(gcode)
            if (pendingArgs == None):
              pendingArgs = {}
              self.pendingCommands[gcode] = pendingArgs

            cmd_args = regex_split.split(cmd)
            for index in range(1, len(cmd_args)):
              arg = cmd_args[index]
              pendingArgs[arg[0].upper()] = arg[1:]
          elif (mode == EXCLUDE_EXCEPT_FIRST):
            if (not (gcode in self.pendingCommands)):
              self.pendingCommands[gcode] = cmd
          elif (mode == EXCLUDE_EXCEPT_LAST):
            self.pendingCommands[gcode] = cmd

          return IGNORE_GCODE_CMD

    # Otherwise, let the command process normally
    return

  def getRegion(self, id):
    for region in self.excluded_regions:
      if (region.id == id):
        return region

    return None

  def addRegion(self, region):
    if (self.getRegion(region.id) == None):
      self._logger.info("New exclude region added: %s", region)
      self.excluded_regions.append(region)
      self.notifyExcludedRegionsChanged()
    else:
      raise ValueError("region id collision")

  def deleteRegion(self, idToDelete):
    if (self.isActivePrintJob()):
      raise ValueError("cannot delete region while printing")

    for index in range(0, len(self.excluded_regions)):
      if (self.excluded_regions[index].id == idToDelete):
        del self.excluded_regions[index]
        self.notifyExcludedRegionsChanged()
        return
  
  def replaceRegion(self, newRegion):
    if (newRegion.id == None):
      raise ValueError("id is required for new region")

    for index in range(0, len(self.excluded_regions)):
      region = self.excluded_regions[index]
      if (region.id == newRegion.id):
        if (self.isActivePrintJob() and not newRegion.containsRegion(region)):
          self._logger.info("Cannot replace region %s with new region %s.  New region doesn't contain the old region. (new contains old=%s oldContainsNew=%s)", region, newRegion, newRegion.containsRegion(region), region.containsRegion(newRegion))
          raise ValueError("cannot replace region while printing unless the new region completely contains the original area")
        self.excluded_regions[index] = newRegion
        self.notifyExcludedRegionsChanged()
        return

    raise ValueError("specified region not found")

  def notifyExcludedRegionsChanged(self):
    self._plugin_manager.send_plugin_message(
      self._identifier,
      dict(
        event=EXCLUDED_REGIONS_CHANGED,
        excluded_regions=[region.toDict() for region in self.excluded_regions]
      )
    );

  def isPointExcluded(self, x, y):
    for region in self.excluded_regions:
      if (region.containsPoint(x, y)):
        return True

    return False

  def isAnyPointExcluded(self, *xyPairs):
    xAxis = self.position.X_AXIS
    yAxis = self.position.Y_AXIS
    exclude = False

    for index in range(0, len(xyPairs), 2):
      x = xAxis.setLogicalPosition(xyPairs[index])
      y = yAxis.setLogicalPosition(xyPairs[index + 1])

      if (not exclude and self.isPointExcluded(x, y)):
        exclude = True

    self._logger.debug("isAnyPointExcluded: pt=%s,%s: %s", x, y, "TRUE" if exclude else "FALSE")
    return exclude

  def buildCommand(self, gcode, **kwargs):
    vals = [gcode]

    for key, val in kwargs.iteritems():
      if (val != None):
        vals.append(key + str(val))
    
    if (len(vals) > 1):
      return " ".join(vals)

    return None

  def recordRetraction(self, retract, returnCommands):
    if (self.lastRetraction == None):
      self.lastRetraction = retract;

      if (self.excluding):
        # If this is the first retraction while excluding ensure the retraction actually occurs
        self._logger.info("Initial retraction encountered while excluding, allowing retraction to proceed: retract=%s", retract)
        returnCommands = retract.addRetractCommands(self, returnCommands)
      elif (returnCommands == None):
        returnCommands = [ retract.originalCommand ]
      else:
        returnCommands.append(retract.originalCommand)
    elif (self.lastRetraction.recoverExcluded):
        # Ignore this retraction command and clear recovery flag
        # (prior recovery was excluded, so already retracted)
        self.lastRetraction.recoverExcluded = False
        if (not self.lastRetraction.firmwareRetract):
          self.lastRetraction.feedRate = self.feedRate
    else:
      # This is an additonal retraction that hasn't had it's recovery excluded
      # It doesn't seem like this should occur in a well-formed file
      # Since it's not expected, log it and let it pass through
      self._logger.debug("Encountered multiple retractions without an intervening recovery (excluding=%s).  Allowing this retraction to proceed: %s", self.excluding, retract)
      if (self.excluding):
        returnCommands = retract.addRetractCommands(self, returnCommands)
      elif (returnCommands == None):
        returnCommands = [ retract.originalCommand ]
      else:
        returnCommands.append(retract.originalCommand)

    self._logger.debug("retraction: excluding=%s, retract=%s, returnCommands=%s", self.excluding, retract, returnCommands)

    return returnCommands
    
  def recoverRetractionIfNeeded(self, returnCommands = None, originalCmd = None, fw_recovery = None):
    if (self.lastRetraction != None):
      if (self.excluding):
        if (fw_recovery != None):
          self.lastRetraction.recoverExcluded = True
      else:
        lastRetraction = self.lastRetraction
        if (lastRetraction.recoverExcluded):
          # Recover from the previous retraction
          self._logger.info("Executing pending recovery for previous retraction: %s", lastRetraction)
          returnCommands = lastRetraction.addRecoverCommands(self, returnCommands)

        self.lastRetraction = None

        # Execute the original command
        if (originalCmd != None):
          if (fw_recovery != None) and lastRetraction.recoverExcluded:
            # The command is a recovery, but we just recovered from a previous retraction.
            # That should indicate multiple recoveries without an intervening retraction
            # That isn't really an expected case, so log it
            self._logger.info("Recovery encountered immediately following a pending recovery action: originalCmd=%s, lastRetraction=%s", originalCmd, lastRetraction)

          if (returnCommands != None):
            returnCommands.append(originalCmd);
          else:
            returnCommands = [ originalCmd ];
    elif (not self.excluding and (originalCmd != None)):
      if (fw_recovery != None):
        # This is a recovery that doesn't correspond to a previous retraction
        # It doesn't seem like this should occur (often) in a well-formed file.
        # Cura generates one at the start of the file, but doesn't seem to after that point.
        # Since it's not generally expected, log it
        self._logger.debug("Encountered recovery without a corresponding retraction: %s", originalCmd)

      if (returnCommands != None):
        returnCommands.append(originalCmd);
      else:
        returnCommands = [ originalCmd ];

    if (fw_recovery != None):
      self._logger.debug("recovery: excluding=%s, originalCmd=%s, returnCommands=%s", self.excluding, originalCmd, returnCommands)

    return returnCommands

  def processLinearMoves(self, cmd, e, feedRate, finalZ, *xyPairs):
    if (feedRate != None):
      feedRate *= self.feedRate_unitMultiplier

    eAxis = self.position.E_AXIS
    priorE = eAxis.current
    if (e != None):
      e = eAxis.setLogicalPosition(e)
      deltaE = e - priorE
    else:
      deltaE = 0

    isMove = False

    if (finalZ != None):
      self.position.Z_AXIS.setLogicalPosition(finalZ)
      isMove = True

    if (not isMove):
      for val in xyPairs:
        if (val != None):
          isMove = True
          break

    if (isMove and (feedRate != None)):
      self.feedRate = feedRate

    returnCommands = None

    self._logger.debug(
      "processLinearMoves: cmd=%s, isMove=%s, e=%s, priorE=%s, deltaE=%s, feedRate=%s, finalZ=%s, xyPairs=%s, excluding=%s, lastRetraction=%s",
      cmd, isMove, e, priorE, deltaE, feedRate, finalZ, xyPairs,
      self.excluding, self.lastRetraction
    );

    if (not isMove):
      if (deltaE < 0):   # retraction, record the amount to potentially recover later
        returnCommands = self.recordRetraction(
          RetractionState(e = -deltaE, feedRate = feedRate, originalCommand = cmd), returnCommands
        )
      elif (deltaE > 0): # recovery
        returnCommands = self.recoverRetractionIfNeeded(returnCommands, cmd, False)
      elif (not self.excluding): # something else (no move, no extrude, probably just setting feedrate)
        returnCommands = [ cmd ]
    elif (self.isAnyPointExcluded(*xyPairs)):
      if (not self.excluding):
        self._logger.info("processLinearMoves: START excluding: cmd=%s", cmd)
      self.excluding = True
      self.lastPosition = Position(self.position)

      if (self.enteringExcludedRegionGcode != None):
        returnCommands = [ self.enteringExcludedRegionGcode ]
    elif (self.excluding):
      self.excluding = False

      # Moving back into printable region, process recovery command(s) if needed
      if (returnCommands == None):
        returnCommands = []

      if (self.exitingExcludedRegionGcode != None):
        returnCommands.append(self.exitingExcludedRegionGcode)

      if (len(self.pendingCommands)):
        for gcode, cmdArgs in self.pendingCommands.iteritems():
          if (isinstance(cmdArgs, dict)):
            returnCommands.append(self.buildCommand(gcode, **cmdArgs))
          else:
            returnCommands.append(cmdArgs)
        self.pendingCommands = {}

      returnCommands.append(
        # Set logical extruder position
        "G92 E{e}".format(e=eAxis.nativeToLogical())
      )

      newZ = self.position.Z_AXIS.nativeToLogical()
      oldZ = self.lastPosition.Z_AXIS.nativeToLogical()
      moveZcmd = "G0 F{f} Z{z}".format(
        f=self.feedRate / self.feedRate_unitMultiplier,
        z=newZ
      )

      if (newZ > oldZ):
        # Move Z axis _up_ to new position (hopefully help avoid hitting any part we may pass over)
        returnCommands.append(moveZcmd)

      returnCommands.append(
        # Move X/Y axes to new position
        "G0 F{f} X{x} Y{y}".format(
          f=self.feedRate / self.feedRate_unitMultiplier,
          x=self.position.X_AXIS.nativeToLogical(),
          y=self.position.Y_AXIS.nativeToLogical()
        )
      )

      if (newZ < oldZ):
        # Move Z axis _down_ to new position (hopefully we avoided hitting any part we may pass over)
        returnCommands.append(moveZcmd)

      self._logger.info("processLinearMoves: STOP excluding: cmd=%s, returnCommands=%s", cmd, returnCommands)
    else:
      if (deltaE > 0):
        # Recover any retraction recorded from the excluded region before the next extrusion occurs
        returnCommands = self.recoverRetractionIfNeeded(returnCommands, cmd)
      else:
        returnCommands = [ cmd ]

    self._logger.debug("processLinearMoves: returnCommands=%s", returnCommands)

    if (returnCommands == None):
      returnCommands = IGNORE_GCODE_CMD

    return returnCommands

  #G0, G1 - Linear Move (by convention: G0 - no extrude, G1 - extrude)
  # G0 [E<pos>] [F<rate>] [X<pos>] [Y<pos>] [Z<pos>]
  #   E - amount to extrude while moving
  #   F - feed rate to accelerate to while moving
  def handle_G0(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    e = None
    f = None
    x = None
    y = None
    z = None
    cmd_args = regex_split.split(cmd)
    for index in range(1, len(cmd_args)):
      match = regex_floatArg.search(cmd_args[index])
      if (match is not None):
        label = match.group("label").upper()
        value = float(match.group("value"))
        if (label == "E"):
          e = value
        elif (label == "F"):
          f = value
        elif (label == "X"):
          x = value
        elif (label == "Y"):
          y = value
        elif (label == "Z"):
          z = value

    return self.processLinearMoves(cmd, e, f, z, x, y)

  def handle_G1(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    return self.handle_G0(comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs)

  def plan_arc(self, endX, endY, i, j, clockwise):
    x = self.position.X_AXIS.current;
    y = self.position.Y_AXIS.current;

    radius = math.hypot(i, j);

    # CCW angle of rotation between position and target from the circle center.
    cx = x + i
    cy = y + j
    rt_X = endX - cx
    rt_Y = endY - cy
    angular_travel = math.atan2(-i * rt_Y + j * rt_X, -i * rt_X - j * rt_Y);
    if (angular_travel < 0):
      angular_travel += TWO_PI;
    if (clockwise):
      angular_travel -= TWO_PI;

    # Make a circle if the angular rotation is 0 and the target is current position
    if (angular_travel == 0) and (x == endX) and (y == endY):
      angular_travel = TWO_PI;

    # Compute the number of segments based on the length of the arc
    arcLength = angular_travel * radius
    numSegments = math.min(math.ceil(arcLength / MM_PER_ARC_SEGMENT), 2)

    # TODO: verify this
    angle = math.atan2(-i, -j)
    angular_increment = angular_travel / (numSegments - 1)

    rval = []
    for index in range(1, numSegments):
      angle += angular_increment
      rval += [ cx + math.cos(angle) * radius, cy + math.sin(angle) * radius ]

    rval += [ endX, endY ]

    return rval

  #G2 - Controlled Arc Move (Clockwise)
  #G3 - Controlled Arc Move (Counter-Clockwise)
  # G2 [E<pos>] [F<rate>] R<radius> [X<pos>] [Y<pos>] [Z<pos>] 
  # G2 [E<pos>] [F<rate>] I<offset> J<offset> [X<pos>] [Y<pos>] [Z<pos>] 
  def handle_G2(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    clockwise = (gcode == "G2")
    xAxis = self.position.X_AXIS
    yAxis = self.position.Y_AXIS

    e = None
    f = none
    x = xAxis.current
    y = yAxis.current
    z = zAxis.current
    r = None
    i = 0
    j = 0
    p = None
    cmd_args = regex_split.split(cmd)
    for index in range(1, len(cmd_args)):
      match = regex_floatArg.search(cmd_args[index])
      if (match is not None):
        label = match.group("label").upper()
        value = float(match.group("value"))
        if (label == "X"):
          x = xAxis.logicalToNative(value)
        elif (label == "Y"):
          y = yAxis.logicalToNative(value)
        elif (label == "Z"):
          z = self.position.Z_AXIS.logicalToNative(value)
        elif (label == "E"):
          e = self.position.E_AXIS.logicalToNative(value)
        elif (label == "F"):
          f = value
        elif (label == "R"):
          r = value
        if (label == "I"):
          i = xAxis.logicalToNative(value)
        if (label == "J"):
          j = yAxis.logicalToNative(value)

    # Based on Marlin 1.1.8
    if (r != None):
      p1 = xAxis.current
      q1 = yAxis.current
      p2 = x
      q2 = y

      if (r and (p1 != p2 or q1 != q2)):
        e = (1 if clockwise else 0) ^ (-1 if (r < 0) else 1)
        dx = p2 - p1
        dy = q2 - q1
        d = math.hypot(dx, dy)
        half_d = d / 2
        h = math.sqrt(r*r - half_d*half_d)
        mx = (p1 + p2) / 2
        my = (q1 + q2) / 2
        sx = -dy / d
        sy = -dx / d
        cx = mx + e * h * sx
        cy = my + e * h * sy

        i = cx - p1
        j = cy - q1

    if (i or j):
      xyPairs = self.plan_arc(x, y, i, j, clockwise)
      return self.processLinearMoves(cmd, e, f, z, *xyPairs)

  def handle_G3(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    return self.handle_G2(comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs)

  #G5  - Bezier curve
  # G5 [E<pos>] I<pos> J<pos> P<pos> Q<pos> X<pos> Y<pos>
  #def handle_G5(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    # TODO: Implement

  #G10 - Retract
  def handle_G10(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    self._logger.debug("handle_G10: firmware retraction")
    returnCommands = self.recordRetraction(RetractionState(firmwareRetract = True, originalCommand = cmd), None)
    if (returnCommands == None):
      return IGNORE_GCODE_CMD
    else:
      return returnCommands

  #G11 - Recover (unretract)
  def handle_G11(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    returnCommands = self.recoverRetractionIfNeeded(None, cmd, True)
    if (returnCommands == None):
      return IGNORE_GCODE_CMD
    else:
      return returnCommands

  def setUnitMultiplier(self, unitMultiplier):
    self.feedRate_unitMultiplier = unitMultiplier;
    for axis in self.position:
      axis.setUnitMultiplier(unitMultiplier)

  #G20 - Set units to inches
  def handle_G20(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    self.setUnitMultiplier(INCHES_PER_MM)

  #G21 - Set units to millimeters
  def handle_G21(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    self.setUnitMultiplier(1)

  #G28 - Auto home
  # G28 [X] [Y] [Z]
  #Set the current position to 0 for each axis in the command
  def handle_G28(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    cmd_args = regex_split.split(cmd)
    home_X = False
    home_Y = False
    home_Z = False
    for v in cmd_args:
      v = v.upper()
      if (v.startswith("X")):
        home_X = True
      elif (v.startswith("Y")):
        home_Y = True
      elif (v.startswith("Z")):
        home_Z = True

    if (not (home_X or home_Y or home_Z)):
      home_X = True
      home_Y = True
      home_Z = True

    if (home_X):
      self.position.X_AXIS.setHome()

    if (home_Y):
      self.position.Y_AXIS.setHome()

    if (home_Z):
      self.position.Z_AXIS.setHome()

  def setAbsoluteMode(self, absolute):
    self.position.X_AXIS.setAbsoluteMode(True)
    self.position.Y_AXIS.setAbsoluteMode(True)
    self.position.Z_AXIS.setAbsoluteMode(True)
    if (self.g90InfluencesExtruder):
      self.position.E_AXIS.setAbsoluteMode(True)
  
  #G90 - Set absolute positioning mode
  def handle_G90(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    self.setAbsoluteMode(True)

  #G91 - Set relative positioning mode
  def handle_G91(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    self.setAbsoluteMode(False)

  #G92 - Set current position (the hotend isn't moved, just changes where Marlin thinks it is)
  # G92 [E<pos>] [X<pos>] [Y<pos>] [Z<pos>]
  def handle_G92(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    cmd_args = regex_split.split(cmd)
    for index in range(1, len(cmd_args)):
      match = regex_floatArg.search(cmd_args[index])
      if (match is not None):
        label = match.group("label").upper()
        value = float(match.group("value"))
        if (label == "E"):
          # Note: 1.0 Marlin and earlier stored an offset for E instead of directly updating the position
          #   This assumes the newer behavior
          self.position.E_AXIS.setLogicalPosition(value)
        elif (label == "X"):
          self.position.X_AXIS.setLogicalOffsetPosition(value)
        elif (label == "Y"):
          self.position.Y_AXIS.setLogicalOffsetPosition(value)
        elif (label == "Z"):
          self.position.Z_AXIS.setLogicalOffsetPosition(value)

  #M206 - Set home offsets
  # M206 [P<offset>] [T<offset>] [X<offset>] [Y<offset>] [Z<offset>]
  def handle_M206(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    cmd_args = regex_split.split(cmd)
    for index in range(1, len(cmd_args)):
      match = regex_floatArg.search(cmd_args[index])
      if (match is not None):
        label = match.group("label").upper()
        value = float(match.group("value"))
        if (label == "X"):
          self.position.X_AXIS.setHomeOffset(value)
        elif (label == "Y"):
          self.position.Y_AXIS.setHomeOffset(value)
        elif (label == "Z"):
          self.position.Z_AXIS.setHomeOffset(value)
