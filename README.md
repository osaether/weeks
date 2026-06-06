# WEEKS Microstrip Calculator with Dielectric Support
## YAML Input Format Version

[![CI](https://github.com/osaether/weeks/actions/workflows/ci.yml/badge.svg)](https://github.com/osaether/weeks/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## About This Project

I created this project in the mid-90s and have uploaded it to GitHub in case someone finds it useful.

This code implements the partial inductance formulas developed by W.T. Weeks et al. at IBM Research in 1979. The original work was groundbreaking for calculating resistance and inductance in rectangular conductors, accounting for skin effect and proximity effect. My MWEEKS implementation built upon this foundation, and the recent 2025 enhancements add support for real-world PCB materials like FR4 and Rogers substrates.

While modern field solvers have become more sophisticated, this calculator remains valuable for quick impedance estimates and understanding the fundamental physics of microstrip transmission lines. It's particularly useful for educational purposes and preliminary PCB design work.

---

## Overview

This is an enhanced version of the WEEKS microstrip resistance calculator with full support for FR4 and general dielectric substrates.

## Features

✅ **YAML input format** - Modern, human-readable configuration files  
✅ **FR4 and dielectric substrate support**  
✅ **Effective dielectric constant calculation** (Hammerstad-Jensen)  
✅ **Dielectric loss modeling** (frequency-dependent tan δ)  
✅ **Linux-compatible** (no Windows dependencies)  
✅ **Pre-defined material constants** (FR4, Rogers, Alumina, PTFE)  
✅ **Frequency defined in input file** - No need to recompile!  
✅ **Example YAML files** for multiple materials  

## Quick Start

```bash
# Check dependencies
make check-deps

# Build
make

# Run with FR4 (default)
./weeks

# Or test with different materials
make test-fr4     # FR4 substrate
make test-air     # Air (baseline comparison)
make test-rogers  # Rogers RO4003C
```

## Requirements

- **GCC** or compatible C compiler
- **Meschach library** (matrix operations)
- **libyaml** (YAML parsing)
- Linux/Unix operating system

### Installing Dependencies

#### Ubuntu/Debian:
```bash
sudo apt-get install libmeschach-dev libyaml-dev
```

#### Fedora/RHEL:
```bash
sudo dnf install meschach-devel libyaml-devel
```

#### From Source (Meschach):
```bash
wget http://homepage.math.uiowa.edu/~dstewart/meschach/meschach.tar.gz
tar xzf meschach.tar.gz
cd meschach
make
sudo make install
```

#### From Source (libyaml):
```bash
git clone https://github.com/yaml/libyaml
cd libyaml
./bootstrap
./configure
make
sudo make install
```

## Input File Format (YAML)

The calculator uses YAML format for input files, making configuration human-readable and easy to edit.

### Basic Structure

```yaml
# Frequency of operation
frequency: 30e6  # 30 MHz (use scientific notation)

# List of conductors
conductors:
  - name: line0      # Ground plane
    w: 2800e-6       # Width in meters
    h: 2.0e-6        # Thickness in meters
    x: 0.0           # X position
    y: 0.0           # Y position
    nw: 201          # Width mesh divisions
    nh: 3            # Height mesh divisions
    b: 0.2           # Mesh density parameter
    er: 4.4          # Dielectric constant
    substrate_h: 1.6e-3    # Substrate height (METERS!)
    tan_delta: 0.02        # Loss tangent
    
  - name: line1      # Signal trace
    w: 150e-6
    h: 18e-6
    x: 600e-6
    y: 77e-6
    nw: 21
    nh: 7
    b: 0.9
    er: 4.4
    substrate_h: 1.6e-3
    tan_delta: 0.02
```

### Parameter Descriptions

**Frequency:**
- `frequency`: Operating frequency in Hz (use scientific notation: 30e6 = 30 MHz)

**Geometric Parameters:**
- `w`: Conductor width (meters)
- `h`: Conductor thickness/height (meters)  
- `x`: X-position of the left edge (min-x corner) (meters)
- `y`: Y-position of conductor bottom (meters)

**Mesh Parameters:**
- `nw`: Number of divisions along width
- `nh`: Number of divisions along height
- `b`: Mesh density parameter (0.2-0.9)

**Dielectric Parameters:**
- `er`: Relative permittivity (dielectric constant)
- `substrate_h`: Substrate height - distance to ground plane (METERS!)
- `tan_delta`: Loss tangent at operating frequency

**IMPORTANT**: All dimensions must be in **METERS**!
- 1.6 mm = **1.6e-3** meters (not 1.6!)
- 150 μm = **150e-6** meters

## Example Materials (YAML Format)

### FR4 Standard PCB
```yaml
frequency: 30e6

conductors:
  - name: line0
    # ... geometry parameters ...
    er: 4.4
    substrate_h: 1.6e-3
    tan_delta: 0.02
```

### Rogers RO4003C (RF/Microwave)
```yaml
frequency: 1e9  # 1 GHz for RF

conductors:
  - name: line0
    # ... geometry parameters ...
    er: 3.38
    substrate_h: 0.813e-3
    tan_delta: 0.0027
```

### Rogers RO4350B (High-Speed Digital)
```yaml
frequency: 2e9

conductors:
  - name: line0
    # ... geometry parameters ...
    er: 3.48
    substrate_h: 0.508e-3
    tan_delta: 0.0037
```

### Air (Baseline/Original Behavior)
```yaml
frequency: 30e6

conductors:
  - name: line0
    # ... geometry parameters ...
    er: 1.0
    substrate_h: 0.0
    tan_delta: 0.0
```

**Tip**: Copy one of the example files from `examples/` directory and modify it for your needs!

## Compilation

### Simple (Recommended)
```bash
make
```

This will:
- Check for required libraries (libyaml, meschach)
- Create the `build/` directory
- Compile all source files from `src/` (lowercase `.c` files)
- Link with Meschach and libyaml libraries
- Create the `weeks` executable in the root directory

### Check Dependencies First
```bash
make check-deps
```

This will verify that both Meschach and libyaml are installed.

### Custom Library Paths
```bash
make INCLUDES='-Iinclude -I/custom/path/include' LDFLAGS='-L/custom/path/lib'
```

### Manual Compilation
```bash
mkdir -p build
gcc -o weeks \
    src/weeks.c src/build.c src/calcl.c src/input.c src/lpp.c \
    -Iinclude -I/usr/local/include \
    -L/usr/local/lib \
    -lmeschach -lyaml -lm -O2
```

### Troubleshooting

**"Cannot find yaml.h"**:
```bash
sudo apt-get install libyaml-dev
```

**"Undefined reference to yaml_parser_initialize"**:
```bash
# Make sure libyaml is installed and linked
sudo ldconfig
```

## Output

The program calculates and displays:

1. **Resistance Matrix (R)** in Ω/m
2. **Inductance Matrix (L)** in H/m  
3. **Impedance Magnitude |Z|** at operating frequency

### Example Output:
```
========================================
RESULTS
========================================

FREQUENCY: 3.000000e+07 Hz (30.00 MHz)

*** RESISTANCE MATRIX (Ohm/m) ***

           1           2           3

  1 +1.2345e-02 +2.3456e-03 +1.2345e-03
  2 +2.3456e-03 +1.2345e-02 +2.3456e-03
  3 +1.2345e-03 +2.3456e-03 +1.2345e-02

*** INDUCTANCE MATRIX (H/m) ***

           1           2           3

  1 +4.5678e-07 +1.2345e-07 +5.6789e-08
  2 +1.2345e-07 +4.5678e-07 +1.2345e-07
  3 +5.6789e-08 +1.2345e-07 +4.5678e-07

*** IMPEDANCE MAGNITUDE (Ohm) at 30.00 MHz ***
...
```

## Understanding the Physics

### Effective Dielectric Constant
For microstrip, the EM field exists partly in the dielectric and partly in air. The effective dielectric constant εeff is calculated using:

```
εeff = (εr + 1)/2 + ((εr - 1)/2) × F(w/h)
```

where F(w/h) is the Hammerstad-Jensen approximation.

### Dielectric Loss
Dielectric loss contributes additional resistance:

```
R_dielectric = (ω√εeff/c) × ((εr-1)/(εeff-1)) × (εeff/εr) × tan(δ)
```

This is frequency-dependent and becomes more significant at higher frequencies.

### What Changes with Dielectric?

| Parameter | Air (εr=1.0) | FR4 (εr=4.4) | Effect |
|-----------|-------------|--------------|--------|
| Capacitance | 1× | ~2.1× | Increases by √εeff |
| Inductance | 1× | ~1× | Approximately same |
| Z0 | 1× | ~0.5× | Decreases by √εeff |
| Loss | Conductor only | Conductor + Dielectric | Increases |
| Velocity | c | ~0.5c | Slows down |

## Directory Structure

```
weeks_lowercase/
├── README.md              # This file
├── INSTALL.md             # Quick start guide
├── LICENSE                # MIT license
├── Makefile               # Build script
│
├── src/                   # Source files (5 files, lowercase .c)
│   ├── weeks.c            # Main program (with YAML support)
│   ├── calcl.c            # Calculator with dielectric
│   ├── input.c            # YAML parser using libyaml
│   ├── build.c            # Element builder
│   └── lpp.c              # Partial inductance formulas
│                          # (complex solvers provided by libmeschach)
│
├── include/               # Header files (3 files, lowercase .h)
│   ├── weeks.h            # Main header with dielectric support
│   ├── calcl.h            # Calculator header
│   └── lpp.h              # Partial inductance header
│
├── examples/              # YAML input examples (4 files)
│   ├── test.yaml          # Default (FR4)
│   ├── test_air.yaml      # Air baseline
│   ├── test_fr4.yaml      # FR4 standard PCB
│   └── test_rogers4003.yaml  # Rogers RO4003C
│
├── docs/                  # Additional documentation
│   └── fasthenry-crosscheck.md  # FastHenry cross-check setup
│
└── build/                 # Build artifacts (auto-created by make)
    └── *.o                # Object files
```

## Validation

To validate results:

1. **Compare against FastHenry**: Run `make check-fasthenry` for independent numerical validation of R/L values.
2. **Mesh Alignment & Accuracy**: When both solvers use uniform meshes (by setting `b: 1.0` in `weeks` to match FastHenry's uniform sub-segmentation in the harness), they match to within **2.3%** across all self and mutual resistance/inductance terms. See [diagnostic_report.md](diagnostic_report.md) and [docs/fasthenry-crosscheck.md](docs/fasthenry-crosscheck.md) for details.
3. **Online calculators**: Cross-check with analytical formulas.

## Troubleshooting

### "Cannot find meschach.h"
```bash
# Find where it's installed
find /usr -name "meschach.h" 2>/dev/null

# Then compile with:
make INCLUDES='-I/path/to/meschach/include'
```

### "Undefined reference to zm_get"
```bash
# Meschach library not linked properly
make LDFLAGS='-L/path/to/meschach/lib'
```

### Wrong Results
- **Check units**: substrate_h must be in METERS!
- **Check dielectric values**: Typical FR4 is εr=4.4, not 44!
- **Compare with air**: Run with er=1.0 to verify baseline

## Technical Details

### Algorithm
- **Method**: Partial Element Equivalent Circuit (PEEC)
- **Formulation**: Weeks method (IBM, 1979)
- **Frequency**: Quasi-static (valid up to ~1 GHz)
- **Matrix**: Complex impedance Z = R + jωL

### Modifications from Original MWEEKS
1. Added dielectric structure members to `conductor`
2. Modified `src/input.c` to parse dielectric parameters
3. Modified `src/calcl.c` to calculate effective εr and dielectric loss
4. Modified `src/weeks.c` to pass conductor info to calcl
5. Removed Windows-specific `_CRT` debug code (Linux compatibility)
6. Added material constant definitions in header

### Backward Compatibility
- Omitting dielectric parameters defaults to air (εr=1.0)
- Original input files work without modification
- Results match original code when dielectric params are omitted

## References

1. **Original Weeks Paper**:  
   W.T. Weeks et al., "Resistive and Inductive Skin Effect in Rectangular Conductors"  
   IBM J. RES. DEVELOP., Vol 23, No. 6, Nov. 1979

2. **Hammerstad-Jensen**:  
   E. Hammerstad & O. Jensen, "Accurate Models for Microstrip Computer-Aided Design"  
   IEEE MTT-S, 1980

3. **Material Properties**:  
   - IPC-4101 Specification for Base Materials
   - Rogers Corporation Datasheets
   - Standard PCB manufacturer references

## License

Changed to MIT license after uploading to github

## Credits

- **Original WEEKS code**: Ole Saether (1995)
- **Weeks formulas**: W.T. Weeks et al., IBM (1979)
- **Dielectric modifications**: 2025 enhancement
- **MWEEKS version**: Enhanced implementation with built-in matrix operations

## Support

For issues or questions:
1. Check this README
2. Verify Meschach installation
3. Compare with provided examples
4. Validate with external tools (FastHenry, online calculators)

