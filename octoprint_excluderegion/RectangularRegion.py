# coding=utf-8

from __future__ import absolute_import

import json
import uuid

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
