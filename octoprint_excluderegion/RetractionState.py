# coding=utf-8

from __future__ import absolute_import

import json

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
      eAxis = excludeRegionPlugin.position.E_AXIS

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