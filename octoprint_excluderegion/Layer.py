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
        The layer number
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the instance properties.

        Parameters
        ----------
        toCopy :  Layer
            If provided, the new instance will be a clone of this instance.

        kwargs.height : number
            The Z height of the layer
        kwargs.number : number
            The layer number
        """
        if args:
            toCopy = args[0]
            assert isinstance(toCopy, Layer), "Expected a Layer instance"

            self.height = toCopy.height
            self.number = toCopy.number
        else:
            self.height = float(kwargs.get("height", 0))
            self.number = float(kwargs.get("number", 0))
