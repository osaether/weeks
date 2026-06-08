/* Modified CALCL.H with dielectric support */

void calcl (ZMAT *, element *, double, element, conductor *, int);

/* New helper functions */
double calc_eff_dielectric(double w, double h, double er);
double calc_dielectric_loss(double er, double tan_delta,
                            double Omega, double w, double h);

/* Per-line quasi-TEM transmission-line parameters (Z0, C, attenuation, gamma).
 * Reads the diagonal self-terms of the final N x N impedance matrix z. */
void calc_line_params(ZMAT *z, double Omega, conductor *cond, int N);
