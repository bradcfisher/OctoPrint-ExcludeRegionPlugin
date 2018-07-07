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


# TODO: Add support for multiple extruders? (gcode cmd: "T#" - selects tool #)  Each tool should have its own extruder position/axis.  What about the other axes?


from __future__ import absolute_import

import octoprint.plugin
import flask
import re
import os
import json
import uuid
import math
import logging

from flask.ext.login import current_user
from octoprint.events import Events
from octoprint.settings import settings

__plugin_name__ = "Exclude Region"


regex_float_pattern = "[-+]?[0-9]*\.?[0-9]+"
regex_floatArg = re.compile("^(?P<label>[A-Za-z])(?P<value>%s)" % regex_float_pattern)
regex_split = re.compile("\s+")

EXCLUDED_REGIONS_CHANGED = "ExcludedRegionsChanged"
MM_PER_ARC_SEGMENT = 1
INCHES_PER_MM = 25.4

X_AXIS = 0
Y_AXIS = 1
Z_AXIS = 2
E_AXIS = 3

TWO_PI = 2 * math.pi
IGNORE_GCODE_CMD = None,

def __plugin_load__():
  global __plugin_implementation__
  __plugin_implementation__ = ExcludeRegionPlugin()

  global __plugin_hooks__
  __plugin_hooks__ = {
    "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
    "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.handle_gcode_queuing
    #"octoprint.filemanager.preprocessor": __plugin_implementation__.modify_file
  }

# A rectangular region to exclude from printing
class RectangularRegion:
  def __init__(self, **kwargs):
    id = kwargs.get("id", None)
    x1 = float(kwargs.get("x1"))
    y1 = float(kwargs.get("y1"))
    x2 = float(kwargs.get("x2"))
    y2 = float(kwargs.get("y2"))

    if (x2 < x1):
      x1, x2 = x2, x1

    if (y2 < y1):
      y1, y2 = y2, y1

    self.x1 = x1
    self.y1 = y1
    self.x2 = x2
    self.y2 = y2
    if (id == None):
      self.id = str(uuid.uuid4())
    else:
      self.id = id 

  def containsPoint(self, x, y):
    return (x >= self.x1) and (x <= self.x2) and (y >= self.y1) and (y <= self.y2)

  def containsRegion(self, otherRegion):
    if (isinstance(otherRegion, RectangularRegion)):
      return (
        (otherRegion.x1 >= self.x1) and (otherRegion.x2 <= self.x2) and
        (otherRegion.y1 >= self.y1) and (otherRegion.y2 <= self.y2)
      )
    elif (isinstance(otherRegion, CircularRegion)):
      return (
        (otherRegion.cx - otherRegion.r >= self.x1) and (otherRegion.cx + otherRegion.r <= self.x2) and
        (otherRegion.cy - otherRegion.r >= self.y1) and (otherRegion.cy + otherRegion.r <= self.y2)
      )
    else:
      raise ValueError("unexpected type: {otherRegion}".format(otherRegion=otherRegion))

  def toDict(self):
    return {
      'type': self.__class__.__name__,
      'x1': self.x1,
      'y1': self.y1,
      'x2': self.x2,
      'y2': self.y2,
      'id': self.id
    }

  def __repr__(self):
    return json.dumps(self.toDict())


# A circular region to exclude from printing
class CircularRegion:
  def __init__(self, **kwargs):
    id = kwargs.get("id", None)

    self.cx = float(kwargs.get("cx"))
    self.cy = float(kwargs.get("cy"))
    self.r = float(kwargs.get("r"))
    if (id == None):
      self.id = str(uuid.uuid4())
    else:
      self.id = id 

  def containsPoint(self, x, y):
    return self.r >= math.hypot(x - self.cx, y - self.cy)

  def containsRegion(self, otherRegion):
    if (isinstance(otherRegion, RectangularRegion)):
      return (
        self.containsPoint(otherRegion.x1, otherRegion.y1) and
        self.containsPoint(otherRegion.x2, otherRegion.y1) and
        self.containsPoint(otherRegion.x2, otherRegion.y2) and
        self.containsPoint(otherRegion.x1, otherRegion.y2)
      )
    elif (isinstance(otherRegion, CircularRegion)):
      return (
        math.hypot(self.cx - otherRegion.cx, self.cy - otherRegion.cy) + otherRegion.r <= self.r
      )
    else:
      raise ValueError("unexpected type: {otherRegion}".format(otherRegion=otherRegion))

  def toDict(self):
    return {
      'type': self.__class__.__name__,
      'cx': self.cx,
      'cy': self.cy,
      'r': self.r,
      'id': self.id
    }

  def __repr__(self):
    return json.dumps(self.toDict())


# State information associated with an axis (X, Y, Z, E)
class AxisPosition:
  def __init__(self, current = None, homeOffset = 0, offset = 0, absoluteMode = True, unitMultiplier = 1):
    # Current value and offsets are stored internally in mm
    self.current = current    # "native" position relative to the homeOffset + offset
    self.homeOffset = homeOffset
    self.offset = offset
    self.absoluteMode = absoluteMode
    # Conversion factor from logical units (e.g. inches) to mm
    self.unitMultiplier = unitMultiplier

  def toDict(self):
    return {
      'type': self.__class__.__name__,
      'current': self.current,
      'homeOffset': self.homeOffset,
      'offset': self.offset,
      'absoluteMode': self.absoluteMode,
      'unitMultiplier': self.unitMultiplier
    }

  def __repr__(self):
    return json.dumps(self.toDict())

  def setAbsoluteMode(self, absoluteMode = True):
    self.absoluteMode = absoluteMode

  # Updates the offset to the delta between the current position and the specified logical position
  def setLogicalOffsetPosition(self, position):
    self.offset = self.current - self.logicalToNative(position)
    self.current -= self.offset

  # Sets the home offset (M206)
  def setHomeOffset(self, homeOffset):
    self.current += self.homeOffset
    self.homeOffset = homeOffset * self.unitMultiplier
    self.current -= self.homeOffset

  # Resets the axis to the home position
  def setHome(self):
    self.current = 0
    self.offset = 0

  # Sets the conversion factor from logical units (inches, etc) to mm
  def setUnitMultiplier(self, unitMultiplier):
    self.unitMultiplier = unitMultiplier

  # Sets the position given a location in logical units.
  # Returns the new value of the 'current' property.
  def setLogicalPosition(self, position):
    if (position != None):
      self.current = self.logicalToNative(position)

    return self.current

  # Converts the value from logical units (inches, etc) to native units (mm), taking into account
  # any offsets in effect and whether the axis is in relative or absolute positioning mode.
  def logicalToNative(self, value = None, absoluteMode = None):
    if (value == None):
      return self.current;

    value *= self.unitMultiplier

    if (absoluteMode == None):
      absoluteMode = self.absoluteMode

    if (absoluteMode):
      value += self.offset + self.homeOffset
    else:
      value += self.current

    return value

  # Converts the value from native units (mm) to logical units (inches, etc), taking into account
  # any offsets in effect and whether the axis is in relative or absolute positioning mode.
  def nativeToLogical(self, value = None, absoluteMode = None):
    if (value == None):
      value = self.current

    if (absoluteMode == None):
      absoluteMode = self.absoluteMode
    
    if (absoluteMode):
      value -= self.offset + self.homeOffset
    else:
      value -= self.current

    return value / self.unitMultiplier


# Information for a retraction that may need to be restored later
class RetractionState:
  def __init__(self, firmwareRetract=None, e=None, feedRate=None, originalCommand=None):
    non_firmwareRetract = (e != None) or (feedRate != None)
    if (firmwareRetract != None):
      if (non_firmwareRetract):
        raise ValueError("You cannot provide a value for e or feedRate if firmwareRetract is specified")
    elif (not non_firmwareRetract):
      if ((e == None) or (feedRate == None)):
        raise ValueError("You must provide values for both e and feedRate together")
      else:
        raise ValueError("You must provide a value for firmwareRetract or e and feedRate")

    self.recoverExcluded = False # Whether the recovery for this retraction was excluded or not
                                  # If it was excluded, it will need to be processed later
    self.firmwareRetract = firmwareRetract  # This was a firmware retraction (G10)
    self.e = e                    # Amount of filament to extrude when recovering a previous retraction
    self.feedRate = feedRate      # Feed rate for filament recovery
    self.originalCommand = originalCommand  # Original retraction gcode

  def toDict(self):
    rv = {
      'type': self.__class__.__name__,
      'recoverExcluded': self.recoverExcluded,
      'originalCommand': self.originalCommand
    }
    if (self.e == None):
      rv['firmwareRetract'] = self.firmwareRetract
    else:
      rv['e'] = self.e
      rv['feedRate'] = self.feedRate
    return rv

  def __repr__(self):
    return json.dumps(self.toDict())

  def addRetractCommands(self, excludeRegionPlugin, returnCommands = None):
    return self._addCommands(self.e, excludeRegionPlugin, returnCommands)

  def addRecoverCommands(self, excludeRegionPlugin, returnCommands = None):
    return self._addCommands(-self.e, excludeRegionPlugin, returnCommands)

  def _addCommands(self, amount, excludeRegionPlugin, returnCommands):
    if (returnCommands == None):
      returnCommands = []

    if (self.firmwareRetract):
      returnCommands.append("G11")
    else:
      eAxis = excludeRegionPlugin.position[E_AXIS]

      eAxis.current += amount

      returnCommands.append(
        # Set logical extruder position
        "G92 E{e}".format(e=eAxis.nativeToLogical())
      )

      eAxis.current -= amount

      returnCommands.append(
        "G1 F{f} E{e}".format(
          e=eAxis.nativeToLogical(),
          f=self.feedRate / eAxis.unitMultiplier
        )
      )

    return returnCommands


class ExcludeRegionPlugin(
  octoprint.plugin.StartupPlugin,
  octoprint.plugin.AssetPlugin,
  octoprint.plugin.SimpleApiPlugin,
  octoprint.plugin.EventHandlerPlugin
):
  def __init__(self):
    self.excluded_regions = []         # The set of excluded regions
    self.g90InfluencesExtruder = False # Will be reset later, based on configured OctoPrint setting
    self.activePrintJob = False        # Whether printing or not
    self.resetInternalPrintState()

  def resetInternalPrintState(self):
    # Current axiz position, home offsets (M206), offsets (G92) and absolute or relative mode
    self.position = [
      AxisPosition(), # X_AXIS
      AxisPosition(), # Y_AXIS
      AxisPosition(), # Z_AXIS
      AxisPosition(0) # E_AXIS
    ]
    self.feedRate = 0                 # Current feed rate
    self.feedRate_unitMultiplier = 1  # Unit multiplier to apply to feed rate
    self.excluding = False            # Whether currently in an excluded area or not
    self.lastRetraction = None        # Retraction that may need to be recovered
    self.savedM204args = dict()       # Stored values from M204 in excluded region
    self.savedM205args = dict()       # Stored values from M205 in excluded region

  def on_after_startup(self):
    self.handle_settings_updated()
    self.notifyExcludedRegionsChanged()

  def get_assets(self):
    return dict(
      js=["js/renderer.js", "js/excluderegion.js"],
      css=["css/excluderegion.css"]
    )

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
      self.__init__()
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

  def handle_settings_updated(self):
    self.g90InfluencesExtruder = settings().getBoolean(["feature", "g90InfluencesExtruder"])
    self._logger.info("Setting update detected: g90InfluencesExtruder=%s", self.g90InfluencesExtruder)

  def handle_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
    if (gcode):
      gcode = gcode.upper()

    if (self._logger.isEnabledFor(logging.DEBUG)):
      self._logger.debug(
        "handle_gcode_queuing: phase=%s, cmd=%s, cmd_type=%s, gcode=%s, subcode=%s, tags=%s, args=%s, kwargs=%s (isActivePrintJob=%s)",
        phase, cmd, cmd_type, gcode, subcode, tags, args, kwargs, self.activePrintJob
      )

    if (gcode and self.isActivePrintJob()):
      method = getattr(self, "handle_"+ gcode, self.handle_other_gcode)
      return method(comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs)

  def handle_other_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
    # Currently nothing to do here
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
    xAxis = self.position[X_AXIS]
    yAxis = self.position[Y_AXIS]
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
      self._logger.warn("Encountered multiple retractions without an intervening recovery (excluding=%s).  Allowing this retraction to proceed: %s", self.excluding, retract)
      if (self.excluding):
        returnCommands = retract.addRetractCommands(self, returnCommands)
      elif (returnCommands == None):
        returnCommands = [ retract.originalCommand ]
      else:
        returnCommands.append(retract.originalCommand)

    self._logger.info("retraction: excluding=%s, retract=%s, returnCommands=%s", self.excluding, retract, returnCommands)

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
          self._logger.warn("Executing pending recovery for previous retraction: %s", lastRetraction)
          returnCommands = lastRetraction.addRecoverCommands(self, returnCommands)

        self.lastRetraction = None

        # Execute the original command
        if (originalCmd != None):
          if (fw_recovery != None) and lastRetraction.recoverExcluded:
            # The command is a recovery, but we just recovered from a previous retraction.
            # That should indicate multiple recoveries without an intervening retraction
            # That isn't really an expected case, so log it
            self._logger.warn("Recovery encountered immediately following a pending recovery action: originalCmd=%s, lastRetraction=%s", originalCmd, lastRetraction)

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
        self._logger.warn("Encountered recovery without a corresponding retraction: %s", originalCmd)

      if (returnCommands != None):
        returnCommands.append(originalCmd);
      else:
        returnCommands = [ originalCmd ];

    if (fw_recovery != None):
      self._logger.info("recovery: excluding=%s, originalCmd=%s, returnCommands=%s", self.excluding, originalCmd, returnCommands)

    return returnCommands

  def processLinearMoves(self, cmd, e, feedRate, finalZ, *xyPairs):
    if (feedRate != None):
      feedRate *= self.feedRate_unitMultiplier

    eAxis = self.position[E_AXIS]
    priorE = eAxis.current
    if (e != None):
      e = eAxis.setLogicalPosition(e)
      deltaE = e - priorE
    else:
      deltaE = 0

    isMove = False

    if (finalZ != None):
      self.position[Z_AXIS].setLogicalPosition(finalZ)
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
    elif (self.excluding):
      self.excluding = False

      # Moving back into printable region, process recovery command(s) if needed
      if (returnCommands == None):
        returnCommands = []

      if (len(self.savedM204args) > 0):
        returnCommands.append(self.buildCommand("M204", **self.savedM204args))
        self.savedM204args = dict()

      if (len(self.savedM205args) > 0):
        returnCommands.append(self.buildCommand("M205", **self.savedM205args))
        self.savedM205args = dict()

      returnCommands.append(
        # Set logical extruder position
        "G92 E{e}".format(e=eAxis.nativeToLogical())
      )

      returnCommands.append(
        # Move Z axis to new position (hopefully help avoid hitting any part we pass might over)
        "G0 F{f} Z{z}".format(
          f=self.feedRate / self.feedRate_unitMultiplier,
          z=self.position[Z_AXIS].nativeToLogical()
        )
      )

      returnCommands.append(
        # Move X/Y axes to new position
        "G0 F{f} X{x} Y{y}".format(
          f=self.feedRate / self.feedRate_unitMultiplier,
          x=self.position[X_AXIS].nativeToLogical(),
          y=self.position[Y_AXIS].nativeToLogical()
        )
      )

      self._logger.info("processLinearMoves: STOP excluding: cmd=%s, returnCommands=%s", cmd, returnCommands)
    else:
      if (deltaE > 0):
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
    x = self.position[X_AXIS].current;
    y = self.position[Y_AXIS].current;

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
    xAxis = self.position[X_AXIS]
    yAxis = self.position[Y_AXIS]

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
          z = self.position[Z_AXIS].logicalToNative(value)
        elif (label == "E"):
          e = self.position[E_AXIS].logicalToNative(value)
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
    returnCommands = self.recordRetraction(RetractionState(firmwareRetract = True, originalCommand = cmd))
    if (returnCommands == None):
      return IGNORE_GCODE_CMD
    else:
      return returnCommands

  #G11 - Recover (unretract)
  def handle_G11(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    returnCommands = self.recoverRetractionIfNeeded(self, cmd, True)
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
    home = [False,False,False]
    for v in cmd_args:
      v = v.upper()
      if (v.startswith("X")):
        home[X_AXIS] = True
      elif (v.startswith("Y")):
        home[Y_AXIS] = True
      elif (v.startswith("Z")):
        home[Z_AXIS] = True

    if (not (home[X_AXIS] or home[Y_AXIS] or home[Z_AXIS])):
      home = [True,True,True]

    for axisIndex in range(0, 3):
      if (home[axisIndex]):
        self.position[axisIndex].setHome()

  def setAbsoluteMode(self, absolute):
    self.position[X_AXIS].setAbsoluteMode(True)
    self.position[Y_AXIS].setAbsoluteMode(True)
    self.position[Z_AXIS].setAbsoluteMode(True)
    if (self.g90InfluencesExtruder):
      self.position[E_AXIS].setAbsoluteMode(True)
  
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
          self.position[E_AXIS].setLogicalPosition(value)
        elif (label == "X"):
          self.position[X_AXIS].setLogicalOffsetPosition(value)
        elif (label == "Y"):
          self.position[Y_AXIS].setLogicalOffsetPosition(value)
        elif (label == "Z"):
          self.position[Z_AXIS].setLogicalOffsetPosition(value)

  #M204 - Set Starting Acceleration
  # M204 [P<accel>] [R<accel>] [T<accel>]
  def handle_M204(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    if (self.excluding):
      cmd_args = regex_split.split(cmd)
      for index in range(1, len(cmd_args)):
        arg = cmd_args[index]
        self.savedM204args[arg[0].upper()] = arg[1:]

      return IGNORE_GCODE_CMD

  #M205 - Set Advanced Settings
  # M205 [B<µs>] [E<jerk>] [S<feedrate>] [T<feedrate>] [X<jerk>] [Y<jerk>] [Z<jerk>]
  def handle_M205(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    if (self.excluding):
      cmd_args = regex_split.split(cmd)
      for index in range(1, len(cmd_args)):
        arg = cmd_args[index]
        self.savedM205args[arg[0].upper()] = arg[1:]

      return IGNORE_GCODE_CMD

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
          self.position[X_AXIS].setHomeOffset(value)
        elif (label == "Y"):
          self.position[Y_AXIS].setHomeOffset(value)
        elif (label == "Z"):
          self.position[Z_AXIS].setHomeOffset(value)
