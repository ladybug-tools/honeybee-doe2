# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*

""" HB-Model Doe2 (eQuest) Properties."""
from collections import defaultdict

from honeybee.model import Model
from honeybee.room import Room
from honeybee.face import Face

from .inputils import blocks as fb
from .inputils.compliance import ComplianceData
from .inputils.sitebldg import SiteBldgData as sbd
from .inputils.run_period import RunPeriod
from .inputils.title import Title
from pprint import pprint


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
    def _header(self):
        """File header.
        NOTE: The header is currently read-only
        """
        return '\n'.join([fb.top_level, fb.abort_diag])

    @property
    def stories(self):
        return self._make_doe_stories(self.host)

    @staticmethod
    def _make_doe_stories(obj):
        storygroups, flr_hgts = Room.group_by_floor_height(obj.rooms, 0.1)

        floor_geom = []
        floor_spaces = []  # * doe2: 'spaces/zones/' wierd ass nomenclature block

        # return storygroups
        # * output at point:
        # [[Room: Room 43ee2, Room: Room 28562],
        # [Room: Room 24600, Room: Room a9bde],
        # [Room: Room 92ca2, Room: Room ae86c],
        # [Room: Room 87225, Room: Room 71235],
        # [Room: Room ae4e3, Room: Room ea9d1]]
        for story in storygroups:
            story_geom = []
            for room in story:
                # *geometry
                story_geom.append([face for face in room.faces])
            floor_geom.append(story_geom)

    @property
    def polygons(self):
        return self._inp_polyblock_maker(self.host)

    @staticmethod
    def _inp_polyblock_maker(obj):
        inp_block = '\n'
        inp_polys = []
        for room in obj.rooms:
            for face in obj.faces:  # eQuest can have interior walls
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
