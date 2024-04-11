from ladybug.datatype.temperature import Temperature
from honeybee_doe2.utils.doe_formatters import short_name
from ladybug.datatype.volumeflowrate import VolumeFlowRate

class SwitchDesignHeat:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions
    
    
    @property
    def activity_descriptions(self):
        return self._activity_descriptions
    
    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], room.properties.energy.setpoint.heating_setpoint) \
                                         for room in hb_model.rooms]))
        return cls(activity_description)
 
    def to_inp(self):
        
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR ZONE\n")
        obj_lines.append('TYPE = CONDITIONED\n')
        obj_lines.append('   DESIGN-HEAT-T =\n')
        obj_lines.append('{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": {Temperature().to_ip(values=[act[1]], from_unit="C")[0][0]}\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        
        return switch_statement
    
    def __repr__(self):
        return self.to_inp()
    

class SwitchHeatSchedule:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions
        
    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], \
            short_name(room.properties.energy.setpoint.heating_schedule.display_name)) \
                                         for room in hb_model.rooms]))
        return cls(activity_description)
    
    def to_inp(self):
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR ZONE\n")
        obj_lines.append('TYPE = CONDITIONED\n')
        obj_lines.append('  HEAT-TEMP-SCH = \n')
        obj_lines.append('{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": #SI("{act[1]}_", "SPACE", "HEAT-TEMP-SCH")\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch} \n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        return switch_statement
    
    def __repr__(self):
        return self.to_inp()
    
       
class SwitchDesignCool:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions
    
    
    @property
    def activity_descriptions(self):
        return self._activity_descriptions
    
    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], room.properties.energy.setpoint.cooling_setpoint) \
                                         for room in hb_model.rooms]))
        return cls(activity_description)
 
    def to_inp(self):
        
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR ZONE\n")
        obj_lines.append('TYPE = CONDITIONED\n')
        obj_lines.append('   DESIGN-COOL-T =\n')
        obj_lines.append('{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": {Temperature().to_ip(values=[act[1]], from_unit="C")[0][0]}\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        
        return switch_statement
    
    def __repr__(self):
        return self.to_inp()
    
    
class SwitchCoolSchedule:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions
        
    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], \
            short_name(room.properties.energy.setpoint.cooling_schedule.display_name)) \
                                         for room in hb_model.rooms]))
        return cls(activity_description)
    
    def to_inp(self):
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR ZONE\n")
        obj_lines.append('TYPE = CONDITIONED\n')
        obj_lines.append('  COOL-TEMP-SCH = \n')
        obj_lines.append('{switch(#LR("SPACE","C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": #SI("{act[1]}_", "SPACE", "COOL-TEMP-SCH")\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        return switch_statement
    
    def __repr__(self):
        return self.to_inp()
    
    
class SwitchAreaPerson:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions
        
    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], room.properties.energy.people.area_per_person) \
                                         for room in hb_model.rooms]))
        return cls(activity_description)
        
    def to_inp(self):
        
        obj_lines = []
        obj_lines.append("\nSET-DEFAULT FOR SPACE\n")
        obj_lines.append('   AREA/PERSON =\n')
        obj_lines.append('{switch(#L("C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": {act[1]}\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        
        return switch_statement
    
    def __repr__(self):
        return self.to_inp()


class SwitchPeopleSched:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], short_name(room.properties.energy.people.occupancy_schedule.display_name)) \
            for room in hb_model.rooms]))
        return cls(activity_description)
        
    def to_inp(self):
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR SPACE\n")
        obj_lines.append('  PEOPLE-SCHEDULE = \n')
        obj_lines.append('{switch(#L("C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": #SI("{act[1]}_", "SPACE", "PEOPLE-SCHEDULE")\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        return switch_statement
    
    def __repr__(self):
        return self.to_inp()
    
    
class SwitchOutsideAirFlow:
    def __init__(self, _activity_descriptions):   
        self._activity_descriptions = _activity_descriptions
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
    
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], \
            VolumeFlowRate()._m3_s_to_cfm(room.properties.energy.infiltration.flow_per_exterior_area)) for room in hb_model.rooms]))
        return cls(activity_description)    
    
    def to_inp(self):
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR ZONE\n")
        obj_lines.append('TYPE = CONDITIONED')
        obj_lines.append("  OUTSIDE-AIR-FLOW = \n")
        obj_lines.append('{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": {act[1]}\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        
        return switch_statement
    
    def __repr__(self):
        return self.to_inp()
        
        
class SwitchLightingWArea:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions
    
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], room.properties.energy.lighting.watts_per_area) \
                                        for room in hb_model.rooms]))
        return cls(activity_description)

    def to_inp(self):
        
        obj_lines = []
        obj_lines.append("\nSET-DEFAULT FOR SPACE\n")
        obj_lines.append('   LIGHTING-W/AREA =\n')
        obj_lines.append('{switch(#L("C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": {act[1]}\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        
        return switch_statement
    
    def __repr__(self):
        return self.to_inp()
   
    
class SwitchEquipmentWArea:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions

    
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], room.properties.energy.electric_equipment.watts_per_area) \
                                        for room in hb_model.rooms]))
        return cls(activity_description)

    def to_inp(self):
        
        obj_lines = []
        obj_lines.append("\nSET-DEFAULT FOR SPACE\n")
        obj_lines.append('   EQUIPMENT-W/AREA =\n')
        obj_lines.append('{switch(#L("C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": {act[1]}\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        
        return switch_statement
    
    def __repr__(self):
        return self.to_inp()
    
    
class SwitchLightingSched:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], short_name(room.properties.energy.lighting.schedule.display_name)) \
            for room in hb_model.rooms]))
        return cls(activity_description)
    
    def to_inp(self):
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR SPACE\n")
        obj_lines.append('  LIGHTING-SCHEDUL = \n')
        obj_lines.append('{switch(#L("C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": #SI("{act[1]}_", "SPACE", "LIGHTING-SCHEDUL")\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        return switch_statement
    
    def __repr__(self):
        return self.to_inp() 
   
    
class SwitchEquipmentSched:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], short_name(room.properties.energy.electric_equipment.schedule.display_name)) \
            for room in hb_model.rooms]))
        return cls(activity_description)
    
    def to_inp(self):
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR SPACE\n")
        obj_lines.append('  EQUIP-SCHEDULE = \n')
        obj_lines.append('{switch(#L("C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": #SI("{act[1]}_", "SPACE", "EQUIP-SCHEDULE")\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        return switch_statement
    
    def __repr__(self):
        return self.to_inp()
   
    
class SwitchFlowArea:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], \
            VolumeFlowRate()._m3_s_to_cfm(room.properties.energy.ventilation.flow_per_area))
                                         for room in hb_model.rooms]))
        return cls(activity_description)
    
    def to_inp(self):
        
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR ZONE\n")
        obj_lines.append('TYPE = CONDITIONED\n')
        obj_lines.append('   FLOW/AREA =\n')
        obj_lines.append('{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": {Temperature().to_ip(values=[act[1]], from_unit="C")[0][0]}\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        
        return switch_statement
    
    def __repr__(self):
        return self.to_inp()
    

class SwitchMinFlowRatio:
    def __init__(self, _activity_descriptions, _hb_model):
        self._activity_descriptions = _activity_descriptions
        self._hb_model = _hb_model
    
    @property
    def hb_model(self):
        return self._hb_model
    
    @hb_model.setter
    def hb_model(self, value):
        self._hb_model = value if value is not None else self.hb_model
     
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], room.user_data['MIN-FLOW-RATIO'])
                                    for room in hb_model.rooms]))                              
        return cls(activity_description, hb_model)
    
    def to_inp(self):
           
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR ZONE\n")
        obj_lines.append('TYPE = CONDITIONED\n')
        obj_lines.append('   MIN-FLOW-RATIO =\n')
        obj_lines.append('{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": {act[1]}\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        return switch_statement

    
    def __repr__(self):
        return self.to_inp()
    
    
class SwitchAssignedFlow:
    def __init__(self, _activity_descriptions, _hb_model):
        self._activity_descriptions = _activity_descriptions
        self._hb_model = _hb_model

    @property
    def hb_model(self):
        return self._hb_model

    @hb_model.setter
    def hb_model(self, value):
        self._hb_model = value if value is not None else self.hb_model
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], room.user_data['ASSIGNED-FLOW'])
                                    for room in hb_model.rooms]))                              
        return cls(activity_description, hb_model)

    def to_inp(self):
            
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR ZONE\n")
        obj_lines.append('TYPE = CONDITIONED\n')
        obj_lines.append('   ASSIGNED-FLOW =\n')
        obj_lines.append('{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": {act[1]}\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        return switch_statement

    def __repr__(self):
        return self.to_inp()
    
    
class SwitchHMaxFlowRatio:
    def __init__(self, _activity_descriptions, _hb_model):
        self._activity_descriptions = _activity_descriptions
        self._hb_model = _hb_model

    @property
    def hb_model(self):
        return self._hb_model

    @hb_model.setter
    def hb_model(self, value):
        self._hb_model = value if value is not None else self.hb_model
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], room.user_data['HMAX-FLOW-RATIO'])
                                    for room in hb_model.rooms]))                              
        return cls(activity_description, hb_model)

    def to_inp(self):
            
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR ZONE\n")
        obj_lines.append('TYPE = CONDITIONED\n')
        obj_lines.append('   HMAX-FLOW-RATIO =\n')
        obj_lines.append('{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": {act[1]}\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        return switch_statement

    def __repr__(self):
        return self.to_inp()
    
    
class SwitchMinFlowArea:
    def __init__(self, _activity_descriptions, _hb_model):
        self._activity_descriptions = _activity_descriptions
        self._hb_model = _hb_model

    @property
    def hb_model(self):
        return self._hb_model

    @hb_model.setter
    def hb_model(self, value):
        self._hb_model = value if value is not None else self.hb_model
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        activity_description = list(set([(room.user_data['act_desc'], room.user_data['MIN-FLOW/AREA'])
                                    for room in hb_model.rooms]))                              
        return cls(activity_description, hb_model)

    def to_inp(self):
            
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR ZONE\n")
        obj_lines.append('TYPE = CONDITIONED\n')
        obj_lines.append('   MIN-FLOW/AREA =\n')
        obj_lines.append('{switch(#LR("SPACE", "C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": {act[1]}\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        return switch_statement

    def __repr__(self):
        return self.to_inp()
    
    
class SwitchMinFlowSched:
    def __init__(self, _activity_descriptions):
        self._activity_descriptions = _activity_descriptions
        
    @property
    def activity_descriptions(self):
        return self._activity_descriptions

    @activity_descriptions.setter
    def activity_descriptions(self, value):
        self._activity_descriptions = value if value is not None else self.activity_descriptions
        
    @classmethod
    def from_hb_model(cls, hb_model):
        switch_rooms = []
        for room in hb_model.rooms:
            if room.properties.energy.ventilation is not None:
                switch_rooms.append(room)
                
        activity_description = list(set([(room.user_data['act_desc'], short_name(room.properties.energy.ventilation.schedule.display_name)) \
            for room in switch_rooms]))
        return cls(activity_description)
    
    def to_inp(self):
        obj_lines = []
        obj_lines.append("SET-DEFAULT FOR SPACE\n")
        obj_lines.append('  MIN-FLOW-SCH = \n')
        obj_lines.append('{switch(#L("C-ACTIVITY-DESC"))\n')
        for act in self.activity_descriptions:
            obj_lines.append(f'case "{act[0]}": #SI("{act[1]}_", "SPACE", "MIN-FLOW-SCH")\n')
        obj_lines.append('default: no_default\n')
        obj_lines.append('endswitch}\n')
        obj_lines.append('..\n')
        
        switch_statement = ''.join(obj_lines)
        return switch_statement
        print(str(self.activity_descriptions))
    
    def __repr__(self):
        return self.to_inp()