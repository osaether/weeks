/* Diagnostic for CLAUDE_FINDINGS.md; reports error, not a pass/fail test. */
#include <stdio.h>
#include <math.h>
#include "weeks.h"
#include "lpp.h"

int main(void)
{
    const double s = 1e-6;
    const double expected = 2e-7 * log(2.0);
    element a = {0, s, 0, s};

    puts("d/s lp(a,b)-lp(a,c) relative_error_vs_filament");
    for (int k = 2; k <= 6; k++) {
        double d = s * pow(10.0, k);
        element b = {d, d+s, 0, s};
        element c = {2*d, 2*d+s, 0, s};
        double difference = lp(&a, &b) - lp(&a, &c);
        printf("%.0f %.12g %.6g\n", d/s, difference,
               fabs((difference - expected) / expected));
    }
    return 0;
}
