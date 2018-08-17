# coding=utf-8

from __future__ import absolute_import

import json

from .AxisPosition import AxisPosition

# Encapsulates the current position of all the axes
class Position:
  def __init__(self, position=None):
    if (isinstance(position, Position)):
      self.X_AXIS = AxisPosition(position.X_AXIS)
      self.Y_AXIS = AxisPosition(position.Y_AXIS)
      self.Z_AXIS = AxisPosition(position.Z_AXIS)
      self.E_AXIS = AxisPosition(position.E_AXIS)
    else:
      self.X_AXIS = AxisPosition()
      self.Y_AXIS = AxisPosition()
      self.Z_AXIS = AxisPosition()
      self.E_AXIS = AxisPosition(0)

  def toDict(self):
    return {
      'type': self.__class__.__name__,
      'X_AXIS': self.X_AXIS,
      'Y_AXIS': self.Y_AXIS,
      'Z_AXIS': self.Z_AXIS,
      'E_AXIS': self.E_AXIS
    }

  def __repr__(self):
    return json.dumps(self.toDict())
