/* Modified CALCL.H with dielectric support */

void calcl (ZMAT *, element *, double, element, conductor *, int);

/* New helper functions */
double calc_eff_dielectric(double w, double h, double er);
double calc_dielectric_loss(double er, double tan_delta,
                            double Omega, double w, double h);

/* Substrate height (trace-to-ground gap) for signal conductor line_index,
 * derived from geometry. Replaces the old per-conductor substrate_h input. */
double substrate_height(const conductor *cond, int line_index);

/* Per-line quasi-TEM transmission-line parameters (Z0, C, attenuation, gamma).
 * Reads the diagonal self-terms of the final N x N impedance matrix z. */
void calc_line_params(ZMAT *z, double Omega, conductor *cond, int N);
