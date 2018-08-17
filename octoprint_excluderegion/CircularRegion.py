# coding=utf-8

from __future__ import absolute_import

import json
import uuid
import math

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
