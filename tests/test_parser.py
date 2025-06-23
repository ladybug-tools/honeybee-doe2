"""Tests for the INP reader classes."""

import pytest
from honeybee_doe2.util import parse_inp_string, parse_inp_file

inp_path = r"C:\Users\Steve.marentette.IG\Desktop\eQuest Projects\Airdrie School\Proposed\temp\temp22\Airdrie School.inp"

inp_space = r'''
"L1WNE Perim Spc (G.NE1)" = SPACE
   X                = 38
   Y                = 167
   AZIMUTH          = 80.5377
   SHAPE            = POLYGON
   ZONE-TYPE        = CONDITIONED
   INF-SCHEDULE     = "Inf Sch"
   INF-METHOD       = AIR-CHANGE
   INF-FLOW/AREA    = 0.1518
   PEOPLE-HG-LAT    = 228.178
   PEOPLE-HG-SENS   = 251.18
   EQUIP-LATENT     = ( 0 )
   EQUIP-SENSIBLE   = ( 1 )
   LIGHTING-W/AREA  = ( {0.66*#PA("LPD") + #PA("LPD")} )
   EQUIPMENT-W/AREA = ( {0*#PA("PLUG")} )
   LIGHT-REF-POINT1 = ( 5, 10 )
   VIEW-AZIMUTH     = 180
   AREA/PERSON      = 1076
   POLYGON          = "L1WSpace Polygon 1"
   C-SUB-SRC-BTUH   = ( 0, 0, 0 )
   C-SUB-SRC-KW     = ( 0, 0, 0 )
   C-ACTIVITY-DESC  = *Corridor/Transition*
   ..
'''

inp_file = parse_inp_file(inp_path)

print(inp_file)



u_name, cmd, keys, vals = parse_inp_string(inp_space)
print(inp_space)
print(u_name)
print(cmd)
print(keys)
print(vals)

d = 2