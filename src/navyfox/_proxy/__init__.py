# navyfox._proxy — proxy base and descriptor machinery
from navyfox._proxy.base import Definition, Element, NativeProxy
from navyfox._proxy.descriptors import (
    BoolProperty,
    ChoiceProperty,
    ColorProperty,
    FloatProperty,
    IntProperty,
    ObjectProperty,
    StringProperty,
)

__all__ = [
    "NativeProxy",
    "Element",
    "Definition",
    "BoolProperty",
    "IntProperty",
    "StringProperty",
    "FloatProperty",
    "ChoiceProperty",
    "ColorProperty",
    "ObjectProperty",
]
