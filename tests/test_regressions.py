"""Regressions from the project review; assertions describe correct behavior.

Run with ``python3 -m pytest tests/ -q``; the normal C build dependencies are needed.
"""

import math
import os
import re
import shutil
import subprocess

import pytest


GROUND = "{w: 0.01, h: 0.000035, nw: 3, nh: 1, b: 1}"
SIGNAL = (
    "{w: 0.001, h: 0.000035, x: 0.004, y: 0.001, "
    "nw: 3, nh: 1, b: 1, er: 4.4, tan_delta: 0.02}"
)


def case(frequency="30e6", conductors=(GROUND, SIGNAL)):
    return "frequency: %s\nconductors:\n%s" % (
        frequency, "".join("  - %s\n" % c for c in conductors)
    )


def line_parameters(result):
    assert result.returncode == 0, result.stderr
    section = result.stdout.split("TRANSMISSION-LINE PARAMETERS", 1)[1]
    for line in section.splitlines():
        fields = line.split()
        if len(fields) == 9 and fields[0] == "1":
            values = [float(field) for field in fields[1:]]
            assert all(math.isfinite(value) for value in values), line
            return dict(zip(
                ("eff_er", "z0", "c", "a_c", "a_d", "a", "beta", "eff_er_im"),
                values,
            ))
    pytest.fail("No numeric transmission-line row for line 1")


def test_valid_scientific_notation_produces_finite_results(run_weeks):
    result = run_weeks(case())
    assert "FREQUENCY: 3.000000e+07 Hz" in result.stdout
    params = line_parameters(result)
    assert params["z0"] > 0
    assert params["a_d"] > 0


def test_dielectric_attenuation_matches_independent_reference(run_weeks):
    params = line_parameters(run_weeks(case()))
    # Qucs technical documentation, equation 11.79:
    # https://qucs.sourceforge.net/tech/node75.html
    # alpha_d = er/sqrt(eff_er) * (eff_er-1)/(er-1)
    #           * pi/lambda_0 * tan_delta, in Np/m.
    # Use reported eff_er to isolate attenuation from the permittivity model.
    er, tan_delta, frequency, c = 4.4, 0.02, 30e6, 299792458.0
    eff_er = params["eff_er"]
    expected_np = (
        er / math.sqrt(eff_er) * (eff_er - 1) / (er - 1)
        * math.pi * frequency / c * tan_delta
    )
    expected_db = expected_np * 20 / math.log(10)
    # Output uses five significant figures; tolerate its rounding.
    assert params["a_d"] == pytest.approx(expected_db, rel=2e-4)


@pytest.mark.parametrize("position", [0, 1, 2], ids=["ground", "middle", "last"])
def test_invalid_conductor_aborts_entire_calculation(run_weeks, position):
    conductors = [GROUND, SIGNAL]
    conductors.insert(position, "{w: -1, h: 0.000035, nw: 3, nh: 1}")
    result = run_weeks(case(conductors=conductors))
    assert result.returncode > 0, (
        "An invalid conductor must cause a controlled error, not a successful "
        "calculation on the remaining conductors.\n" + result.stderr
    )
    assert "ERROR" in result.stderr
    assert "RESISTANCE MATRIX" not in result.stdout


@pytest.mark.parametrize("frequency", ["nan", "inf", "30MHz", "1e999", "0", "-1", '""'])
def test_invalid_numeric_frequency_is_rejected(run_weeks, frequency):
    result = run_weeks(case(frequency=frequency))
    assert result.returncode > 0, (
        "Invalid frequency %r must be rejected before calculation.\n%s\n%s"
        % (frequency, result.stderr, result.stdout)
    )
    assert "ERROR" in result.stderr
    assert "RESISTANCE MATRIX" not in result.stdout


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("w", "nan"), ("h", "inf"), ("x", "bad"), ("y", "1mm"),
        ("b", "nan"), ("er", "nan"), ("er", "0"),
        ("tan_delta", "inf"), ("tan_delta", "-0.02"),
        ("nw", "1e100"), ("nh", "nan"), ("nw", "1.5"),
    ],
)
def test_invalid_conductor_numbers_are_rejected(run_weeks, field, value):
    signal = re.sub(r"\b%s: [^,}]+" % field, "%s: %s" % (field, value), SIGNAL)
    result = run_weeks(case(conductors=(GROUND, signal)))
    assert result.returncode > 0, result.stdout + result.stderr
    assert "ERROR" in result.stderr
    assert field in result.stderr
    assert "RESISTANCE MATRIX" not in result.stdout


@pytest.mark.parametrize("signal", [SIGNAL.replace("er: 4.4", "er: 1"),
                                    SIGNAL.replace("tan_delta: 0.02", "tan_delta: 0")])
def test_air_or_lossless_substrate_has_no_dielectric_attenuation(run_weeks, signal):
    params = line_parameters(run_weeks(case(conductors=(GROUND, signal))))
    assert params["a_d"] == 0
    assert params["eff_er_im"] == 0


@pytest.mark.parametrize(
    ("header", "object_file"),
    [("weeks.h", "weeks.o"), ("calcl.h", "calcl.o"), ("lpp.h", "lpp.o")],
)
def test_header_change_rebuilds_object_and_executable(
    built_project, tmp_path, header, object_file
):
    project = tmp_path / "project"
    shutil.copytree(built_project, project)
    obj = project / "build" / object_file
    binary = project / "weeks"
    old_object_mtime = obj.stat().st_mtime_ns
    old_binary_mtime = binary.stat().st_mtime_ns

    path = project / "include" / header
    path.write_text(path.read_text() + "\n/* Regression test: header changed. */\n")
    # Guarantee the header is newer even on filesystems with coarse timestamps.
    newer = max(old_object_mtime, old_binary_mtime) + 2_000_000_000
    os.utime(path, ns=(newer, newer))
    result = subprocess.run(
        ["make"], cwd=project, capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert obj.stat().st_mtime_ns != old_object_mtime, (
        "%s did not rebuild after %s changed.\n%s" % (object_file, header, result.stdout)
    )
    assert binary.stat().st_mtime_ns != old_binary_mtime, "Executable was not relinked"


def test_gamma_explanation_agrees_with_attenuation_column_units(run_weeks):
    result = run_weeks(case())
    line_parameters(result)
    header = next(line for line in result.stdout.splitlines() if "Z0(Ohm)" in line)
    column_units = re.search(r"\ba\(([^)]+)\)", header).group(1)
    explanation = next(
        line for line in result.stdout.splitlines() if "gamma =" in line
    )
    # A direct reference must use the actual column units. Removing this claim
    # or replacing it with an explicit dB-to-Np conversion is also acceptable.
    direct_reference = re.search(
        r"alpha\s*=\s*a column above in ([A-Za-z]+/m)", explanation
    )
    if direct_reference:
        assert direct_reference.group(1) == column_units, (
            "The gamma explanation labels the %s attenuation column as %s; "
            "alpha requires conversion to Np/m."
            % (column_units, direct_reference.group(1))
        )


def test_gamma_conversion_from_db_to_np_is_correct(run_weeks):
    result = run_weeks(case())
    line_parameters(result)
    conversion = re.search(r"alpha in Np/m = a\(dB/m\) / ([0-9.]+)", result.stdout)
    assert conversion, "Output must explain how to convert attenuation for gamma"
    assert float(conversion.group(1)) == pytest.approx(20 / math.log(10), rel=1e-9)
