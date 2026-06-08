# GEMINI.md - WEEKS Microstrip Calculator

This file provides context and instructions for AI assistants working on the `weeks` project.

## Project Overview

`weeks` is a C-based command-line tool that implements the **Partial Element Equivalent Circuit (PEEC)** method (Weeks et al., IBM, 1979) to calculate the resistance and inductance of rectangular conductors on PCB substrates.

### Key Capabilities
- **R/L Matrices**: Computes frequency-dependent series resistance (Ω/m) and inductance (H/m) matrices for multi-conductor systems.
- **Transmission-Line Parameters**: Derives per-line quasi-TEM parameters including characteristic impedance ($Z_0$), capacitance ($C$), effective permittivity ($\varepsilon_{eff}$), and attenuation.
- **Dielectric Support**: Supports materials like FR4 and Rogers substrates (affects transmission-line parameters only).
- **Validation**: Includes Python-based harnesses to cross-check results against FastHenry (field solver) and Hammerstad-Jensen closed-form solutions.

## Architecture & Data Flow

1.  **Input Phase (`src/input.c`)**: Parses a YAML configuration file (hardcoded as `test.yaml`) using `libyaml`. Populates the `conductor[]` array and sets the `global_frequency`.
2.  **Meshing Phase (`src/build.c`)**: Discretizes each conductor into rectangular mesh elements based on user-defined divisions (`nw`, `nh`) and density (`b`).
3.  **Matrix Phase (`src/calcl.c`)**: Builds a large complex impedance matrix $Z$ for all filaments. Self-inductance is calculated in `src/lpp.c` using the Neumann partial inductance formula.
4.  **Aggregation Phase (`src/weeks.c`)**: Inverts the $Z$ matrix (using Meschach), aggregates filament-level admittances back to per-conductor quantities, and inverts again to get the final $N \times N$ R/L matrices.
5.  **Output Phase**: Prints the R, L, and $|Z|$ matrices. Calls `calc_line_params()` to print transmission-line results.

## Build and Run

### Requirements
- **GCC**: C compiler.
- **libmeschach-dev**: Matrix/vector operations library.
- **libyaml-dev**: YAML parsing library.

### Key Commands
```bash
# Check if libraries are installed
make check-deps

# Build the 'weeks' executable
make

# Run the tool (reads from test.yaml)
./weeks

# Run with material examples
make test-fr4      # FR4 substrate
make test-air      # Air baseline
make test-rogers   # Rogers RO4003C

# Validation
make check-fasthenry  # Cross-check R/L vs FastHenry (needs fasthenry on PATH)
make check-z0         # Sanity-check Z0 vs Hammerstad-Jensen closed form

# Cleaning
make clean
```

## Development Conventions

- **Input Filename**: The C program hardcodes `test.yaml` as the input. To run a specific case, copy it to `test.yaml`.
- **Conductor 0**: The first conductor (`line0`) in the YAML file MUST be the ground plane.
- **Substrate Height**: Not a direct input. It is derived as the gap between the signal trace's bottom (`y`) and the ground plane's top (`y + h`).
- **Dielectric Parameters**:
    - `er` and `tan_delta` are material properties.
    - They **do not** affect the series R/L/|Z| matrices (which are dielectric-independent for $\mu_r \approx 1$).
    - They **do** affect the separate "TRANSMISSION-LINE PARAMETERS" section.
- **Units**: All dimensions in the YAML file MUST be in **meters** (e.g., `1.6e-3` for 1.6 mm).
- **Matrix Library**: Uses `libmeschach`. Key types: `ZMAT` (complex matrix), `ZVEC` (complex vector).
- **Testing**:
    - The C code lacks an internal unit test suite.
    - Use the Python harnesses in `tools/` for numerical validation.
    - FastHenry validation requires `fasthenry` to be installed manually (see `docs/fasthenry-crosscheck.md`).

## Directory Structure

- `src/`: C source files.
- `include/`: C header files.
- `examples/`: Sample YAML configurations.
- `tools/`: Python validation harnesses.
- `docs/`: Technical documentation and cross-check details.
- `build/`: Temporary build artifacts.
