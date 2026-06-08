"""Run FastHenry and parse its Zc.mat impedance-matrix output.

Zc.mat format (verified against FastHenry 3.0.1):
  Row k:  <nodeA>  to  <nodeB>          (one per port, reverse order)
  Impedance matrix for frequency = <f> <N> x <N>
  <N rows, each N complex entries>      ("<re>  <±im>j", space separated)
  Body rows are in ascending .external port order (data row 1 = port 1),
  even though the "Row k:" header labels above are printed in reverse. Verified
  empirically with an asymmetric multi-port test.
"""

import os
import shutil
import subprocess
import tempfile

_MARKER = "Impedance matrix for frequency ="


class FastHenryNotFound(Exception):
    """`fasthenry` is not on PATH."""


class FastHenryError(Exception):
    """`fasthenry` ran but did not produce a usable Zc.mat."""


def _parse_complex_row(line, n):
    tokens = line.split()
    values = []
    i = 0
    while i + 1 < len(tokens) and len(values) < n:
        re_tok = tokens[i]
        im_tok = tokens[i + 1]
        values.append(complex(float(re_tok), float(im_tok.rstrip("j"))))
        i += 2
    return values


def parse_zc(text, frequency):
    """Parse Zc.mat ``text`` and return the N×N matrix (list of lists of complex)
    for the frequency block nearest ``frequency``."""
    blocks = text.split(_MARKER)
    best = None
    best_delta = None
    for block in blocks[1:]:
        header, _, body = block.partition("\n")
        parts = header.split()
        block_freq = float(parts[0])
        n = int(parts[1])
        rows = []
        for line in body.splitlines():
            if not line.strip():
                continue
            rows.append(_parse_complex_row(line, n))
            if len(rows) == n:
                break
        delta = abs(block_freq - frequency)
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best = rows
    if best is None:
        raise ValueError("no impedance matrix found in Zc.mat output")
    return best


def run(inp_text, frequency, keep_dir=None):
    """Write ``inp_text``, run ``fasthenry`` on it, return the parsed N×N matrix.

    When ``keep_dir`` is None a temporary directory is created and intentionally
    left in place (not cleaned up) so the generated .inp and Zc.mat remain
    available for inspection; acceptable for this developer cross-check tool.

    Raises FastHenryNotFound if the binary is missing, FastHenryError if it runs
    but produces no Zc.mat.
    """
    if shutil.which("fasthenry") is None:
        raise FastHenryNotFound(
            "fasthenry not on PATH — see docs/fasthenry-crosscheck.md for install steps"
        )
    workdir = keep_dir or tempfile.mkdtemp(prefix="fhxc_")
    if keep_dir:
        os.makedirs(keep_dir, exist_ok=True)
    inp_path = os.path.join(workdir, "input.inp")
    with open(inp_path, "w") as handle:
        handle.write(inp_text)
    proc = subprocess.run(
        ["fasthenry", inp_path, "-s", "ludecomp", "-a", "off"], cwd=workdir, capture_output=True, text=True,
        timeout=120
    )
    if proc.returncode != 0:
        raise RuntimeError(f"FastHenry exited with code {proc.returncode}")
    zc_path = os.path.join(workdir, "Zc.mat")
    if not os.path.exists(zc_path):
        raise FastHenryError(
            "fasthenry produced no Zc.mat.\nstdout:\n%s\nstderr:\n%s"
            % (proc.stdout, proc.stderr)
        )
    with open(zc_path) as handle:
        return parse_zc(handle.read(), frequency)
