# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*-

from honeybee.room import Room


class RoomDoe2Properties(object):
    def __init__(self, _host):
        self._host = _host

    @property
    def host(self):
        return self._host

    def duplicate(self, new_host=None):

        _host = new_host or self._host
        new_properties_obj = RoomDoe2Properties(_host)
        return new_properties_obj
