# coding=utf-8

from __future__ import absolute_import

import json

# State information associated with an axis (X, Y, Z, E)
class AxisPosition:
  def __init__(self, current = None, homeOffset = 0, offset = 0, absoluteMode = True, unitMultiplier = 1):
    if (isinstance(current, AxisPosition)):
      self.homeOffset = current.homeOffset
      self.offset = current.offset
      self.absoluteMode = current.absoluteMode
      self.unitMultiplier = current.unitMultiplier
      self.current = current.current
    else:
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
