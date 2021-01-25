# coding=utf-8
"""Module providing the Layer class."""

from __future__ import absolute_import, division

from .CommonMixin import CommonMixin


class Layer(CommonMixin):

    """
    Object containing drawing layer information.

    Attributes
    ----------
    height : number
        The Z height of the layer
    number : number
        The layer number (
    """
    def __init__(self, *args, **kwargs):
        if args:
            toCopy = args[0]
            assert isinstance(toCopy, self.__class__), "Expected a " + self.__class__ + " instance"

            self.height = toCopy.height
            self.number = toCopy.number
        else:
            self.height = float(kwargs.get("height", 0))
            self.number = float(kwargs.get("number", 0))
