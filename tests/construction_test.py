from honeybee_energy.material.opaque import EnergyMaterial, EnergyMaterialNoMass
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing
from honeybee_energy.material.shade import EnergyWindowMaterialShade
from honeybee_energy.material.gas import EnergyWindowMaterialGas
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.windowshade import WindowConstructionShade
from honeybee_energy.construction.air import AirBoundaryConstruction
from honeybee_energy.schedule.ruleset import ScheduleRuleset


def test_material_to_inp():
    """Test the EnergyMaterial to_inp method."""
    concrete = EnergyMaterial('Concrete', 0.2, 0.5, 800, 1200,
                              'MediumSmooth', 0.95, 0.75, 0.8)
    inp_str = concrete.to_inp()

    assert inp_str == \
        '"Concrete" = MATERIAL\n' \
        '   TYPE                     = PROPERTIES\n' \
        '   THICKNESS                = 0.656\n' \
        '   CONDUCTIVITY             = 0.289\n' \
        '   DENSITY                  = 49.944\n' \
        '   SPECIFIC-HEAT            = 0.287\n' \
        '   ..\n'


def test_material_nomass_to_inp():
    """Test the EnergyMaterialNoMass to_inp method."""
    insul_r2 = EnergyMaterialNoMass('Insulation R-2', 2, 'MediumSmooth', 0.95, 0.75, 0.8)
    inp_str = insul_r2.to_inp()

    assert inp_str == \
        '"Insulation R-2" = MATERIAL\n' \
        '   TYPE                     = RESISTANCE\n' \
        '   RESISTANCE               = 11.356527\n' \
        '   ..\n'


def test_opaque_construction_to_inp():
    """Test the OpaqueConstruction to_inp method."""
    concrete = EnergyMaterial('Concrete', 0.15, 2.31, 2322, 832, 'MediumRough',
                              0.95, 0.75, 0.8)
    insulation = EnergyMaterialNoMass('Insulation R-3', 3, 'MediumSmooth')
    wall_gap = EnergyMaterial('Wall Air Gap', 0.1, 0.67, 1.2925, 1006.1)
    gypsum = EnergyMaterial('Gypsum', 0.0127, 0.16, 784.9, 830, 'MediumRough',
                            0.93, 0.6, 0.65)
    wall_constr = OpaqueConstruction(
        'Generic Wall Construction', [concrete, insulation, wall_gap, gypsum])
    inp_str = wall_constr.to_inp()

    assert inp_str == \
        '"Generic Wall Construction_l" = LAYERS\n' \
        '   MATERIAL                 = (\n' \
        '      "Concrete",\n' \
        '      "Insulation R-3",\n' \
        '      "Wall Air Gap",\n' \
        '      "Gypsum",\n' \
        '   )\n' \
        '   ..\n' \
        '"Generic Wall Construction" = CONSTRUCTION\n' \
        '   TYPE                     = LAYERS\n' \
        '   ABSORPTANCE              = 0.75\n' \
        '   ROUGHNESS                = 3\n' \
        '   LAYERS                   = "Generic Wall Construction_l"\n' \
        '   ..\n'


def test_window_construction_to_inp():
    """Test the WindowConstruction to_inp method."""
    simple_double_low_e = WindowConstruction.from_simple_parameters(
        'NECB Window Construction', 1.7, 0.4)
    lowe_glass = EnergyWindowMaterialGlazing(
        'Low-e Glass', 0.00318, 0.4517, 0.359, 0.714, 0.207,
        0, 0.84, 0.046578, 1.0)
    clear_glass = EnergyWindowMaterialGlazing(
        'Clear Glass', 0.005715, 0.770675, 0.07, 0.8836, 0.0804,
        0, 0.84, 0.84, 1.0)
    gap = EnergyWindowMaterialGas('air gap', thickness=0.0127)
    double_low_e = WindowConstruction(
        'Double Low-E Window', [lowe_glass, gap, clear_glass])
    double_clear = WindowConstruction(
        'Double Clear Window', [clear_glass, gap, clear_glass])
    triple_clear = WindowConstruction(
        'Triple Clear Window', [clear_glass, gap, clear_glass, gap, clear_glass])

    inp_str = simple_double_low_e.to_inp()
    assert inp_str == \
        '"NECB Window Construction" = GLASS-TYPE\n' \
        '   TYPE                     = SHADING-COEF\n' \
        '   SHADING-COEF             = 0.46\n' \
        '   GLASS-CONDUCT            = 0.302373\n' \
        '   ..\n'

    inp_str = double_low_e.to_inp()
    assert inp_str == \
        '"Double Low-E Window" = GLASS-TYPE\n' \
        '   TYPE                     = SHADING-COEF\n' \
        '   SHADING-COEF             = 0.488\n' \
        '   GLASS-CONDUCT            = 0.299039\n' \
        '   ..\n'

    inp_str = double_clear.to_inp()
    assert inp_str == \
        '"Double Clear Window" = GLASS-TYPE\n' \
        '   TYPE                     = SHADING-COEF\n' \
        '   SHADING-COEF             = 0.791\n' \
        '   GLASS-CONDUCT            = 0.479229\n' \
        '   ..\n'
    
    inp_str = triple_clear.to_inp()
    assert inp_str == \
        '"Triple Clear Window" = GLASS-TYPE\n' \
        '   TYPE                     = SHADING-COEF\n' \
        '   SHADING-COEF             = 0.688\n' \
        '   GLASS-CONDUCT            = 0.309475\n' \
        '   ..\n'


def test_window_construction_shade_to_inp():
    """Test the WindowConstructionShade to_inp method."""
    lowe_glass = EnergyWindowMaterialGlazing(
        'Low-e Glass', 0.00318, 0.4517, 0.359, 0.714, 0.207,
        0, 0.84, 0.046578, 1.0)
    clear_glass = EnergyWindowMaterialGlazing(
        'Clear Glass', 0.005715, 0.770675, 0.07, 0.8836, 0.0804,
        0, 0.84, 0.84, 1.0)
    gap = EnergyWindowMaterialGas('air gap', thickness=0.0127)
    shade_mat = EnergyWindowMaterialShade(
        'Low-e Diffusing Shade', 0.005, 0.15, 0.5, 0.25, 0.5, 0, 0.4,
        0.2, 0.1, 0.75, 0.25)
    window_constr = WindowConstruction('Double Low-E', [lowe_glass, gap, clear_glass])
    double_low_e_shade = WindowConstructionShade(
        'Double Low-E with Shade', window_constr, shade_mat, 'Exterior',
        'OnIfHighSolarOnWindow', 200)

    inp_str = double_low_e_shade.to_inp()
    assert inp_str == \
        '"Double Low-E with Shade" = GLASS-TYPE\n' \
        '   TYPE                     = SHADING-COEF\n' \
        '   SHADING-COEF             = 0.488\n' \
        '   GLASS-CONDUCT            = 0.299039\n' \
        '   ..\n'


def test_air_construction_to_inp():
    """Test the AirBoundaryConstruction to_inp method."""
    default_constr = AirBoundaryConstruction('Default Air Construction')
    night_flush = ScheduleRuleset.from_daily_values(
        'Night Flush', [1, 1, 1, 1, 1, 1, 1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
                        0.5, 0.5, 0.5, 0.5, 0.5, 1, 1, 1])
    night_flush_constr = AirBoundaryConstruction('Night Flush Boundary', 0.4, night_flush)

    inp_str = default_constr.to_inp()
    assert inp_str == \
        '"Default Air Construction" = CONSTRUCTION\n' \
        '   TYPE                     = U-VALUE\n' \
        '   U-VALUE                  = 1.0\n' \
        '   ..\n'
    
    inp_str = night_flush_constr.to_inp()
    assert inp_str == \
        '"Night Flush Boundary" = CONSTRUCTION\n' \
        '   TYPE                     = U-VALUE\n' \
        '   U-VALUE                  = 1.0\n' \
        '   ..\n'
    
