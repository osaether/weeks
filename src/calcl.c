/* Modified calcl.c with dielectric support for Weeks
 * 
 * Calculates partial inductances accounting for dielectric substrate
 * The dielectric primarily affects capacitance, but we account for
 * effective permittivity in the calculations
 */

#include "zmatrix2.h"
#include "weeks.h"
#include "calcl.h"
#include "lpp.h"
#include <math.h>

/* Calculate effective dielectric constant for microstrip
 * Using approximate formula (Hammerstad & Jensen)
 * This is valid for most practical microstrip configurations
 */
double calc_eff_dielectric(double w, double h, double er)
{
  double a, b, eff_er;
  
  if (h <= 0.0 || er <= 1.0) {
    /* No substrate or air - return 1.0 */
    return 1.0;
  }
  
  /* Hammerstad & Jensen approximation for effective dielectric constant */
  a = 1.0 + (1.0/49.0) * log(
      ((w/h) * (w/h) * (w/h) * (w/h) + (w/h/52.0) * (w/h/52.0)) /
      ((w/h) * (w/h) * (w/h) * (w/h) + 0.432)
      ) + (1.0/18.7) * log(1.0 + (w/h/18.1) * (w/h/18.1) * (w/h/18.1));
  
  b = 0.564 * pow((er - 0.9)/(er + 3.0), 0.053);
  
  eff_er = (er + 1.0)/2.0 + ((er - 1.0)/2.0) * pow(1.0 + 10.0*h/w, -a*b);
  
  return eff_er;
}

/* Calculate dielectric loss contribution
 * Returns additional resistance per unit length due to dielectric loss
 */
double calc_dielectric_loss(double er, double tan_delta, 
                            double Omega, double w, double h)
{
  double eff_er, loss_per_length;
  const double c = 2.99792458e8; /* speed of light */

  if (tan_delta <= 0.0 || h <= 0.0) {
    return 0.0;
  }

  eff_er = calc_eff_dielectric(w, h, er);
  if (eff_er <= 1.0)
    return 0.0;

  /* Dielectric loss: α_d = (π/λ) * (εr - 1)/(εeff - 1) * (εeff/εr) * tan(δ)
   * where λ = 2πc/ω
   * Converting to resistance per unit length
   */
  loss_per_length = (Omega * sqrt(eff_er) / c) *
                    ((er - 1.0)/(eff_er - 1.0)) *
                    (eff_er/er) * tan_delta;
  
  return loss_per_length;
}

void calcl(ZMAT *Z, element *e, double Omega,
            element e0, conductor *cond, int N)
{
  int i, j;
  int dim;
  double lmm, lpi0, r00;
  double sigma=58e6;  /* Copper conductivity S/m */
  double eff_er;
  double diel_loss;
  VEC *lpj;
  dim = Z->m;

  /* Effective permittivity and dielectric loss are reported for information
   * only. They influence the line capacitance / characteristic impedance Z0,
   * which this tool does NOT compute -- it solves for the series R and L
   * matrices. Folding the dielectric attenuation (units 1/m) into the
   * resistance matrix (units Ohm/m) would be dimensionally wrong, so it is
   * not applied. */
  if (cond != NULL && cond[0].substrate_h > 0.0) {
    eff_er = calc_eff_dielectric(cond[0].w, cond[0].substrate_h, cond[0].er);
    fprintf(stderr, "\n  Ground plane effective εr: %.3f", eff_er);

    diel_loss = calc_dielectric_loss(cond[0].er, cond[0].tan_delta,
                                     Omega, cond[0].w, cond[0].substrate_h);
    fprintf(stderr, "\n  Dielectric attenuation (informational): %.3e 1/m", diel_loss);
  } else {
    eff_er = 1.0;  /* Air */
    diel_loss = 0.0;
  }

  /* Report effective permittivity per signal conductor (informational, not
   * applied -- see note above). Uses the correct per-conductor properties. */
  if (cond != NULL) {
    for (i = 1; i <= N; i++) {
      if (cond[i].substrate_h > 0.0)
        fprintf(stderr, "\n  Line %d effective εr: %.3f", i,
                calc_eff_dielectric(cond[i].w, cond[i].substrate_h, cond[i].er));
    }
  }

  lmm = lp (&e0, &e0);
  r00 = 1/(sigma*(e0.x2-e0.x1)*(e0.y2-e0.y1));

  lpj = v_get (dim);
  for (j=0; j<dim; j++)
    lpj->ve[j] = lp (&e0, &e[j]);
    
  for (i=0; i<dim; i++)
    {
      lpi0 = lmm-lp (&e[i], &e0);
      for (j=0;j<=i;j++)
        {
          /* Inductance is affected by effective permeability
           * For non-magnetic materials, μr ≈ 1
           * The effective permittivity mainly affects capacitance
           * L remains approximately the same
           */
          Z->me[i][j].im = Z->me[j][i].im = Omega * (lpi0-lpj->ve[j]+lp (&e[i], &e[j]));
          Z->me[i][j].re = Z->me[j][i].re = r00;
        }
    }
  V_FREE (lpj);
  
  /* Add each filament's own conductor (ohmic) resistance to the diagonal.
   * This must cover ALL filaments (ground plane + signal traces), not just
   * the signal ones: every filament forms a loop with the reference element
   * e0, mirroring the inductance self-term above. Omitting the ground-plane
   * filaments drops the return-path resistance and yields unphysical
   * (negative) mutual resistances. The reference filament e0 itself is not in
   * the matrix (build.c diverts it out); its resistance is the shared r00
   * term already written to every entry. Dielectric loss is intentionally not
   * added here (see note above). */
  for (i=0; i<dim; i++)
    Z->me[i][i].re += 1/(sigma*(e[i].x2-e[i].x1)*(e[i].y2-e[i].y1));
}
