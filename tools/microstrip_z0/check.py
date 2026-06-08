"""Single-line Z0 sanity check: weeks vs Hammerstad-Jensen closed form."""

from tools.fh_crosscheck.geometry import load_case
from tools.fh_crosscheck.parse_weeks import parse_line_params, run_weeks_text
from tools.microstrip_z0.microstrip import geometric_gap, microstrip_z0


def _pct(ref, val):
    return None if ref == 0 else 100.0 * (val - ref) / ref


def check_z0(case_yaml, weeks_bin="./weeks", workdir=".", tol=10.0):
    """Compare weeks' per-line Z0 against the Hammerstad-Jensen closed form.

    Both weeks and the closed form use the same substrate height -- the
    geometric trace-to-ground gap -- so the comparison is always consistent.
    Returns ``(report_text, flagged)``; ``flagged`` is True if any line's Z0
    differs by more than ``tol`` percent.
    """
    _freq, conductors = load_case(case_yaml)
    params = parse_line_params(run_weeks_text(case_yaml, weeks_bin, workdir))

    lines = [
        "*** Z0 SANITY CHECK: weeks vs Hammerstad-Jensen (%s) ***" % case_yaml,
        "  line   sub_h(m)    weeks_Z0     H-J_Z0      %diff   note",
    ]
    flagged = False
    for i, p in enumerate(params):
        sig = conductors[i + 1]
        w, er = sig["w"], sig["er"]
        h = geometric_gap(conductors, i + 1)  # substrate height from geometry

        note = ""
        if er <= 1.0 or h <= 0.0:
            note = "air / no dielectric (H-J not applicable)"
            hj_text, pd_text = "        n/a", "    n/a"
        else:
            _eff, hj_z0 = microstrip_z0(w, h, er)
            pd = _pct(hj_z0, p["z0"])
            hj_text = "%11.4e" % hj_z0
            pd_text = "  n/a" if pd is None else "%+7.2f%%" % pd
            if pd is not None and abs(pd) > tol:
                note = "over %.0f%% tolerance" % tol
                flagged = True

        lines.append(
            "  %3d  %10.3e  %11.4e %s %s   %s"
            % (i + 1, h, p["z0"], hj_text, pd_text, note)
        )

    if not params:
        lines.append("  (no TRANSMISSION-LINE PARAMETERS section found in weeks output)")
        flagged = True
    return "\n".join(lines), flagged
