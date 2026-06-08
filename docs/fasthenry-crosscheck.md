# FastHenry Cross-Check

Validates `weeks`' per-unit-length R/L matrices against
[FastHenry](https://www.fastfieldsolvers.com/), an independent 3-D field solver.

## Installing FastHenry

There is no apt package on Ubuntu 24.04; build from source:

```bash
git clone https://github.com/ediloren/FastHenry2.git
cd FastHenry2
# GCC 10+ (incl. GCC 14 on Ubuntu 24.04) needs -fcommon, or the link fails with
# "multiple definition of 'fp'/'timestuff'":
make fasthenry CFLAGS="-O -DFOUR -m64 -fcommon"
cp bin/fasthenry ~/.local/bin/      # anywhere on PATH; no sudo needed
fasthenry            # prints "Running FastHenry 3.0.1 ..."
```

## Running

```bash
make check-fasthenry                              # both bundled cases
python3 -m tools.fh_crosscheck examples/test_single.yaml   # one case
python3 -m tools.fh_crosscheck examples/test_fr4.yaml --tol 15 --l1 5e-3 --l2 10e-3
```

The report prints, per matrix entry, the `weeks` value, the FastHenry value, and the
signed % difference; entries beyond the tolerance are marked `*`. The comparison always
exits 0 (informational); a missing/failed FastHenry exits non-zero.

## How it works

FastHenry has no 2-D / per-unit-length mode. Each conductor is modelled as a straight bar
of length L along z; all far ends are shorted to the ground far end; one port is declared
per signal line between its near node and the ground near node. Per-unit-length impedance
is extracted by running two lengths and differencing,
`Zpul = (Z(L2) - Z(L1)) / (L2 - L1)`, which cancels the length-independent end effects.
Then `R = Re(Zpul)`, `L = Im(Zpul)/ω`.

## Mesh Alignment and Accuracy

- **Default Discrepancies (30–80%)**: When `b` is less than `1.0` (e.g. `0.2`), `weeks` uses a graded mesh that concentrates filaments at the edges of signal traces, whereas the cross-check harness tiles FastHenry conductors into equal-width sub-segments with `nwinc=1` (always uniform). This discretization mismatch, combined with spatial aliasing on coarse ground plane grids, leads to artificial variations.
- **High-Precision Agreement (≤2.3%)**: If `weeks` is configured with a uniform mesh (by setting `b: 1.0` in the YAML), both solvers use aligned uniform grids. In this case, the results for both resistance and inductance matrices match to within **2.3%** across all self and mutual terms.
- **Solver Configurations**: The cross-check harness automatically runs FastHenry using the direct LU solver with length refinement disabled (`-s ludecomp -a off`) to ensure fast and numerically exact results.

