import pytest

from tools.fh_crosscheck.run_fasthenry import parse_zc

# Two-frequency, 2x2 Zc.mat sample in FastHenry's real format.
SAMPLE = """\
Row 2:  N1s  to  N0s
Row 1:  N2s  to  N0s
Impedance matrix for frequency = 30000000 2 x 2
      20.5  +0.06j   6.75  +0.012j
      6.70  +0.011j   20.6  +0.061j
Impedance matrix for frequency = 1e+08 2 x 2
      30.0  +0.20j   7.0  +0.05j
      6.9  +0.04j   31.0  +0.21j
"""


def test_parse_zc_selects_frequency_block():
    z = parse_zc(SAMPLE, 30e6)
    assert len(z) == 2 and len(z[0]) == 2
    assert z[0][0] == complex(20.5, 0.06)
    assert z[0][1] == complex(6.75, 0.012)
    assert z[1][0] == complex(6.70, 0.011)


def test_parse_zc_picks_nearest_when_exact_absent():
    z = parse_zc(SAMPLE, 9e7)  # nearest is the 1e8 block
    assert z[0][0] == complex(30.0, 0.20)


def test_parse_zc_raises_when_empty():
    with pytest.raises(ValueError):
        parse_zc("no matrices here", 30e6)


def test_parse_zc_row_order_and_negative_imag():
    # Real FastHenry output: asymmetric 3-port case. Port 1 (data row 0) was the
    # widest/lowest-R bar; port 3 (data row 2) the narrowest/highest-R. Confirms
    # body rows are in ascending port order, and negative imaginaries parse.
    sample = (
        "Row 3:  n3s  to  n0s\n"
        "Row 2:  n2s  to  n0s\n"
        "Row 1:  n1s  to  n0s\n"
        "Impedance matrix for frequency = 3e+07 3 x 3\n"
        "      0.061914     +0.731567j    0.00430169    -0.0102765j    0.00359427   +0.00432681j \n"
        "   0.00449565   -0.00986562j      0.128766     +0.890128j    0.00607244   +0.00577569j \n"
        "    0.0028022   +0.00252797j    0.00602415   +0.00576023j      0.387439      +1.19108j \n"
    )
    z = parse_zc(sample, 30e6)
    assert len(z) == 3 and len(z[0]) == 3
    assert z[0][0] == complex(0.061914, 0.731567)
    assert z[0][1] == complex(0.00430169, -0.0102765)   # negative imaginary
    assert z[2][2] == complex(0.387439, 1.19108)
    assert z[0][0].real < z[2][2].real                  # row 0 = port 1 (low R)
