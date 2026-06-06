# Quick Installation Guide
## WEEKS Microstrip Calculator with YAML Input

## 🚀 5-Minute Setup

### Step 1: Extract
```bash
unzip weeks_yaml.zip
cd weeks_yaml
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
    substrate_h: 1.6e-3 # Height in METERS (1.6mm)
    tan_delta: 0.02     # Loss tangent
```

**IMPORTANT**: All dimensions must be in **METERS**!
- 1.6mm = 1.6e-3 ✅
- 1.6mm ≠ 1.6 ❌

---

## Common Materials

### FR4 Standard PCB
```yaml
er: 4.4
substrate_h: 1.6e-3
tan_delta: 0.02
```

### Rogers RO4003C (RF)
```yaml
er: 3.38
substrate_h: 0.813e-3
tan_delta: 0.0027
```

### Air (Baseline)
```yaml
er: 1.0
substrate_h: 0.0
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
- Check substrate_h is in METERS (not mm!)
- Verify εr looks reasonable (FR4 ≈ 4.4)
- Test with air first (er=1.0)
- Compare examples in `examples/` directory

---

## Documentation

- **README.md** - Complete user guide with YAML format details
- See examples in `examples/` directory

---

## Next Steps

1. ✅ **Validate**: Compare air vs FR4 results
2. 🔧 **Customize**: Edit YAML files for your geometry
3. 📊 **Verify**: Cross-check with FastHenry or online calculators
4. 🎯 **Use**: Apply to your PCB designs

---

**Need help?** Check README.md for detailed documentation on YAML format.

**Happy calculating!** 🎉
