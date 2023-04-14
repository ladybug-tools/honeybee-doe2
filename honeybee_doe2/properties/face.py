# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*-

from ..geometry.polygon import DoePolygon


class FaceDoe2Properties(object):

    def __init__(self, _host):
        self._host = _host

    @property
    def host(self):
        return self._host

    @property
    def poly(self):
        """Return a DOE2 Polygon object."""
        my_poly = DoePolygon.from_face(self.host)
        return my_poly.to_inp()

    def duplicate(self, new_host=None):
        # type: (Any) -> FaceDoe2Properties
        _host = new_host or self._host
        new_properties_obj = FaceDoe2Properties(_host)

        return new_properties_obj

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return "Face Doe2 Properties: [host: {}]".format(self.host.display_name)
