import math

from tools.fh_crosscheck.parse_weeks import parse_line_params
from tools.microstrip_z0.microstrip import (
    eff_permittivity,
    geometric_gap,
    microstrip_z0,
)


def test_eff_permittivity_air_and_bounds():
    # Air / no substrate returns 1.0.
    assert eff_permittivity(150e-6, 0.0, 4.4) == 1.0
    assert eff_permittivity(150e-6, 200e-6, 1.0) == 1.0
    # With dielectric, eff_er lies strictly between 1 and er.
    ee = eff_permittivity(150e-6, 200e-6, 4.4)
    assert 1.0 < ee < 4.4


def test_eff_permittivity_matches_weeks_c_formula():
    # Value cross-checked against src/calcl.c calc_eff_dielectric() output
    # for w=150um, h=200um, er=4.4 (weeks prints 3.1118).
    ee = eff_permittivity(150e-6, 200e-6, 4.4)
    assert abs(ee - 3.1118) < 1e-3


def test_microstrip_z0_known_geometry():
    # Consistent microstrip used by examples/test_microstrip.yaml; weeks
    # reports Z0 ~= 81.06 Ohm, so the closed form must land within ~1%.
    eff_er, z0 = microstrip_z0(150e-6, 200e-6, 4.4)
    assert abs(eff_er - 3.1118) < 1e-3
    assert abs(z0 - 81.06) / 81.06 < 0.01


def test_microstrip_z0_increases_for_narrower_line():
    # Narrower trace (smaller w/h) -> higher characteristic impedance.
    _e1, wide = microstrip_z0(400e-6, 200e-6, 4.4)
    _e2, narrow = microstrip_z0(100e-6, 200e-6, 4.4)
    assert narrow > wide


def test_geometric_gap():
    conductors = [
        {"name": "line0", "y": 0.0, "h": 2.0e-6},
        {"name": "line1", "y": 202e-6, "h": 18e-6},
    ]
    assert math.isclose(geometric_gap(conductors, 1), 200e-6, rel_tol=1e-9)


def test_parse_line_params_extracts_z0():
    text = """\
*** TRANSMISSION-LINE PARAMETERS (per line, quasi-TEM) at 30.00 MHz ***

Line     eff_er       Z0(Ohm)      C(F/m)       a_c(dB/m)    a_d(dB/m)    a(dB/m)      beta(rad/m)  eff_er''

  1    +3.1118e+00  +8.1058e+01  +7.2591e-11  +7.9381e-01  +2.1939e-01  +1.0132e+00  +1.1091e+00  +1.4173e-01

  gamma = alpha + j*beta
"""
    params = parse_line_params(text)
    assert len(params) == 1
    assert abs(params[0]["eff_er"] - 3.1118) < 1e-9
    assert abs(params[0]["z0"] - 81.058) < 1e-3
    assert abs(params[0]["eff_er_im"] - 0.14173) < 1e-4
