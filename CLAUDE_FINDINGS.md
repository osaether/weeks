# CLAUDE_FINDINGS.md

Deep-analysis findings for the `weeks` PEEC calculator, 2026-09-18, against
`main` at `d8b7bf7`. Every numerical claim below was reproduced by running the
built binary or a small C harness against `src/lpp.c`; the commands are given so
they can be re-run. Ordered by severity.

Legend: **[bug]** wrong or misleading output · **[robustness]** silent bad input ·
**[model]** physics limitation worth documenting or fixing · **[perf]** scaling.

---

## 1. [bug] `lp()` loses all precision for well-separated elements

`src/lpp.c` evaluates Weeks' closed form as a signed sum of 16 `F()` terms of
magnitude ~`d²·ln d / (area₁·area₂)`, which cancel down to a result of order
`1e-6`. Once an element's separation `d` exceeds ~10³× its smallest side, the
cancellation exhausts double precision.

Harness (`element a` of side `s = 1 µm`, elements `b`, `c` at `d` and `2d`; the
difference `lp(a,b) − lp(a,c)` must equal the thin-filament value
`2e-7·ln 2 = 1.3863e-7`):

| d/s | `lp(a,b) − lp(a,c)` | rel. error |
|-----|---------------------|------------|
| 10² | 1.38629446e-7 | 7e-8 |
| 10³ | 1.39304001e-7 | **5e-3** |
| 10⁴ | −3.31e-6 | **wrong sign, 25×** |
| 10⁵ | 0.0 | total loss |
| 10⁶ | −23.1 | garbage |

The harness uses square elements; for a `w × h` element the cancellation error
scales as `ε·d⁴/(w²·h²)`, so the thin dimension dominates. The shipped examples
sit at the edge of this regime: the ground plane is 2 µm/3 = 0.67 µm thick per
element and 2.8 mm wide, so d/h ≈ 4·10³ across the plane. The far mutual
*differences* carry ~0.1–0.3 % error (checked against the filament formula at
2.0 mm vs 2.8 mm: 6.743e-8 vs 6.729e-8), which is ~1e-4 of each `lp` entry and
about the same on the final reference-subtracted L — the examples are fine.
The risk is refinement: the input limits allow `nh: 100`, i.e. 20 nm-tall
ground elements (width unchanged at ~4.7 µm), which puts the error at ~1–2 %
of each entry and tens of percent on the loop terms after reference
subtraction. A user who "refines the ground mesh and checks convergence" —
which `weeks.c:73` tells them to do — will therefore see results *diverge*
with refinement, with no warning.

Making `F()` compute in `long double` (the code already calls `logl`/`atanl`
but throws the extra bits away by returning `double`) only moves the breakdown
from d/s ≈ 10³ to ≈ 10⁴. The real fix is a far-field branch: for
d/s above ~50–100, replace the closed form with the filament/multipole
expansion `−2e-7·ln(d_centroid) + O((s/d)²)` (this is what FastHenry does).
Add a regression test that compares `lp` differences to the filament limit
across the d/s range above.

Repro: `gcc -O2 -Iinclude lptest.c src/lpp.c -lm` with the harness in this
session's scratchpad (`lptest.c`, 20 lines).

## 2. [bug] Transmission-line C and Z0 are frequency-dependent and meaningless below the skin-effect regime

`calc_line_params()` derives `C = εeff/(c²·L_ii)` from the *frequency-dependent*
`L_ii` of the R/L matrix. That L includes internal inductance and the
low-frequency spreading of the return current across the whole ground plane, so
C — a purely static quantity — drifts with frequency. `examples/test_microstrip.yaml`
swept over `frequency:`:

| f (Hz) | R (Ω/m) | L (H/m) | Z0 (Ω) | C (F/m) |
|--------|---------|---------|--------|---------|
| 1e4 | 9.46 | 5.75e-7 | **97.7** | **6.02e-11** |
| 1e6 | 9.56 | 5.72e-7 | 97.2 | 6.05e-11 |
| 1e7 | 12.4 | 5.07e-7 | 86.2 | 6.83e-11 |
| 1e8 | 18.3 | 4.65e-7 | 79.0 | 7.44e-11 |
| 1e10 | 61.0 | 4.53e-7 | **77.0** | **7.64e-11** |

C changes by 27 % and Z0 by 27 % for the same geometry. At 10 kHz the line has
R = 9.5 Ω/m against ωL = 0.036 Ω/m, so a real-valued `Z0 = √(L/C)` is not
defined at all — the printed 97.7 Ω is an artefact. The `check-z0` harness only
runs at 30 MHz for an 18 µm trace, where this is masked.

Fix: compute C once from a *static* source that does not depend on the
frequency-swept PEEC inductance. Do **not** obtain it by re-running the PEEC
fill at a very high frequency: finding 3 shows the same mesh is skin-depth
limited there, so an "L∞" from the volume mesh would be mesh-limited too. Two
consistent options are (a) take C from the Hammerstad-Jensen closed form the
code already implements (H-J gives Z0 and εeff, hence `C = √εeff/(c·Z0)`), or
(b) a separate PEC/surface-current solve for the external inductance. Then
report `Z0 = √((R + jωL)/(jωC))` as a complex number (or at least print |Z0|
and its phase and label the real-Z0 column as the lossless high-frequency
limit). Add a test asserting C is frequency-independent to within the mesh
tolerance.

## 3. [robustness] No skin-depth check: R is silently mesh-limited at high frequency

Weeks' method requires element cross-sections smaller than the skin depth
`δ = √(2/(ωμσ))` (0.66 µm in copper at 10 GHz, 2.1 µm at 1 GHz). Nothing in
`build.c`/`weeks.c` compares element size to δ, and no document in the repo
mentions skin depth. Same microstrip example, trace mesh only changed:

| f | trace mesh | R (Ω/m) |
|---|------------|---------|
| 1 GHz | `nw:21 nh:7 b:0.9` (shipped) | 36.0 |
| 1 GHz | `nw:41 nh:21 b:0.3` | 43.2 (+20 %) |
| 10 GHz | `nw:21 nh:7 b:0.9` (shipped) | 61.0 |
| 10 GHz | `nw:41 nh:21 b:0.3` | **116.7 (+91 %)** |

The shipped mesh under-predicts conductor loss by ~2× at 10 GHz and prints no
diagnostic. Caveat: the refined-mesh figures are not converged values — the
`b: 0.3` trace mesh has ~0.4 µm elements at up to 2.8 mm range (d/h ≈ 7·10³),
so they carry some of the cancellation error from finding 1. The conclusion
(shipped mesh is mesh-limited by ~2× at 10 GHz) stands; the exact refined
number should not be quoted. Add a warning in `build_elements()` (or after the fill) when the
smallest element dimension of any conductor exceeds ~δ/2, naming the conductor
and the ratio; optionally refuse when it exceeds ~2δ. Document the rule in
`YAML_USER_GUIDE.md` next to the mesh parameters.

## 4. [robustness] Geometry is never validated; overlapping / inverted stack-ups run silently

`parse_conductor()` checks each conductor's fields in isolation but nothing
checks the assembly. A trace placed *inside* the ground plane runs to
completion:

```yaml
- {w: 2800e-6, h: 2.0e-6, x: 0, y: 0, nw: 21, nh: 1, b: 1}
- {w: 150e-6,  h: 18e-6,  x: 1325e-6, y: 0.0, nw: 5, nh: 3, b: 1, er: 4.4, tan_delta: 0.02}
```

produces `substrate h=-2.00e-06 m`, then `eff_er = 1.0`, `a_d = 0`, and a
"microstrip" Z0 of 38 Ω — because `calc_eff_dielectric()` treats `h <= 0` as
"air" instead of an error. Overlapping traces likewise yield an (ill-conditioned
or singular) Z whose only symptom is a Meschach `E_SING` abort or nonsense
numbers.

Add an assembly validation pass after `getinput()`: every signal conductor must
satisfy `y > ground.y + ground.h`; no two conductor rectangles may overlap; and
signals whose x-extent lies outside the ground plane should warn (the return
path assumption is void). Reject with `ERROR` so the existing regression style
(`returncode > 0`, `ERROR` in stderr) applies.

## 5. [robustness] Unknown YAML keys are silently ignored, so typos change the mesh and material

`parse_conductor_value()` returns success for any unrecognised key ("Names and
unknown fields do not affect the calculation"). Combined with the defaults
`nw=10, nh=10, b=0.5, er=1.0`, a typo silently changes the model:

```yaml
- {w: 150e-6, h: 18e-6, x: 1325e-6, y: 202e-6, nW: 5, nh: 3, b: 1, epsr: 4.4, tan_delta: 0.02}
```

runs with `nw=10` and `εr=1.00` and prints nothing about `nW` or `epsr`.
Because `frequency` at the root is handled the same way (`freq:` would leave the
30 MHz default), the same applies there.

Warn on every unrecognised key (whitelist `name`, and keep the existing
`substrate_h` note), or make it an error the way malformed values already are.
The root mapping should get the same treatment.

## 6. [model] Dielectric is modelled per conductor, but physically it is one substrate

`er`/`tan_delta` live in every `conductor` struct. Consequences:

- The ground plane's `er` is parsed, validated and printed (`weeks.c:83`) but
  never used; every example nevertheless sets it, which suggests it matters.
- A user who sets `er` only on the ground plane (the natural reading of "the
  board is FR4") gets air for every trace with no diagnostic (see finding 5).
- Two traces on the same board can be given different `εr`, which has no
  physical meaning and silently gives inconsistent `eff_er`/`a_d` per line.

Promote the substrate to a top-level `substrate: {er, tan_delta}` mapping
(keeping the per-conductor keys as a deprecated alias for one release), store it
once, and drop the fields from `conductor`. This also removes the
`(void)cond;` parameter that `calcl()` carries only for the dielectric.

## 7. [model] Quasi-TEM section uses static, zero-thickness Hammerstad–Jensen

`calc_eff_dielectric()` implements the static H-J `εeff(w/h, εr)`; it ignores
trace thickness and frequency. Two effects that matter for the frequencies the
tool accepts:

- **Thickness**: the standard `w_eff = w + (t/π)·(1 + ln(2h/t))` correction is
  absent. For the 35 µm / 1.6 mm FR4 examples this is ~1 %, but for a 35 µm trace
  on a 100 µm prepreg it is several percent of Z0.
- **Dispersion**: εeff rises toward εr with frequency (Kirschning–Jansen or the
  Yamashita form). At 10 GHz on 1.6 mm FR4, static H-J underestimates εeff by
  roughly 10 %, i.e. β and the delay by ~5 %.

Neither is hard to add, and both should be noted in the output header until
they are. The `check-z0` harness (`tools/microstrip_z0/microstrip.py`) would
need the same corrections to stay an independent reference.

## 8. [perf] Full M×M inverse where N solves suffice; O(M²) transcendental fill

`examples/test_fr4.yaml` (M = 1043) takes 1.7 s wall — roughly 1 s in
`calcl()` and 0.7 s in `zm_inverse()`. Both scale badly and the input limits
(`nw ≤ 1000`, `nh ≤ 100`, 10 conductors) permit M ≈ 10⁶, i.e. 16 TB per
matrix — 32 TB for the two the current code holds — with no estimate or
refusal before `zm_get()` aborts.

- `weeks.c` computes the full inverse `Y = Z⁻¹` (LU + M triangular solves) but
  only uses block sums of N ≤ 9 column groups. Solving `Z·X = B` for N
  indicator columns (`zLUfactor` + N `zLUsolve`, both exported by Meschach) gives
  identical `y` at ~¼ the cost *of the inversion step* and halves peak memory
  (no second M×M result). On its own that is ~0.7 s → ~0.2 s here, i.e. ~30 %
  of wall time; the 4× only materialises once the fill is also sped up.
- `calcl()` evaluates `lp(&e[i], &e0)` inside the `i` loop although the same
  value is already in `lpj->ve[i]` (symmetry), and each `lp()` call does 16
  `F()` evaluations with three transcendental calls each. A far-field branch
  (finding 1) would also make the fill ~3–5× cheaper for the ground-plane
  block, which dominates M.
- Print the projected `2·M²·16` bytes and refuse (or require a flag) above a
  sane threshold before allocating.

## 9. [robustness] Hard-coded copper conductivity

`sigma = 58e6` in `calcl()` is the only material constant a user cannot set,
yet it is the one that varies most in practice (annealed vs ED foil, 5.8e7 vs
~4.7e7 S/m; aluminium; temperature). Since R ∝ 1/σ this is a direct ~20 %
uncertainty on every R and `a_c` value. Add an optional per-conductor `sigma`
(default 5.8e7) alongside the geometry keys; it is a two-line change in
`input.c` plus one in `calcl()`, and lets the FastHenry cross-check use the
same σ on both sides.

---

### Suggested order of work

1. Findings 4 and 5 (input validation) — small, isolated, immediately testable
   with the existing `tests/test_regressions.py` pattern.
2. Finding 1 (far-field `lp`) — needs a numerical test; must land before
   users are told to refine meshes, otherwise the convergence checks that
   finding 3 asks for will diverge.
3. Finding 3 (skin-depth warning) — small, prevents the most common misuse.
4. Finding 2 (static C, complex Z0) — changes output format; coordinate with
   `tools/microstrip_z0` and the regression tests that parse the TL table.
5. Findings 6, 7, 9 (input model) — YAML format changes; do together so the
   guide is updated once.
6. Finding 8 (solver) — only if larger meshes become a goal.
