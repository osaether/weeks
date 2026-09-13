"""Regressions from the project review; assertions describe correct behavior.

Run with ``python3 -m pytest tests/ -q``; the normal C build dependencies are needed.
"""

import math
import os
import re
import shutil
import subprocess

import pytest

from tools.fh_crosscheck.parse_weeks import run_weeks_text


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


@pytest.mark.parametrize("yaml_text", [
    "conductors:\n  - {w: 1",
    "metadata: [1, 2",
    "metadata: {nested: [1, 2",
    "conductors:\n  - w: 1\n    metadata: [1, 2",
    case(conductors=(GROUND,) * 10) + "  - {metadata: [1, 2",
])
def test_truncated_yaml_exits_with_error(run_weeks, yaml_text):
    # Covers conductor parsing and every caller that skips nested YAML.
    # The subprocess timeout in run_weeks catches the former infinite loops.
    result = run_weeks(yaml_text)
    assert result.returncode > 0
    assert "YAML parse error" in result.stderr
    assert "RESISTANCE MATRIX" not in result.stdout


def test_valid_nested_metadata_is_skipped(run_weeks):
    signal = SIGNAL[:-1] + ", metadata: {nested: [1, {label: sample}]}}"
    result = run_weeks("metadata: {nested: [1, 2]}\n" + case(conductors=(GROUND, signal)))
    line_parameters(result)


@pytest.mark.parametrize("field", [
    "w", "h", "x", "y", "nw", "nh", "b", "er", "tan_delta",
])
@pytest.mark.parametrize("value", ["[1]", "{value: 1}"])
def test_numeric_conductor_fields_require_scalars(run_weeks, field, value):
    signal = re.sub(r"\b%s: [^,}]+" % field, "%s: %s" % (field, value), SIGNAL)
    result = run_weeks(case(conductors=(GROUND, signal)))
    assert result.returncode > 0, result.stdout + result.stderr
    assert field in result.stderr
    assert "ERROR" in result.stderr
    assert "RESULTS" not in result.stdout


@pytest.mark.parametrize("yaml_text,message", [
    ("", "mapping"),
    ("plain text", "mapping"),
    ("- " + case().replace("\n", "\n  "), "mapping"),
    (case(frequency="[1e9]"), "frequency"),
    (case(frequency="{value: 1e9}"), "frequency"),
    ("conductors: {}", "conductors"),
    ("conductors: invalid", "conductors"),
    (case().replace("conductors:\n", "conductors:\n  - invalid\n"), "conductor"),
    (case().replace("conductors:\n", "conductors:\n  - [invalid]\n"), "conductor"),
    (case().replace("conductors:\n", "conductors:\n  - null\n"), "conductor"),
    (case().replace("conductors:\n", "conductors:\n  - *undefined\n"), "YAML parse error"),
    ("frequency: 1e9\n" + case(), "duplicate"),
    (case() + "conductors: []\n", "duplicate"),
    (case(conductors=(GROUND, SIGNAL[:-1] + ", er: 2}")), "duplicate"),
    ("? [frequency]\n: 1e9\n" + case(), "key"),
    (case(conductors=(GROUND, SIGNAL[:-1] + ", [er]: 2}")), "key"),
    (case(frequency='"30e6\\0ignored"'), "frequency"),
    (case().replace("frequency:", '"frequency\\0ignored":'), "key"),
    (case() + "---\nfrequency: 1e9\n", "one YAML document"),
    (case() + "---\n", "one YAML document"),
    (case() + "---\nmetadata: [1,", "YAML parse error"),
    (case() + "<<: {frequency: 1e9}\n", "merge keys"),
    (case(conductors=(GROUND, SIGNAL[:-1] + ", <<: {er: 2}}")), "merge keys"),
    ("conductors: &model [*model, *model]\n", "conductor"),
])
def test_invalid_yaml_structure_aborts_calculation(run_weeks, yaml_text, message):
    result = run_weeks(yaml_text)
    assert result.returncode > 0, result.stdout + result.stderr
    assert message in result.stderr
    assert "RESULTS" not in result.stdout


@pytest.mark.parametrize("count", [10, 11])
def test_conductor_limit_never_truncates_model(run_weeks, count):
    signals = [SIGNAL.replace("y: 0.001", f"y: {0.001 * i}")
               for i in range(1, count)]
    result = run_weeks(case(conductors=(GROUND, *signals)))
    if count == 10:
        line_parameters(result)
        assert "Total conductors loaded: 10" in result.stderr
    else:
        assert result.returncode > 0, result.stdout + result.stderr
        assert "ERROR" in result.stderr
        assert "10" in result.stderr
        assert "RESULTS" not in result.stdout


def test_yaml_aliases_preserve_frequency_and_conductors(run_weeks):
    yaml_text = (
        "metadata:\n  frequency: &freq 1e9\n  ground: &ground " + GROUND + "\n"
        + case(frequency="*freq", conductors=("*ground", SIGNAL))
    )
    result = run_weeks(yaml_text)
    expected = run_weeks(case(frequency="1e9"))
    assert line_parameters(result) == line_parameters(expected)
    assert "FREQUENCY: 1.000000e+09 Hz" in result.stdout


def test_recursive_metadata_is_ignored_without_traversal(run_weeks):
    result = run_weeks("metadata: &meta {self: *meta}\n" + case())
    line_parameters(result)


def test_omitted_frequency_and_dielectric_keep_defaults(run_weeks):
    signal = SIGNAL.replace(", er: 4.4, tan_delta: 0.02", "")
    yaml_text = case(conductors=(GROUND, signal)).split("\n", 1)[1]
    result = run_weeks(yaml_text)
    params = line_parameters(result)
    assert "FREQUENCY: 3.000000e+07 Hz" in result.stdout
    assert params["eff_er"] == 1
    assert params["a_d"] == 0


def test_explicit_input_path_preserves_default(built_project, tmp_path):
    default = tmp_path / "test.yaml"
    default.write_text("deliberately invalid default input")
    selected = tmp_path / "selected input.yaml"
    selected.write_text(case(frequency="1e6"))
    result = subprocess.run(
        [str(built_project / "weeks"), selected.name], cwd=tmp_path,
        capture_output=True, text=True, timeout=10,
    )
    line_parameters(result)
    assert "FREQUENCY: 1.000000e+06 Hz" in result.stdout
    assert default.read_text() == "deliberately invalid default input"


@pytest.mark.parametrize("arguments,code,message", [
    (["--help"], 0, "Usage:"),
    (["-h"], 0, "Usage:"),
    (["one.yaml", "two.yaml"], 1, "Usage:"),
    (["missing.yaml"], 1, "Cannot open input file 'missing.yaml'"),
])
def test_cli_diagnostics(built_project, tmp_path, arguments, code, message):
    result = subprocess.run(
        [str(built_project / "weeks"), *arguments], cwd=tmp_path,
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == code
    assert message in result.stdout + result.stderr


@pytest.mark.parametrize("nw,nh,b,warn", [
    (4, 1, 1, False), (3, 2, 1, False),
    (4, 1, 0.5, True), (3, 2, 0.5, True), (3, 3, 0.5, False),
])
def test_mesh_symmetry_warning(run_weeks, nw, nh, b, warn):
    signal = SIGNAL.replace("nw: 3, nh: 1, b: 1", f"nw: {nw}, nh: {nh}, b: {b}")
    result = run_weeks(case(conductors=(GROUND, signal)))
    line_parameters(result)
    assert ("graded mesh is only symmetric" in result.stderr) == warn


@pytest.mark.parametrize("nw,warn", [(1, True), (3, False)])
def test_single_ground_element_warning(run_weeks, nw, warn):
    ground = GROUND.replace("nw: 3", f"nw: {nw}")
    result = run_weeks(case(conductors=(ground, SIGNAL)))
    line_parameters(result)
    assert ("ground plane has only one element" in result.stderr) == warn


@pytest.mark.parametrize("valid", [True, False])
def test_crosscheck_runner_preserves_workdir_input(built_project, tmp_path, valid):
    workdir = tmp_path / "work"
    workdir.mkdir()
    default = workdir / "test.yaml"
    default.write_text("existing input")
    backup = workdir / "test.yaml.xcbak"
    backup.write_text("existing backup")
    selected = tmp_path / "selected input.yaml"
    selected.write_text(case() if valid else "metadata: [1, 2")
    if valid:
        output = run_weeks_text(selected, str(built_project / "weeks"), workdir)
        assert "RESISTANCE MATRIX" in output
    else:
        with pytest.raises(RuntimeError, match="YAML parse error"):
            run_weeks_text(selected, str(built_project / "weeks"), workdir)
    assert default.read_text() == "existing input"
    assert backup.read_text() == "existing backup"
