from tools.fh_crosscheck.report import percent_diff, compare_matrix


def test_percent_diff():
    assert percent_diff(100.0, 110.0) == 10.0
    assert percent_diff(100.0, 90.0) == -10.0
    assert percent_diff(0.0, 5.0) is None


def test_compare_matrix_counts_flags():
    w = [[100.0, 50.0], [50.0, 100.0]]
    f = [[105.0, 80.0], [50.0, 100.0]]  # entry [0][1] is +60% -> flagged
    text, flagged, total, max_abs = compare_matrix("R", w, f, tol=12.0)
    assert total == 4
    assert flagged == 1
    assert round(max_abs, 1) == 60.0
    assert "R" in text and "%" in text
