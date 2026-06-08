"""Format side-by-side weeks-vs-FastHenry matrix comparisons."""


def percent_diff(weeks_value, fh_value):
    """Signed % difference of FastHenry relative to weeks; None if weeks==0."""
    if weeks_value == 0:
        return None
    return 100.0 * (fh_value - weeks_value) / weeks_value


def compare_matrix(name, weeks_mat, fh_mat, tol):
    """Build a comparison table for one matrix.

    Returns ``(text, flagged_count, total, max_abs_pct)``. Entries whose
    |%diff| exceeds ``tol`` are marked with a trailing '*'.
    """
    lines = [
        "*** %s: weeks vs FastHenry ***" % name,
        "  i  j        weeks    fasthenry        %diff",
    ]
    flagged = 0
    total = 0
    max_abs = 0.0
    for i, row in enumerate(weeks_mat):
        for j, w in enumerate(row):
            f = fh_mat[i][j]
            pd = percent_diff(w, f)
            total += 1
            if pd is None:
                mark = ""
                pd_text = "     n/a"
            else:
                abs_pd = abs(pd)
                max_abs = max(max_abs, abs_pd)
                mark = " *" if abs_pd > tol else ""
                pd_text = "%+8.2f%%" % pd
                if abs_pd > tol:
                    flagged += 1
            lines.append(
                "%3d %3d %12.4e %12.4e %s%s" % (i + 1, j + 1, w, f, pd_text, mark)
            )
    lines.append(
        "  -> %d/%d entries over %.0f%% tolerance; max |diff| = %.2f%%"
        % (flagged, total, tol, max_abs)
    )
    return "\n".join(lines), flagged, total, max_abs
