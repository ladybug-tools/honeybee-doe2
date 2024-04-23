"""Global settings and configurations governing the translation process."""

# global parameters that may need to be adjusted in the future
DOE2_TOLERANCE = 0.03  # current best guess for DOE-2 absolute tolerance in Feet
DOE2_ANGLE_TOL = 1.0  # current best guess for DOE-2 angle tolerance in degrees
DOE2_INTERIOR_BCS = ('Surface', 'Adiabatic', 'OtherSideTemperature')
GEO_CHARS = 24  # number of original characters used in names of geometry
RES_CHARS = 30  # number of characters used in names of resources (constructions, etc.)
