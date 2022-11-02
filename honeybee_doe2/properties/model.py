# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*

""" HB-Model Doe2 (eQuest) Properties."""
from .inputils import blocks as fb
from collections import defaultdict
from honeybee.model import Model
from honeybee.room import Room
from honeybee.face import Face


class ModelDoe2Properties(object):
    """_summary_

    Args:
        object (_type_): _description_
    """

    def __init__(self, _host):
        self._host = _host

    @property
    def host(self):
        return self._host

    def duplicate(self, new_host=None):
        """_summary_
        Args:
            new_host (_type_, optional): _description_. Defaults to None.
        Returns:
            _type_: _description_
        """
        # type: (Any) -> ModelDoe2Properties
        _host = new_host or self._host
        new_properties_obj = ModelDoe2Properties(_host)
        return new_properties_obj

    @property
    def stories(self):
        return self._make_doe_stories(self.host)

    @staticmethod
    def _make_doe_stories(obj):
        grouped_rooms, flr_hgts = Room.group_by_floor_height(obj.rooms, 0.1)
        return grouped_rooms

    @property
    def polygons(self):
        return self._inp_polyblock_maker(self.host)

    @staticmethod
    def _inp_polyblock_maker(obj):
        inp_block = '\n'
        inp_polys = []
        for room in obj.rooms:
            for face in obj.faces:
                if str(face.boundary_condition) != 'Surface':
                    inp_polys.append(face.properties.doe2.poly)
        final_form = inp_block.join(pol for pol in inp_polys)
        return final_form  # I don't even know what I'm making a reference to tbh

    @property
    def header(self):
        return '\n'.join([fb.top_level, fb.abort_diag])

    def __str__(self):
        return "Model Doe2 Properties: [host: {}]".format(self.host.display_name)

    def __repr__(self):
        return str(self)

    def ToString(self):
        return self.__repr__()
