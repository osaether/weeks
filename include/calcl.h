/* Modified CALCL.H with dielectric support */

void calcl (ZMAT *, element *, double, element, conductor *, int);

/* New helper functions */
double calc_eff_dielectric(double w, double h, double er);
double calc_dielectric_loss(double er, double tan_delta, 
                            double Omega, double w, double h);
