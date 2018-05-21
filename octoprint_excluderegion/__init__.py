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
  def __init__(self, current = None, home_offset = 0, offset = 0, absolute_mode = True, unit_multiplier = 1):
    # Current value and offsets are stored internally in mm
    self.current = current    # "native" position relative to the home_offset + offset
    self.home_offset = home_offset
    self.offset = offset
    self.absolute_mode = absolute_mode
    # Conversion factor from logical units (e.g. inches) to mm
    self.unit_multiplier = unit_multiplier

  def toDict(self):
    return {
      'type': self.__class__.__name__,
      'current': self.current,
      'home_offset': self.home_offset,
      'offset': self.offset,
      'absolute_mode': self.absolute_mode,
      'unit_multiplier': self.unit_multiplier
    }

  def __repr__(self):
    return json.dumps(self.toDict())

  def setAbsoluteMode(self, absoluteMode = True):
    self.absolute_mode = absoluteMode

  # Updates the offset to the delta between the current position and the specified logical position
  def setLogicalOffsetPosition(self, position):
    self.offset = self.current - self.logicalToNative(position)
    self.current -= self.offset

  # Sets the home offset (M206)
  def setHomeOffset(self, homeOffset):
    self.current += self.home_offset
    self.home_offset = homeOffset * unitMultiplier
    self.current -= self.home_offset

  # Resets the axis to the home position
  def setHome(self):
    self.current = 0
    self.offset = 0

  # Sets the conversion factor from logical units (inches, etc) to mm
  def setUnitMultiplier(self, unitMultiplier):
    self.unit_multiplier = unitMultiplier

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

    value *= self.unit_multiplier

    if (absoluteMode == None):
      absoluteMode = self.absolute_mode

    if (absoluteMode):
      value += self.offset + self.home_offset
    else:
      value += self.current

    return value

  # Converts the value from native units (mm) to logical units (inches, etc), taking into account
  # any offsets in effect and whether the axis is in relative or absolute positioning mode.
  def nativeToLogical(self, value = None, absoluteMode = None):
    if (value == None):
      value = self.current

    if (absoluteMode == None):
      absoluteMode = self.absolute_mode
    
    if (absoluteMode):
      value -= self.offset + self.home_offset
    else:
      value -= self.current

    return value / self.unit_multiplier


class ExcludeRegionPlugin(
  octoprint.plugin.StartupPlugin,
  octoprint.plugin.AssetPlugin,
  octoprint.plugin.SimpleApiPlugin,
  octoprint.plugin.EventHandlerPlugin
):
  def __init__(self):
    # Current axiz position, home offsets (M206), offsets (G92) and absolute or relative mode
    self.position = [
      AxisPosition(), # X_AXIS
      AxisPosition(), # Y_AXIS
      AxisPosition(), # Z_AXIS
      AxisPosition(0) # E_AXIS
    ]
    self.feedRate = 0                 # Current feed rate
    self.feedRate_unit_multiplier = 1 # Unit multiplier to apply to feed rate

    self.excluded_regions = []        # The set of exclude regions

    # Values to use for the next allowed (non-excluded) printing move
    self.excluding = False            # Whether currently in an exclude area or not
    self.need_recover = False         # Use firmware recovery
    self.recover_e = None             # Amount of filament to extrude when recovering a previous retraction
    self.recover_e_needsRecover = False # Whether a prior retraction recorded in recover_e needs to be recovered or not
    self.recover_e_feedRate = None    # Feed rate for filament recovery

    self.g90InfluencesExtruder = False # Will be reset later, based on configured OctoPrint setting

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
    return self._printer.is_printing() or self._printer.is_paused() or self._printer.is_pausing()

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

    self._logger.info("API command received: data={data}".format(data=str(data)))

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
    self._logger.info("Event received: event={event} payload={payload}".format(event=event, payload=str(payload)))
    if (event == Events.FILE_SELECTED):
      self._logger.info("File selected, resetting internal state")
      self.__init__()
      self.notifyExcludedRegionsChanged()
    elif (event == Events.SETTINGS_UPDATED):
      self.handle_settings_updated()

    #elif (event == Events.PRINT_STARTED):
    #  self._logger.info("Print started, resetting internal state")
    #  self.__init__()

  def handle_settings_updated(self):
    self.g90InfluencesExtruder = settings().getBoolean(["feature", "g90InfluencesExtruder"])
    self._logger.info("Setting update detected: g90InfluencesExtruder={g90InfluencesExtruder}".format(g90InfluencesExtruder = self.g90InfluencesExtruder))

  def handle_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
    gcode = gcode.upper()
    self.log_gcode("Queuing:", comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs)
    if (gcode):
      method = getattr(self, "handle_"+ gcode, self.handle_other_gcode)
      return method(comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs)

  def handle_other_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
    # Currently nothing to do here
    return

  def log_gcode(self, src, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
    self._logger.debug(
      "{src}: phase={phase}, cmd={cmd}, cmd_type={cmd_type}, gcode={gcode}, subcode={subcode}, tags={tags}, args={args}, kwargs={kwargs}".format(
        src=src,
        phase=phase,
        cmd=cmd,
        cmd_type=cmd_type,
        gcode=gcode,
        subcode=subcode,
        tags=tags,
        args=str(args),
        kwargs=str(kwargs)
      )
    )

  def getRegion(self, id):
    for region in self.excluded_regions:
      if (region.id == id):
        return region

    return None

  def addRegion(self, region):
    if (self.getRegion(region.id) == None):
      self._logger.info("New exclude region added: {region}".format(region=region))
      self.excluded_regions.append(region)
      self.notifyExcludedRegionsChanged()
    else:
      raise ValueError("region id collision")

  def deleteRegion(self, idToDelete):
    if (self.isActivePrintJob()):
      raise ValueError("cannot delete region while printing")

    for i in range(0, len(self.excluded_regions)):
      if (self.excluded_regions[i].id == idToDelete):
        del self.excluded_regions[i]
        self.notifyExcludedRegionsChanged()
        return
  
  def replaceRegion(self, newRegion):
    if (newRegion.id == None):
      raise ValueError("id is required for new region")

    for i in range(0, len(self.excluded_regions)):
      region = self.excluded_regions[i]
      if (region.id == newRegion.id):
        if (self.isActivePrintJob() and not newRegion.containsRegion(region)):
          self._logger.info("Cannot replace region {region} with new region {newRegion}.  New region doesn't contain the old region. (new contains old={newContainsOld} oldContainsNew={oldContainsNew})".format(region=region, newRegion=newRegion, newContainsOld=newRegion.containsRegion(region), oldContainsNew=region.containsRegion(newRegion)))
          raise ValueError("cannot replace region while printing unless the new region completely contains the original area")
        self.excluded_regions[i] = newRegion
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

    for i in range(0, len(xyPairs), 2):
      x = xAxis.setLogicalPosition(xyPairs[i])
      y = yAxis.setLogicalPosition(xyPairs[i + 1])

      if (not exclude and self.isPointExcluded(x, y)):
        exclude = True

    self._logger.debug("isAnyPointExcluded: pt={x},{y}: {exclude}".format(x=x, y=y, exclude="TRUE" if exclude else "FALSE"))
    return exclude

  def processLinearMoves(self, cmd, e, feedRate, finalZ, *xyPairs):
    if (feedRate != None):
      self.feedRate = feedRate * self.feedRate_unit_multiplier

    eAxis = self.position[E_AXIS]
    priorE = eAxis.current
    if (e != None):
      e = eAxis.setLogicalPosition(e)
      deltaE = e - priorE
    else:
      deltaE = 0

    self.position[Z_AXIS].setLogicalPosition(finalZ)

    returnCommands = None

    self._logger.debug("processLinearMoves: cmd={cmd}, e={e}, priorE={priorE}, deltaE={deltaE}, feedRate={feedRate}, finalZ={finalZ}, xyPairs={xyPairs}, excluding={excluding}, recover_e_feedRate={recover_e_feedRate}, recover_e={recover_e}".format(
      cmd=str(cmd), e=e, priorE=priorE, deltaE=deltaE, feedRate=feedRate, finalZ=finalZ, xyPairs=str(xyPairs),
      excluding=self.excluding,
      recover_e_feedRate=self.recover_e_feedRate, recover_e=self.recover_e
    ));

    # Ro - Retract immediately before entering excluded area
    # Ei - Extrude inside excluded area
    # Ri - Retract inside excluded area
    # Mo - First move outside excluded area
    #
    # if Ro: store retraction delta; set restore flag = false
    #   If Ei: set restore flag = true
    #   If Ri: set restore flag = false
    # if Mo: restore retraction if restore flag = true

    if (deltaE < 0): # retraction
      if (self.recover_e == None):
        self._logger.debug("processLinearMoves: retraction: deltaE={deltaE} feedRate={feedRate} needsRecover=FALSE".format(deltaE=deltaE, feedRate=feedRate))

        self.recover_e = -deltaE   # Record the amount to recover later
        self.recover_e_feedRate = self.feedRate
        self.recover_e_needsRecover = False

        # Ensure the retraction actually occurs even if the move doesn't
        if (self.excluding):
          self._logger.debug("processLinearMoves: sending G92: priorE={priorE} e={e}".format(priorE=priorE, e=eAxis.current))
          returnCommands = [
            # Set logical extruder position
            "G92 E{e}".format(e=priorE),
            # Perform retraction
            "G0 F{f} E{e}".format(
              e=eAxis.nativeToLogical(),
              f=self.recover_e_feedRate / self.feedRate_unit_multiplier
            )
          ]
    elif (deltaE > 0) and (self.recover_e != None):
      if (not self.excluding):
        self._logger.debug("processLinearMoves: extrude NOT excluding: clearing recover_e={recover_e} needsRecover=None".format(recover_e=self.recover_e))
        self.recover_e = None
      elif (not self.recover_e_needsRecover):
        self._logger.debug("processLinearMoves: extrude IS excluding: recover_e={recover_e} feedRate={feedRate} needsRecover=TRUE".format(recover_e=self.recover_e, feedRate=self.feedRate))
        # The first extrude inside an excluded area following a retract
        self.recover_e_needsRecover = True
        self.recover_e_feedRate = self.feedRate

    if (self.isAnyPointExcluded(*xyPairs)):
      if (not self.excluding):
        self._logger.info("processLinearMoves: START excluding: cmd={cmd}".format(cmd=cmd))
      self.excluding = True
    elif (self.excluding):
      self._logger.info("processLinearMoves: STOP excluding: cmd={cmd}".format(cmd=cmd))
      self.excluding = False

      # Moving back into printable region, process recovery command(s) if needed
      if (returnCommands == None):
        returnCommands = []

      if (self.recover_e_needsRecover):
        eAxis.current -= self.recover_e

      returnCommands.append(
        # Set logical extruder position
        "G92 E{e}".format(e=eAxis.nativeToLogical())
      )
      returnCommands.append(
        # Move to new position
        "G0 F{f} X{x} Y{x} Z{z}".format(
          f=self.feedRate / self.feedRate_unit_multiplier,
          x=self.position[X_AXIS].nativeToLogical(),
          y=self.position[Y_AXIS].nativeToLogical(),
          z=self.position[Z_AXIS].nativeToLogical()
        )
      )

      if (self.need_recover):
        returnCommands.append("G11")
      elif (self.recover_e_needsRecover):
        eAxis.current += self.recover_e
        returnCommands.append(
          "G0 F{f} E{e}".format(
            e=eAxis.nativeToLogical(),
            f=self.recover_e_feedRate / self.feedRate_unit_multiplier
          )
        )
        self.recover_e = None
        self.recover_e_needsRecover = False

      # Ensure final feed rate is correct
      returnCommands.append(
        "G0 F{f}".format(f=self.feedRate / self.feedRate_unit_multiplier)
      )
    else:
      returnCommands = [ cmd ]

    self._logger.debug("processLinearMoves: returnCommands={returnCommands}".format(returnCommands=str(returnCommands)))

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
    for i in range(1, len(cmd_args)):
      match = regex_floatArg.search(cmd_args[i])
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
    for i in range(1, numSegments):
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
    z = None
    r = None
    i = 0
    j = 0
    p = None
    cmd_args = regex_split.split(cmd)
    for i in range(1, len(cmd_args)):
      match = regex_floatArg.search(cmd_args[i])
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
          f = value * self.feedRate_unit_multiplier
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
    if (self.excluding):
      # Ignore if already retracted
      if (self.need_recover):
        return IGNORE_GCODE_CMD
    else:
      self.need_recover = True

  #G11 - Recover (unretract)
  def handle_G11(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    if (self.excluding):
      return IGNORE_GCODE_CMD
    else:
      self.need_recover = False

  def setUnitMultiplier(self, unit_multiplier):
    self.feedRate_unit_multiplier = unit_multiplier
    for axis in self.position:
      axis.setUnitMultiplier(unit_multiplier)

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
    for i in range(1, len(cmd_args)):
      match = regex_floatArg.search(cmd_args[i])
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

  #M206 - Set home offsets
  # M206 [P<offset>] [T<offset>] [X<offset>] [Y<offset>] [Z<offset>]
  def handle_M206(self, comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs):
    cmd_args = regex_split.split(cmd)
    for i in range(1, len(cmd_args)):
      match = regex_floatArg.search(cmd_args[i])
      if (match is not None):
        label = match.group("label").upper()
        value = float(match.group("value"))
        if (label == "X"):
          self.position[X_AXIS].setHomeOffset(value)
        elif (label == "Y"):
          self.position[Y_AXIS].setHomeOffset(value)
        elif (label == "Z"):
          self.position[Z_AXIS].setHomeOffset(value)

  def handle_gcode_sending(self):
    self.log_gcode("Sending", comm_instance, phase, cmd, cmd_type, gcode, subcode, tags, *args, **kwargs)
