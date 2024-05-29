# coding=utf-8
"""Model DOE-2 Properties."""


class ModelDoe2Properties(object):
    """DOE-2 Properties for Honeybee Model.

    Args:
        host: A honeybee_core Model object that hosts these properties.

    Properties:
        * host
    """

    def __init__(self, host):
        """Initialize ModelDoe2Properties."""
        self._host = host

    @property
    def host(self):
        """Get the Model object hosting these properties."""
        return self._host

    def to_dict(self):
        """Return Model DOE-2 properties as a dictionary."""
        return {'doe2': {'type': 'ModelDoe2Properties'}}

    def apply_properties_from_dict(self, data):
        """Apply the energy properties of a dictionary to the host Model of this object.

        Args:
            data: A dictionary representation of an entire honeybee-core Model.
                Note that this dictionary must have ModelEnergyProperties in order
                for this method to successfully apply the energy properties.
        """
        assert 'doe2' in data['properties'], \
            'Dictionary possesses no ModelDoe2Properties.'
        room_doe2_dicts = []
        if 'rooms' in data and data['rooms'] is not None:
            for room_dict in data['rooms']:
                try:
                    room_doe2_dicts.append(room_dict['properties']['doe2'])
                except KeyError:
                    room_doe2_dicts.append(None)
            for room, r_dict in zip(self.host.rooms, room_doe2_dicts):
                if r_dict is not None:
                    room.properties.doe2.apply_properties_from_dict(r_dict)

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Model DOE2 Properties: [host: {}]'.format(self.host.display_name)
