# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*-
"""This is called during __init__and extends the base honeybee class Properties with a new ._doe2 slot"""

from honeybee.properties import (
    ModelProperties,
    RoomProperties,
    FaceProperties,
    # ApertureProperties,
    # ShadeProperties #* bldg | context disangination important for 90.1 baseline hokeypokey
)

from .properties.model import ModelDoe2Properties
from .properties.room import RoomDoe2Properties
from .properties.face import FaceDoe2Properties
# from .properties.aperture import ApertureDoe2Properties
# Step 1)
# set a private ._doe2 attribute on each relevant HB-Core Property class to None
setattr(ModelProperties, '_doe2', None)
setattr(RoomProperties, '_doe2', None)
setattr(FaceProperties, '_doe2', None)
#setattr(ApertureProperties, '_doe2', None)
#setattr(ShadeProperties, '_doe2', None)


def model_doe2_properties(self):
    if self._doe2 is None:
        self._doe2 = ModelDoe2Properties(self.host)
    return self._doe2


def room_doe2_properties(self):
    if self._doe2 is None:
        self._doe2 = RoomDoe2Properties(self.host)
    return self._doe2


def face_doe2_properties(self):
    if self._doe2 is None:
        self._doe2 = FaceDoe2Properties(self.host)
    return self._doe2


# def aperture_doe2_properties(self):
#     if self._doe2 is None:
#         self._doe2 = ApertureDoe2Properties(self.host)
#     return self._doe2


# Step 3)
# add public .doe2 property methods to the Properties classes
setattr(ModelProperties, 'doe2', property(model_doe2_properties))
setattr(RoomProperties, 'doe2', property(room_doe2_properties))
setattr(FaceProperties, 'doe2', property(face_doe2_properties))
#setattr(ApertureProperties, 'doe2', property(aperture_doe2_properties))
