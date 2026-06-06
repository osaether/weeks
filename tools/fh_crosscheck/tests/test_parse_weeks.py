from tools.fh_crosscheck.parse_weeks import parse_weeks_output

SAMPLE = """\

========================================
RESULTS
========================================

FREQUENCY: 3.000000e+07 Hz (30.00 MHz)

*** RESISTANCE MATRIX (Ohm/m) ***

               1           2

  1 +2.0733e+01 +6.7517e+00 
  2 +6.7517e+00 +2.0566e+01 

*** INDUCTANCE MATRIX (H/m) ***

               1           2

  1 +3.1468e-07 +5.6073e-08
  2 +5.6073e-08 +3.1092e-07

*** IMPEDANCE MAGNITUDE (Ohm) at 30.00 MHz ***
"""


def test_parse_weeks_resistance_and_inductance():
    R, L = parse_weeks_output(SAMPLE)
    assert len(R) == 2 and len(R[0]) == 2
    assert R[0][0] == 20.733
    assert R[0][1] == 6.7517
    assert L[1][1] == 3.1092e-07


def test_parse_single_entry_matrix():
    one = SAMPLE.replace(
        "               1           2\n\n  1 +2.0733e+01 +6.7517e+00 \n  2 +6.7517e+00 +2.0566e+01 ",
        "               1\n\n  1 +2.0733e+01 ",
    )
    R, _ = parse_weeks_output(one)
    assert R == [[20.733]]
