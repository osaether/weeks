"""Run ./weeks on a case YAML and parse its R and L matrices from stdout.

weeks prints each matrix as:
    *** RESISTANCE MATRIX (Ohm/m) ***

                   1           2
      1 +2.0733e+01 +6.7517e+00
      2 +6.7517e+00 +2.0566e+01
The column-index header has bare integers; data rows start with an integer row
index followed by %+.4e floats. We detect data rows by the float format.
"""

import os
import re
import shutil
import subprocess

_ROW_INDEX = re.compile(r"^\d+$")
_FLOATISH = re.compile(r"[.eE]")


def _looks_like_data_row(tokens):
    if len(tokens) < 2 or not _ROW_INDEX.match(tokens[0]):
        return False
    return all(_FLOATISH.search(t) for t in tokens[1:])


def _matrix_after(lines, marker):
    start = next(i for i, l in enumerate(lines) if marker in l)
    rows = []
    for line in lines[start + 1:]:
        tokens = line.split()
        if _looks_like_data_row(tokens):
            rows.append([float(t) for t in tokens[1:]])
        elif rows:
            break
    return rows


def parse_weeks_output(text):
    """Return ``(R, L)``, each a list-of-lists of floats."""
    lines = text.splitlines()
    R = _matrix_after(lines, "RESISTANCE MATRIX")
    L = _matrix_after(lines, "INDUCTANCE MATRIX")
    return R, L


# Column order of the TRANSMISSION-LINE PARAMETERS rows printed by
# calc_line_params() in src/calcl.c (after the leading line index):
#   eff_er  Z0  C  a_c  a_d  a_total  beta  eff_er''
_LINE_PARAM_KEYS = ("eff_er", "z0", "c", "a_c", "a_d", "a_total", "beta", "eff_er_im")


def parse_line_params(text):
    """Return the per-line transmission-line parameters as a list of dicts.

    One dict per signal line, keyed by ``_LINE_PARAM_KEYS``. Empty if the
    section is absent (older builds) or a line was skipped (printed as text).
    """
    lines = text.splitlines()
    rows = _matrix_after(lines, "TRANSMISSION-LINE PARAMETERS")
    out = []
    for row in rows:
        if len(row) != len(_LINE_PARAM_KEYS):
            continue  # e.g. a "(L<=0, skipped)" row
        out.append(dict(zip(_LINE_PARAM_KEYS, row)))
    return out


def run_weeks_text(case_yaml, weeks_bin="./weeks", workdir="."):
    """Copy ``case_yaml`` to ``workdir/test.yaml``, run weeks, return stdout.

    Any pre-existing test.yaml is backed up and restored (even on error).
    """
    test_yaml = os.path.join(workdir, "test.yaml")
    backup = None
    had_existing = os.path.exists(test_yaml)
    if had_existing:
        backup = test_yaml + ".xcbak"
        shutil.copy2(test_yaml, backup)
    try:
        if os.path.abspath(case_yaml) != os.path.abspath(test_yaml):
            shutil.copy2(case_yaml, test_yaml)
        proc = subprocess.run(
            [weeks_bin], cwd=workdir, capture_output=True, text=True,
            timeout=120
        )
        if proc.returncode != 0:
            raise RuntimeError(
                "weeks exited %d.\nstderr:\n%s" % (proc.returncode, proc.stderr)
            )
        return proc.stdout
    finally:
        if backup:
            shutil.move(backup, test_yaml)
        elif os.path.exists(test_yaml):
            os.remove(test_yaml)


def run_weeks(case_yaml, weeks_bin="./weeks", workdir="."):
    """Run weeks on ``case_yaml`` and return its parsed ``(R, L)`` matrices."""
    return parse_weeks_output(run_weeks_text(case_yaml, weeks_bin, workdir))
