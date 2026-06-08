# Quick Installation Guide
## WEEKS Microstrip Calculator with YAML Input

## 🚀 5-Minute Setup

### Step 1: Clone
```bash
git clone https://github.com/osaether/weeks.git
cd weeks
```

### Step 2: Check Dependencies
```bash
make check-deps
```

You should see:
```
Meschach: Found
libyaml: Found
```

### Step 3: Install Missing Dependencies (if needed)
```bash
# Ubuntu/Debian:
sudo apt-get install libmeschach-dev libyaml-dev

# Fedora/RHEL:
sudo dnf install meschach-devel libyaml-devel
```

### Step 4: Build
```bash
make
```

### Step 5: Run
```bash
./weeks
```

The program will read `test.yaml` by default (FR4 example).

Done! 🎉

---

## What You Get

**Input files in examples/ directory (YAML format)**:
- `test.yaml` - FR4 example (default)
- `test_air.yaml` - Air baseline
- `test_fr4.yaml` - FR4 standard PCB
- `test_rogers4003.yaml` - Rogers RO4003C
- `test_single.yaml` - Single trace (used by `make check-fasthenry`)

**To try different materials**:
```bash
make test-fr4     # FR4 substrate
make test-air     # Air (baseline)
make test-rogers  # Rogers material
```

The Makefile will copy the appropriate file from `examples/` to `test.yaml` and run the program.

---

## Quick YAML Format

Add these lines to each conductor in your YAML file:

```yaml
frequency: 30e6  # Operating frequency

conductors:
  - name: line0
    w: 2800e-6          # Width in METERS
    h: 2.0e-6           # Thickness in METERS
    x: 0.0              # X position
    y: 0.0              # Y position
    nw: 201             # Mesh divisions
    nh: 3
    b: 0.2
    er: 4.4             # Dielectric constant
    tan_delta: 0.02     # Loss tangent
  - name: line1         # Signal trace; its y sets the substrate height
    w: 150e-6
    h: 35e-6            # 35 µm = 1 oz copper
    x: 600e-6
    y: 1.602e-3         # 1.6 mm above the ground-plane top (= substrate height)
    nw: 21
    nh: 7
    b: 0.9
    er: 4.4
    tan_delta: 0.02
```

**IMPORTANT**: All dimensions must be in **METERS**!
- 1.6mm = 1.6e-3 ✅
- 1.6mm ≠ 1.6 ❌

The substrate **height** is not a parameter — it is the gap between the signal
trace and the ground plane, derived from the `y` coordinates.

---

## Common Materials

Material properties are `er` / `tan_delta`; the substrate height comes from the
trace's `y` (its height above the ground plane).

### FR4 Standard PCB (1.6 mm)
```yaml
er: 4.4
tan_delta: 0.02
# place the signal trace at y = ground_top + 1.6e-3
```

### Rogers RO4003C (RF, 0.813 mm)
```yaml
er: 3.38
tan_delta: 0.0027
# place the signal trace at y = ground_top + 0.813e-3
```

### Air (Baseline)
```yaml
er: 1.0
tan_delta: 0.0
```

---

## Troubleshooting

### "Cannot find yaml.h"
```bash
sudo apt-get install libyaml-dev
```

### "Undefined reference to yaml_parser_initialize"
```bash
sudo ldconfig  # Refresh library cache
```

### "Cannot find meschach.h"
```bash
sudo apt-get install libmeschach-dev
```

### Wrong results?
- Check all **geometry** dimensions are in METERS, not mm (`w`, `h`, `x`, `y`)
- Sanity-check the mesh (`nw`, `nh`, `b`) and compare against `examples/`
- Cross-check against FastHenry: `make check-fasthenry`
- Note: `er`/`tan_delta` do **not** change the R/L/|Z| matrices (those solve the
  series R and L, which are dielectric-independent), so air vs FR4 look identical
  there — expected, not a bug. The dielectric instead drives the separate
  TRANSMISSION-LINE PARAMETERS section (Z0, C, attenuation); cross-check it with
  `make check-z0`.

---

## Documentation

- **README.md** - Complete user guide and project overview
- **YAML_USER_GUIDE.md** - Detailed YAML input reference
- **docs/fasthenry-crosscheck.md** - FastHenry cross-check setup
- **docs/meschach-static-analysis.md** - Static-analysis report on the Meschach dependency
- See examples in the `examples/` directory

---

## Next Steps

1. ✅ **Validate**: Run `make check-fasthenry` to cross-check R/L against FastHenry
2. 🔧 **Customize**: Edit YAML files for your geometry
3. 📊 **Verify**: Cross-check with online calculators too
4. 🎯 **Use**: Apply to your PCB designs

---

**Need help?** Check README.md for detailed documentation on YAML format.

**Happy calculating!** 🎉
