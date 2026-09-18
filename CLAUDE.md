# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Run

```bash
# Check dependencies (requires libmeschach-dev and libyaml-dev)
make check-deps

# Build (objects go to build/, executable is ./weeks)
make

# Run — optional input filename; defaults to test.yaml in the current directory
./weeks
./weeks examples/test_fr4.yaml
./weeks --help

# Run preset material examples (passes the example path directly; nothing is copied)
make test-fr4       # FR4 substrate
make test-air       # Air baseline
make test-rogers    # Rogers RO4003C

# Cross-check R/L against the FastHenry field solver (needs fasthenry on PATH)
make check-fasthenry

# Sanity-check per-line Z0 against the Hammerstad-Jensen closed form (no solver)
make check-z0

# Clean
make clean
```

## Tests

All tests are Python/pytest and must be run from the repo root (they import
`tools.fh_crosscheck`). Only the C build deps plus `pytest` are needed; FastHenry
is not required.

```bash
python3 -m pytest -q                                   # everything (what CI runs)
python3 -m pytest tests/ -q                            # C-program regression tests
python3 -m pytest tools/fh_crosscheck/ tools/microstrip_z0/ -q   # harness unit tests
python3 -m pytest tests/test_regressions.py -k "cli_diagnostics" -q   # single test
```

- `tests/test_regressions.py` tests the real C program: `tests/conftest.py` copies
  `src/`, `include/` and the `Makefile` into a temp dir, runs `make` there, and the
  `run_weeks` fixture writes YAML to a per-test `test.yaml` and runs the binary on it.
  Assertions parse stdout (the `TRANSMISSION-LINE PARAMETERS` table) and check stderr
  for `ERROR`/`Warning` text, so output wording is part of the tested contract.
- These cover input validation (invalid numbers, truncated/malformed YAML, aliases,
  >10 conductors), CLI behaviour, mesh warnings, dielectric-loss units, and Makefile
  header-dependency rebuilds. Add a regression here when fixing a bug in the C code.
- CI (`.github/workflows/ci.yml`) runs `make check-deps`, `make`, then `python -m pytest -q`.

For numerical validation beyond the regression tests there are two stdlib-only Python
harnesses in `tools/`:

- `tools/fh_crosscheck/` compares `weeks`' per-unit-length R/L against
  [FastHenry](https://www.fastfieldsolvers.com/) (`make check-fasthenry` or
  `python3 -m tools.fh_crosscheck <case.yaml>`). See `docs/fasthenry-crosscheck.md` for
  setup (FastHenry has no apt package; build from source with `-fcommon` on GCC 10+).
  Single-line R agrees with FastHenry to ~1%; with uniform meshes (`b: 1.0`) all
  self/mutual R/L terms agree within ~2.3%.
- `tools/microstrip_z0/` checks per-line Z0 against the Hammerstad-Jensen microstrip
  closed form (`make check-z0` or `python3 -m tools.microstrip_z0 <case.yaml>`); it
  reuses `fh_crosscheck`'s `geometry`/`parse_weeks`. Both `weeks` and the closed form
  use the same substrate height (the geometric trace-to-ground gap), so the comparison
  is consistent by construction. `examples/test_microstrip.yaml` agrees to ~0.03%;
  multi-line examples show a few percent (per-line H-J ignores inter-line coupling).

Manual sanity check: R/L/|Z| matrices should be finite and symmetric. Changing only
the substrate material (air vs FR4) does **not** change them — but it **does** change
the TRANSMISSION-LINE PARAMETERS section. See "Notes on the codebase" below.

## Architecture

This is a C command-line tool implementing the Partial Element Equivalent Circuit (PEEC) method based on Weeks et al. (IBM, 1979) for calculating resistance and inductance matrices of rectangular conductors on PCB substrates.

### Data flow

1. `input.c` parses the input YAML (`getinput()`) → populates `conductor[]` array and sets `global_frequency`
2. `build.c` discretizes each conductor into rectangular elements → `element[]` array
3. `calcl.c` fills the complex impedance matrix Z (M×M, where M = total mesh elements across all conductors)
4. `weeks.c` (main) inverts Z, then aggregates element-level admittances back to per-conductor quantities → N×N result matrices for R, L, and |Z|
5. `calc_line_params()` in `calcl.c` then derives per-line (quasi-TEM) transmission parameters from the diagonal of the final impedance matrix — Z0, capacitance C, conductor/dielectric attenuation, and complex propagation γ / effective εr. This is the only output the dielectric affects.

### Key structural details

- **`conductor[0]` is always the ground plane**; `conductor[1..N]` are signal traces
- `global_frequency` in `input.c` (default 30 MHz if `frequency:` is omitted) is accessed via `extern double global_frequency` in `weeks.c`
- `main()` takes one optional argument, the input filename (default `test.yaml`); `-h`/`--help` prints usage, more than one argument or an unopenable file exits 1
- Maximum 10 conductors (`MAX_CONDUCTORS` in `include/weeks.h`); more is a hard error, never a silent truncation
- Input validation is all-or-nothing: any invalid conductor or malformed YAML aborts with `ERROR` on stderr and a non-zero exit before any calculation runs. Unknown keys and nested metadata mappings are ignored; `substrate_h` is ignored with a note
- Two non-fatal warnings go to stderr: `build.c` warns when a graded mesh (`b < 1`) has an even `nw`/`nh` (mesh not symmetric), `weeks.c` warns when the ground plane has a single element
- Copper conductivity is hardcoded as `sigma = 58e6` S/m in `calcl.c`

### Source files

| File | Role |
|------|------|
| `src/weeks.c` | `main()`: reads input, builds elements, inverts the impedance matrix (via Meschach's `zm_inverse`), aggregates element admittances into per-conductor R/L, and prints the results |
| `src/input.c` | YAML parser using libyaml; defines `global_frequency` |
| `src/calcl.c` | Builds impedance matrix; adds each filament's self-resistance (ground plane + signal). Computes Hammerstad-Jensen effective εr / dielectric loss (**not** applied to the R/L matrix). `calc_line_params()` here uses them to produce the per-line transmission-line output (Z0, C, attenuation, γ) |
| `src/build.c` | Creates mesh elements from conductor geometry |
| `src/lpp.c` | Neumann partial inductance formula (`lp()`) |
| `tests/` | pytest regression suite that builds and runs the real C binary (see Tests) |
| `tools/fh_crosscheck/` | Python (stdlib-only) FastHenry R/L cross-check harness; not part of the C build |
| `tools/microstrip_z0/` | Python (stdlib-only) Z0 sanity check vs the Hammerstad-Jensen closed form; reuses `fh_crosscheck`'s `geometry`/`parse_weeks`; not part of the C build |

The complex LU factorization / triangular solve / vector ops (`zLUfactor`, `zUsolve`,
`zv_*`, etc.) are **not** vendored in `src/` — they resolve from `libmeschach` at link
time. Three local copies (`zlufctr.c`, `zvecop.c`, `zsolve.c`) were removed after a diff
confirmed them byte-identical to upstream Meschach 1.2b (only `zlufctr.c` differed, by a
removed-duplicate `zLUsolve` and a `HUGE`→`HUGE_VAL` portability tweak — both behavior-
neutral). The actual matrix inversion in `weeks.c` uses Meschach's own `zm_inverse`; the
file defines no custom solver routines.

### Headers

- `include/weeks.h` — `conductor` struct (geometry + dielectric *material* props `er`, `tan_delta`; the substrate **height** is derived from geometry, not stored), `element` struct, `MAX_CONDUCTORS`, material constants (`ER_FR4`, etc.)
- `include/calcl.h` — `calcl()`, `calc_eff_dielectric()`, `calc_dielectric_loss()`, `calc_line_params()` declarations
- `include/lpp.h` — `lp()` declaration

### Notes on the codebase

- The dielectric (`er`, `tan_delta`) does **not** affect the series R/L/|Z| matrices —
  those are dielectric-independent (μr≈1), so the air and FR4 examples produce ~identical
  R/L/|Z| output. The dielectric **does** affect the separate TRANSMISSION-LINE PARAMETERS
  section produced by `calc_line_params()`: εeff, Z0, C, attenuation and propagation γ.
- The substrate **height** is not an input. It is derived from geometry as the trace-to-
  ground gap (`substrate_height()` in `calcl.c`: signal `y` minus ground-plane top), so the
  inductance L and the effective permittivity εeff always refer to the same height. The old
  `substrate_h` field was an AI-era addition redundant with the geometry; it is now ignored
  with a deprecation note if present in an input file.
- The dielectric attenuation `calc_dielectric_loss()` returns has units of 1/m (a
  propagation-loss constant α_d); it is fed into the shunt side of the transmission-line
  calculation, **not** folded into the Ω/m resistance matrix (which would be
  dimensionally wrong).
- `calc_line_params()` uses the quasi-TEM relation LC = εeff/c² with the per-line diagonal
  R/L self-terms. This is a single-line characterization — it does not model inter-line
  capacitive coupling under an inhomogeneous dielectric (that would need a full
  electrostatic P-matrix solve, e.g. FastCap).

## YAML Input Format

All dimensions must be in **meters** (use scientific notation: `1.6e-3` for 1.6 mm).

```yaml
frequency: 30e6   # Hz

conductors:
  - name: line0   # Ground plane (must be first)
    w: 2800e-6    # Width (m)
    h: 2.0e-6     # Thickness (m)
    x: 0.0        # X position of the LEFT edge / min-x corner (m)
    y: 0.0        # Y position of the BOTTOM edge / min-y corner (m)
    nw: 201       # Mesh divisions along width
    nh: 3         # Mesh divisions along height
    b: 0.2        # Mesh density (0.2–0.9)
    er: 4.4       # Relative permittivity
    tan_delta: 0.02      # Loss tangent
  - name: line1   # Signal trace
    ...
```

The substrate **height** is NOT specified — it is the trace-to-ground gap derived
from the `y` coordinates (signal `y` minus ground-plane top). Place the signal trace
at the intended substrate height. A legacy `substrate_h:` key is ignored (with a note).
Omitting `er`/`tan_delta` defaults to air (εr=1.0, no dielectric loss).

## Dependencies

- **GCC** — C compiler
- **Meschach** (`libmeschach-dev`) — matrix/vector operations (provides `ZMAT`, `ZVEC`, etc.)
- **libyaml** (`libyaml-dev`) — YAML parsing

```bash
# Ubuntu/Debian
sudo apt-get install libmeschach-dev libyaml-dev
```
