"""Hammerstad-Jensen microstrip closed form, and a single-line Z0 sanity
check against weeks' TRANSMISSION-LINE PARAMETERS output.

This is an independent cross-check of weeks' per-line characteristic impedance:
weeks derives Z0 = c * L / sqrt(eff_er) from its PEEC inductance L and the
effective permittivity, whereas the Hammerstad-Jensen formulas below give
eff_er and Z0 purely from the microstrip geometry (w, h, er). Agreement
validates the PEEC inductance against a published closed form, complementing
the FastHenry R/L crosscheck.

Both sides use the same substrate height -- the geometric trace-to-ground gap
(``geometric_gap`` below) -- which is also what weeks uses for eff_er, so the
comparison is consistent by construction.
"""

import math

ETA0 = 376.730313668  # free-space wave impedance (Ohm)


def eff_permittivity(w, h, er):
    """Hammerstad-Jensen effective permittivity. Mirrors calc_eff_dielectric()
    in src/calcl.c exactly (same branches and constants)."""
    if h <= 0.0 or er <= 1.0:
        return 1.0
    u = w / h
    a = (1.0
         + (1.0 / 49.0) * math.log((u ** 4 + (u / 52.0) ** 2)
                                   / (u ** 4 + 0.432))
         + (1.0 / 18.7) * math.log(1.0 + (u / 18.1) ** 3))
    b = 0.564 * ((er - 0.9) / (er + 3.0)) ** 0.053
    return (er + 1.0) / 2.0 + ((er - 1.0) / 2.0) * (1.0 + 10.0 / u) ** (-a * b)


def microstrip_z0(w, h, er):
    """Return ``(eff_er, Z0)`` for a microstrip of width ``w``, substrate
    height ``h`` and relative permittivity ``er`` (Hammerstad-Jensen, zero
    thickness). ``Z0`` is in ohms."""
    eff_er = eff_permittivity(w, h, er)
    u = w / h
    fu = 6.0 + (2.0 * math.pi - 6.0) * math.exp(-((30.666 / u) ** 0.7528))
    z0_air = (ETA0 / (2.0 * math.pi)) * math.log(fu / u + math.sqrt(1.0 + (2.0 / u) ** 2))
    return eff_er, z0_air / math.sqrt(eff_er)


def geometric_gap(conductors, line_index):
    """Vertical gap (m) between the bottom of signal conductor ``line_index``
    (1-based among signal traces) and the top of the ground plane (index 0)."""
    ground = conductors[0]
    sig = conductors[line_index]
    return sig["y"] - (ground["y"] + ground["h"])
