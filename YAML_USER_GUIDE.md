# YAML Input Format - Complete User Guide
## WEEKS Microstrip Calculator

---

## Table of Contents

1. [Introduction](#introduction)
2. [Basic Structure](#basic-structure)
3. [Global Parameters](#global-parameters)
4. [Conductor Parameters](#conductor-parameters)
5. [Complete Examples](#complete-examples)
6. [Parameter Reference](#parameter-reference)
7. [Material Library](#material-library)
8. [Common Scenarios](#common-scenarios)
9. [Tips & Best Practices](#tips--best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

The YAML input format makes it easy to define microstrip configurations for the WEEKS calculator. YAML (YAML Ain't Markup Language) is human-readable and widely used in modern software.

### Why YAML?

✅ **Human-readable** - Easy to write and understand  
✅ **Comments supported** - Document your configurations  
✅ **Hierarchical** - Clear structure for complex setups  
✅ **Standard format** - Many tools can read/write YAML  
✅ **Frequency in file** - No need to recompile to change frequency!  

---

## Basic Structure

Every YAML input file has two main sections:

```yaml
# Section 1: Global settings
frequency: 30e6

# Section 2: List of conductors
conductors:
  - name: conductor1
    # ... parameters ...
    
  - name: conductor2
    # ... parameters ...
```

### YAML Syntax Rules

**Indentation:**
- Use **spaces** (2 or 4), NOT tabs
- Consistent indentation required

**Colons:**
- Space required after colon: `frequency: 30e6` ✅
- No space is wrong: `frequency:30e6` ❌

**Lists:**
- List items start with dash: `- name: line0`
- Items must be indented under the list name

**Comments:**
- Start with `#` symbol
- Can be on their own line or at end of line

---

## Global Parameters

### Frequency

Defines the operating frequency for all calculations.

```yaml
frequency: 30e6  # 30 MHz
```

**Format:** Scientific notation or decimal
**Units:** Hertz (Hz)

**Examples:**
```yaml
frequency: 1e9       # 1 GHz
frequency: 2.4e9     # 2.4 GHz (WiFi)
frequency: 30e6      # 30 MHz
frequency: 100e6     # 100 MHz
frequency: 5.8e9     # 5.8 GHz
```

**Common Frequencies:**
- **30 MHz** - Low frequency PCB
- **100 MHz** - Digital circuits
- **1 GHz** - RF circuits
- **2.4 GHz** - WiFi, Bluetooth
- **5.8 GHz** - High-speed RF

---

## Conductor Parameters

Each conductor in the `conductors:` list requires these parameters:

### Required Geometric Parameters

#### width (w)
Conductor width

```yaml
w: 150e-6  # 150 micrometers = 0.15 mm
```

**Units:** Meters  
**Typical values:** 50e-6 to 5e-3 (50μm to 5mm)

#### thickness (h)
Conductor thickness (vertical dimension)

```yaml
h: 18e-6  # 18 micrometers (standard copper foil)
```

**Units:** Meters  
**Typical values:**
- 18e-6 (0.5 oz copper)
- 35e-6 (1 oz copper)
- 70e-6 (2 oz copper)

#### x-position (x)
Horizontal position of conductor left edge (min-x corner)

```yaml
x: 600e-6  # 600 micrometers from origin
```

**Units:** Meters  
**Reference:** x=0 is arbitrary origin

#### y-position (y)
Vertical position of conductor bottom edge

```yaml
y: 0.0        # Ground plane at y=0
y: 1.602e-3   # Signal trace 1.6mm above a 2μm ground plane
```

**Units:** Meters  
**Reference:** y=0 typically at ground plane

**Important:** for a signal trace, its height above the ground-plane top *is* the
substrate height used for the effective permittivity / Z0 (there is no separate
`substrate_h` input). Place the trace at `y = ground_top + substrate_thickness`.

---

### Required Mesh Parameters

#### width divisions (nw)
Number of mesh divisions along width

```yaml
nw: 21  # Divide width into 21 segments
```

**Typical values:**
- Ground plane: 50-201 (more = better but slower)
- Signal traces: 11-21 (adequate for most cases)

**Rule of thumb:**
- Wider conductors need more divisions
- Start with ~20 and increase if results unstable

#### thickness divisions (nh)
Number of mesh divisions along thickness

```yaml
nh: 7  # Divide thickness into 7 segments
```

**Typical values:**
- Ground plane: 3-5 (thin, doesn't need many)
- Signal traces: 5-9 (more for thick conductors)

**Rule of thumb:**
- Thicker conductors need more divisions
- Minimum: 3
- Typical: 5-7

#### mesh density (b)
Mesh density parameter (controls element sizing)

```yaml
b: 0.2   # Ground plane (less dense)
b: 0.9   # Signal trace (more dense)
```

**Range:** 0.1 to 0.9  
**Typical values:**
- 0.2 - Ground planes (large, uniform)
- 0.5 - Medium density
- 0.9 - Signal traces (needs fine detail)

---

### Optional Dielectric Parameters

> **`er` and `tan_delta` are optional material properties** (default air:
> `er=1.0`, `tan_delta=0.0`). They do **not** change the series R/L/|Z| matrices
> (those are dielectric-independent), but they **do** drive the separate per-line
> TRANSMISSION-LINE PARAMETERS section (effective permittivity, Z0, capacitance,
> attenuation, propagation γ).
>
> There is **no `substrate_h` parameter.** The substrate height is the trace-to-
> ground gap, derived from geometry (a signal trace's `y` minus the ground
> plane's top). A legacy `substrate_h:` key is ignored with a note on stderr.

#### dielectric constant (er)
Relative permittivity of substrate

```yaml
er: 4.4  # FR4 standard value
```

**Units:** Dimensionless  
**Common values:**
- 1.0 - Air (no substrate)
- 2.1 - PTFE (Teflon)
- 3.38 - Rogers RO4003C
- 4.4 - FR4 (standard PCB)
- 9.8 - Alumina ceramic

#### substrate height (derived from geometry — not an input)

There is no `substrate_h` field. The substrate height is the gap between the
signal trace and the ground plane, set by the trace's `y` position:

```yaml
# ground plane: y=0, thickness h=2e-6  -> top at 2e-6
# signal trace on a 1.6mm substrate:
y: 1.602e-3   # 2e-6 (ground top) + 1.6e-3 (substrate) = trace bottom
```

**Common substrate thicknesses to add above the ground-plane top (METERS!):**
- 0.508e-3 - 20 mil
- 0.813e-3 - 32 mil (Rogers standard)
- 1.6e-3 - 1.6mm (standard FR4)
- 3.2e-3 - 3.2mm (thick PCB)

**⚠️ CRITICAL:** Must be in METERS! `1.6mm = 1.6e-3`, not `1.6`.

#### loss tangent (tan_delta)
Dielectric loss at operating frequency

```yaml
tan_delta: 0.02  # FR4 at 1 GHz
```

**Units:** Dimensionless  
**Common values:**
- 0.0 - Air (no loss)
- 0.0002 - PTFE (very low loss)
- 0.0027 - Rogers RO4003C
- 0.02 - FR4 at 1 GHz
- 0.04 - Poor quality FR4

**Note:** Loss tangent increases with frequency!

---

### Optional Parameter

#### name
Conductor identifier (for reference only)

```yaml
name: line0       # Ground plane
name: signal1     # First signal trace
name: power_rail  # Power distribution
```

**Not used in calculations** - just for documentation

---

## Complete Examples

### Example 1: Single Microstrip on FR4

Simple single trace over ground plane on standard FR4.

```yaml
# Single microstrip line on FR4
# Frequency: 100 MHz
# Board: 1.6mm FR4

frequency: 100e6

conductors:
  # Ground plane
  - name: ground
    w: 5000e-6      # 5mm wide ground
    h: 35e-6        # 1oz copper (35μm)
    x: 0.0
    y: 0.0          # Ground at y=0
    nw: 101         # Fine mesh for ground
    nh: 3
    b: 0.2
    er: 4.4         # FR4
    tan_delta: 0.02
    
  # Signal trace
  - name: signal
    w: 200e-6       # 200μm wide trace
    h: 35e-6        # 1oz copper
    x: 2500e-6      # Centered over ground
    y: 1.6e-3       # On top of substrate
    nw: 21
    nh: 7
    b: 0.9
    er: 4.4
    tan_delta: 0.02
```

---

### Example 2: Three Coupled Microstrips

Three parallel traces with coupling effects.

```yaml
# Three coupled microstrip traces
# Differential pair + clock signal
# Rogers RO4003C for RF

frequency: 2.4e9  # 2.4 GHz WiFi

conductors:
  # Ground plane
  - name: ground
    w: 10000e-6     # 10mm ground
    h: 18e-6        # Thin copper
    x: 0.0
    y: 0.0
    nw: 201
    nh: 3
    b: 0.2
    er: 3.38        # Rogers RO4003C
    tan_delta: 0.0027
    
  # Differential pair - trace 1
  - name: diff_p
    w: 100e-6       # 100μm
    h: 18e-6
    x: 4500e-6      # Left side
    y: 0.813e-3
    nw: 21
    nh: 7
    b: 0.9
    er: 3.38
    tan_delta: 0.0027
    
  # Differential pair - trace 2
  - name: diff_n
    w: 100e-6
    h: 18e-6
    x: 4700e-6      # 200μm spacing
    y: 0.813e-3
    nw: 21
    nh: 7
    b: 0.9
    er: 3.38
    tan_delta: 0.0027
    
  # Clock signal
  - name: clock
    w: 150e-6       # Wider for lower impedance
    h: 18e-6
    x: 5500e-6      # Separated from diff pair
    y: 0.813e-3
    nw: 21
    nh: 7
    b: 0.9
    er: 3.38
    tan_delta: 0.0027
```

---

### Example 3: Air Dielectric (Baseline)

No substrate - conductors in free space.

```yaml
# Wire-in-air configuration
# Used for baseline comparison
# No dielectric loss

frequency: 30e6

conductors:
  # Reference conductor
  - name: reference
    w: 1000e-6
    h: 50e-6
    x: 0.0
    y: 0.0
    nw: 51
    nh: 5
    b: 0.5
    er: 1.0         # Air
    tan_delta: 0.0  # No loss
    
  # Signal conductor
  - name: signal
    w: 500e-6
    h: 50e-6
    x: 2000e-6
    y: 500e-6       # Elevated above reference
    nw: 31
    nh: 5
    b: 0.7
    er: 1.0
    tan_delta: 0.0
```

---

### Example 4: High-Frequency RF (5.8 GHz)

Low-loss material for high-frequency applications.

```yaml
# 5.8 GHz RF microstrip
# Ultra-low loss PTFE substrate
# Typical for radar, satellite

frequency: 5.8e9

conductors:
  - name: ground
    w: 3000e-6
    h: 17e-6
    x: 0.0
    y: 0.0
    nw: 151
    nh: 3
    b: 0.2
    er: 2.1         # PTFE (Teflon)
    tan_delta: 0.0002  # Ultra-low loss
    
  - name: rf_line
    w: 75e-6        # Narrow for 50Ω
    h: 17e-6
    x: 1500e-6
    y: 0.508e-3
    nw: 15
    nh: 5
    b: 0.9
    er: 2.1
    tan_delta: 0.0002
```

---

## Parameter Reference

### Quick Reference Table

| Parameter | Symbol | Units | Typical Range | Example |
|-----------|--------|-------|---------------|---------|
| **Global** |
| Frequency | - | Hz | 1e6 to 10e9 | `frequency: 1e9` |
| **Geometry** |
| Width | w | meters | 50e-6 to 5e-3 | `w: 150e-6` |
| Thickness | h | meters | 17e-6 to 70e-6 | `h: 35e-6` |
| X-position | x | meters | Any | `x: 600e-6` |
| Y-position | y | meters | Any | `y: 1.6e-3` |
| **Mesh** |
| Width divisions | nw | count | 11 to 201 | `nw: 21` |
| Height divisions | nh | count | 3 to 9 | `nh: 7` |
| Mesh density | b | ratio | 0.1 to 0.9 | `b: 0.9` |
| **Dielectric** |
| Permittivity | er | - | 1.0 to 10.0 | `er: 4.4` |
| Substrate height | *(from geometry)* | meters | set via trace `y` | `y: 1.602e-3` |
| Loss tangent | tan_delta | - | 0.0 to 0.05 | `tan_delta: 0.02` |

---

## Material Library

### Common PCB Materials

Each material is defined by `er` and `tan_delta`. The substrate thickness in the
comments is the gap to set via the trace's `y` (height above the ground plane),
not a `substrate_h` field.

#### FR4 (Standard PCB)
```yaml
er: 4.4
tan_delta: 0.02          # At 1 GHz
# substrate thickness 1.6mm  -> trace y = ground_top + 1.6e-3
```

**Use cases:** General purpose PCBs, consumer electronics  
**Frequency range:** DC to 1 GHz  
**Cost:** Low  

#### Rogers RO4003C (RF Material)
```yaml
er: 3.38
tan_delta: 0.0027        # Low loss
# substrate thickness 0.813mm (32 mil)  -> trace y = ground_top + 0.813e-3
```

**Use cases:** RF, microwave, high-speed digital  
**Frequency range:** Up to 10 GHz  
**Cost:** Medium  

#### Rogers RO4350B (High-Speed Digital)
```yaml
er: 3.48
tan_delta: 0.0037
# substrate thickness 0.508mm (20 mil)  -> trace y = ground_top + 0.508e-3
```

**Use cases:** High-speed digital, RF  
**Frequency range:** Up to 10 GHz  
**Cost:** Medium  

#### PTFE / Teflon (Ultra-Low Loss)
```yaml
er: 2.1
tan_delta: 0.0002        # Very low loss
# substrate thickness 0.508mm  -> trace y = ground_top + 0.508e-3
```

**Use cases:** Microwave, satellite, radar  
**Frequency range:** Up to 40 GHz  
**Cost:** High  

#### Alumina (Ceramic)
```yaml
er: 9.8
tan_delta: 0.001
# substrate thickness 0.635mm (25 mil)  -> trace y = ground_top + 0.635e-3
```

**Use cases:** Hybrid circuits, high power  
**Frequency range:** DC to 20 GHz  
**Cost:** High  

---

### Standard Board Thicknesses

| Thickness | Mils | Meters | Common Use |
|-----------|------|--------|------------|
| 0.4mm | 16 | 0.4e-3 | Thin flex PCB |
| 0.508mm | 20 | 0.508e-3 | RF boards |
| 0.8mm | 31 | 0.8e-3 | Compact PCB |
| 0.813mm | 32 | 0.813e-3 | Rogers standard |
| 1.6mm | 63 | 1.6e-3 | Standard PCB |
| 2.4mm | 94 | 2.4e-3 | Thick PCB |
| 3.2mm | 126 | 3.2e-3 | Power electronics |

---

### Copper Thicknesses

| Weight | Thickness | Meters | Use |
|--------|-----------|--------|-----|
| 0.5 oz | 17μm | 17e-6 | Light traces |
| 1 oz | 35μm | 35e-6 | Standard |
| 2 oz | 70μm | 70e-6 | High current |
| 3 oz | 105μm | 105e-6 | Power planes |

---

## Common Scenarios

### Scenario 1: 50Ω Microstrip Design

You want a 50Ω trace on 1.6mm FR4 at 1 GHz.

**Calculator result:** w ≈ 3mm for 50Ω

```yaml
frequency: 1e9

conductors:
  - name: ground
    w: 20000e-6
    h: 35e-6
    x: 0.0
    y: 0.0
    nw: 201
    nh: 3
    b: 0.2
    er: 4.4
    tan_delta: 0.02
    
  - name: fifty_ohm_line
    w: 3000e-6      # 3mm for ~50Ω
    h: 35e-6
    x: 10000e-6
    y: 1.6e-3
    nw: 31
    nh: 7
    b: 0.9
    er: 4.4
    tan_delta: 0.02
```

---

### Scenario 2: Differential Pair

100Ω differential impedance, tight coupling.

```yaml
frequency: 2.5e9  # High-speed digital

conductors:
  - name: ground
    w: 10000e-6
    h: 35e-6
    x: 0.0
    y: 0.0
    nw: 201
    nh: 3
    b: 0.2
    er: 3.48       # Rogers RO4350B
    tan_delta: 0.0037
    
  # Positive trace
  - name: diff_p
    w: 120e-6
    h: 35e-6
    x: 4800e-6
    y: 0.508e-3
    nw: 21
    nh: 7
    b: 0.9
    er: 3.48
    tan_delta: 0.0037
    
  # Negative trace (100μm spacing for tight coupling)
  - name: diff_n
    w: 120e-6
    h: 35e-6
    x: 5020e-6     # 100μm edge-to-edge
    y: 0.508e-3
    nw: 21
    nh: 7
    b: 0.9
    er: 3.48
    tan_delta: 0.0037
```

---

### Scenario 3: Comparing Materials

Same geometry, different substrates.

```yaml
# This is for FR4 - save as test_fr4.yaml
frequency: 1e9

conductors:
  - name: ground
    w: 5000e-6
    h: 35e-6
    x: 0.0
    y: 0.0
    nw: 101
    nh: 3
    b: 0.2
    er: 4.4         # FR4
    tan_delta: 0.02
    
  - name: signal
    w: 200e-6
    h: 35e-6
    x: 2500e-6
    y: 1.6e-3
    nw: 21
    nh: 7
    b: 0.9
    er: 4.4         # FR4
    tan_delta: 0.02
```

Then change ONLY dielectric parameters for Rogers:
```yaml
    er: 3.38         # Rogers RO4003C
    tan_delta: 0.0027
```

Run both and compare impedance!

---

## Tips & Best Practices

### Units Conversion Cheat Sheet

**Always use METERS in YAML!**

| You Have | Convert To | Example |
|----------|------------|---------|
| 1.6 mm | 1.6e-3 | `y: 1.602e-3` |
| 150 μm | 150e-6 | `w: 150e-6` |
| 0.813 mm | 0.813e-3 | `y: 0.815e-3` |
| 35 μm | 35e-6 | `h: 35e-6` |
| 3 mm | 3e-3 | `w: 3e-3` |

**Quick conversion:**
- mm → multiply by 1e-3
- μm → multiply by 1e-6
- mil → multiply by 25.4e-6

---

### Mesh Density Guidelines

**Ground plane:**
```yaml
nw: 101-201    # More is better but slower
nh: 3-5        # Usually thin
b: 0.2-0.3     # Lower density OK
```

**Signal traces:**
```yaml
nw: 11-31      # Depends on width
nh: 5-9        # Depends on thickness
b: 0.7-0.9     # Higher density for accuracy
```

**Rule:** Start conservative, increase nw/nh if results change significantly.

---

### Frequency Selection

**Choose frequency based on application:**

```yaml
# Low-speed digital, audio
frequency: 10e6    # 10 MHz

# General digital (microcontrollers)
frequency: 100e6   # 100 MHz

# High-speed digital, DDR
frequency: 1e9     # 1 GHz

# RF, WiFi
frequency: 2.4e9   # 2.4 GHz

# Microwave
frequency: 10e9    # 10 GHz
```

**Tip:** Use the highest frequency your circuit will see!

---

### Dielectric Constant Notes

**Temperature dependence:**
- FR4 εr changes ±10% with temperature
- Rogers materials more stable

**Frequency dependence:**
- FR4: εr decreases slightly with frequency
- Use datasheet value at your frequency

**Moisture:**
- FR4 absorbs moisture (εr increases)
- Rogers materials unaffected

---

### Comments Best Practices

Use comments to document your design:

```yaml
# Project: WiFi Antenna Feed
# Designer: John Smith
# Date: 2025-02-08
# Board: Rogers RO4003C, 32 mil

frequency: 2.4e9  # 2.4 GHz WiFi band

conductors:
  # 50Ω ground plane (copper pour)
  - name: ground
    w: 50000e-6   # 50mm wide (full board width)
    h: 35e-6      # 1oz copper
    # ... rest ...
    
  # Microstrip feed line to antenna
  # Target: 50Ω, length: 25mm
  - name: antenna_feed
    w: 1800e-6    # Calculated for 50Ω
    # ... rest ...
```

---

### Validation Checklist

Before running, verify:

```yaml
✅ Frequency is in Hz (not MHz!)
   frequency: 1e9  ✅
   frequency: 1000 ❌

✅ All dimensions in meters
   w: 150e-6  ✅
   w: 0.15    ❌  (this is 0.15 m = 150 mm!)

✅ Trace height (sets the substrate height) reasonable
   y: 1.602e-3    ✅ (1.6mm above ground)
   y: 1.6         ❌ (1.6 m = 1600 mm!)

✅ Spacing indented correctly (use spaces)

✅ Colons have spaces after them
   frequency: 30e6  ✅
   frequency:30e6   ❌

✅ All conductors have required parameters
```

---

## Troubleshooting

### Common YAML Errors

#### Error: "YAML parse error at line X"

**Cause:** Syntax error

**Check:**
1. Indentation uses spaces, not tabs
2. Spaces after colons
3. List items properly indented
4. No typos in parameter names

**Example of WRONG:**
```yaml
frequency:30e6              # Missing space after colon
conductors:
- name: ground              # Not indented
	w: 1000e-6              # Using tab character
```

**CORRECT:**
```yaml
frequency: 30e6
conductors:
  - name: ground
    w: 1000e-6
```

---

#### Error: "Failed to initialize YAML parser"

**Cause:** libyaml not installed

**Solution:**
```bash
sudo apt-get install libyaml-dev
make clean
make
```

---

### Common Parameter Errors

#### Wildly Wrong Results

**Check dimensions!**

```yaml
# WRONG - dimensions in mm instead of meters
y: 1.6      # This is 1.6 METERS = 1600mm above ground!

# CORRECT
y: 1.602e-3   # 1.6mm above the ground plane
```

---

#### Negative Inductance

**Cause:** Usually mesh too coarse or geometry error

**Solution:**
1. Increase nw and nh
2. Check conductor positions (y-values reasonable?)
3. Verify trace heights (`y` above the ground plane) make sense

---

#### Very High Resistance

**Check:**
1. Frequency too high?
2. Conductors too thin?
3. Dielectric loss too high?

---

### Validation Tools

**Check your YAML syntax:**
```bash
# Python
python3 -c "import yaml; yaml.safe_load(open('test.yaml'))"

# Online
# yamllint.com
# codebeautify.org/yaml-validator
```

**Visual check:**
```bash
cat test.yaml
# Make sure structure looks right
```

---

## Advanced Topics

### Copying Parameters

YAML doesn't have variable substitution, but you can use comments as templates:

```yaml
# Template for signal traces on this board:
# er: 4.4
# tan_delta: 0.02
# h: 35e-6
# y: 1.602e-3   # 1.6mm above ground (sets the substrate height)

frequency: 1e9

conductors:
  - name: trace1
    w: 200e-6
    h: 35e-6       # Copy from template
    x: 1000e-6
    y: 1.6e-3
    nw: 21
    nh: 7
    b: 0.9
    er: 4.4        # Copy from template
    tan_delta: 0.02
    
  # ... more traces with same dielectric
```

---

### Parametric Studies

Create multiple files to study parameter effects. To sweep substrate height,
vary the signal trace's `y` (its height above the ground-plane top):

```bash
# test_1mm.yaml   -> signal trace at
y: 1.002e-3

# test_1.6mm.yaml -> signal trace at
y: 1.602e-3

# test_2.4mm.yaml -> signal trace at
y: 2.402e-3
```

Then run all:
```bash
for f in test_*.yaml; do
    cp $f test.yaml
    ./weeks > results_$(basename $f .yaml).txt
done
```

---

### Precision

YAML supports full floating-point precision:

```yaml
# Standard notation
frequency: 2400000000

# Scientific notation (preferred)
frequency: 2.4e9

# High precision
frequency: 2.412e9

# Very precise dimensions
w: 123.456e-6
```

---

## Summary

### Quick Checklist for Creating YAML Files

1. ✅ Start with `frequency:` in Hz
2. ✅ Add `conductors:` list
3. ✅ Each conductor starts with `- name:`
4. ✅ Include all required parameters (w, h, x, y, nw, nh, b; optional er, tan_delta)
5. ✅ Use METERS for all dimensions
6. ✅ Use spaces for indentation (not tabs)
7. ✅ Add comments to document your design
8. ✅ Validate YAML syntax before running
9. ✅ Check results make sense

---

### Example Template

Copy this template to start your own design:

```yaml
# Project: [Your project name]
# Date: [Date]
# Board: [Material type and thickness]

frequency: 1e9  # [Your frequency]

conductors:
  # Ground plane
  - name: ground
    w: 10000e-6
    h: 35e-6
    x: 0.0
    y: 0.0
    nw: 101
    nh: 3
    b: 0.2
    er: 4.4
    tan_delta: 0.02
    
  # Signal trace
  - name: signal
    w: 200e-6
    h: 35e-6
    x: 5000e-6
    y: 1.6e-3
    nw: 21
    nh: 7
    b: 0.9
    er: 4.4
    tan_delta: 0.02
```

---

## Further Reading

**In this package:**
- `README.md` - Complete documentation
- `examples/` - Working examples
- `YAML_MIGRATION_GUIDE.md` - Migration details

**External resources:**
- YAML specification: yaml.org
- PCB material datasheets from manufacturers
- Microstrip impedance calculators for comparison

---

**Version:** 1.0  
**Last Updated:** February 8, 2025  
**Format:** YAML 1.2  

---

*Happy calculating! 🎉*
