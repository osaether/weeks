"""Orchestrate a full cross-check of one case: weeks vs FastHenry."""

import math

from tools.fh_crosscheck.geometry import load_case
from tools.fh_crosscheck.gen_inp import build_inp
from tools.fh_crosscheck.run_fasthenry import run
from tools.fh_crosscheck.parse_weeks import run_weeks
from tools.fh_crosscheck.report import compare_matrix


def _per_unit_length(z1, z2, l1, l2):
    """Zpul = (Z(l2) - Z(l1)) / (l2 - l1), cancelling length-independent ends."""
    n = len(z1)
    dl = l2 - l1
    return [[(z2[i][j] - z1[i][j]) / dl for j in range(n)] for i in range(n)]


def cross_check(case_yaml, l1=5e-3, l2=10e-3, tol=12.0, keep_inp=None):
    """Run weeks and FastHenry for ``case_yaml`` and return a report string.

    Returns ``(report_text, flagged_total)``.
    """
    frequency, conductors = load_case(case_yaml)
    omega = 2.0 * math.pi * frequency

    weeks_r, weeks_l = run_weeks(case_yaml)

    z1 = run(build_inp(frequency, conductors, l1), frequency,
             keep_dir=(keep_inp + "/l1" if keep_inp else None))
    z2 = run(build_inp(frequency, conductors, l2), frequency,
             keep_dir=(keep_inp + "/l2" if keep_inp else None))
    zpul = _per_unit_length(z1, z2, l1, l2)

    if len(weeks_r) != len(zpul):
        raise ValueError(
            "matrix size mismatch: weeks N=%d vs FastHenry N=%d"
            % (len(weeks_r), len(zpul))
        )

    n = len(zpul)
    fh_r = [[zpul[i][j].real for j in range(n)] for i in range(n)]
    fh_l = [[zpul[i][j].imag / omega for j in range(n)] for i in range(n)]

    header = (
        "================================================================\n"
        "Cross-check: %s\n"
        "  frequency = %.3e Hz | FastHenry lengths L1=%.3g m, L2=%.3g m\n"
        "  tolerance = %.0f%% (soft flag)\n"
        "================================================================"
        % (case_yaml, frequency, l1, l2, tol)
    )

    r_text, r_flag, _, _ = compare_matrix("RESISTANCE (Ohm/m)", weeks_r, fh_r, tol)
    l_text, l_flag, _, _ = compare_matrix("INDUCTANCE (H/m)", weeks_l, fh_l, tol)

    report = "\n\n".join([header, r_text, l_text])
    return report, r_flag + l_flag
