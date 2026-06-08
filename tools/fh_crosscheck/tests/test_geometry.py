import os
import tempfile

from tools.fh_crosscheck.geometry import load_case

SAMPLE = """\
frequency: 30e6  # 30 MHz

conductors:
  - name: line0
    w: 2800e-6
    h: 2.0e-6
    x: 0.0
    y: 0.0
    nw: 201
    nh: 3
    b: 0.2
  - name: line1
    w: 150e-6
    h: 18e-6
    x: 600e-6
    y: 77e-6
    nw: 21
    nh: 7
    b: 0.9
"""


def _write(text):
    fd, path = tempfile.mkstemp(suffix=".yaml")
    os.write(fd, text.encode())
    os.close(fd)
    return path


def test_load_case_parses_frequency_and_conductors():
    freq, conductors = load_case(_write(SAMPLE))
    assert freq == 30e6
    assert len(conductors) == 2


def test_conductor_fields_have_correct_types_and_values():
    _, conductors = load_case(_write(SAMPLE))
    gnd = conductors[0]
    assert gnd["name"] == "line0"
    assert gnd["w"] == 2800e-6
    assert gnd["h"] == 2.0e-6
    assert gnd["nw"] == 201 and isinstance(gnd["nw"], int)
    assert gnd["nh"] == 3 and isinstance(gnd["nh"], int)
    sig = conductors[1]
    assert sig["x"] == 600e-6
    assert sig["nw"] == 21
