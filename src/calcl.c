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
  VEC *lpj;
  dim = Z->m;
  (void)cond;  /* dielectric is handled in calc_line_params(), not the matrix */

  /* The dielectric does NOT enter the series R/L matrices: those are purely
   * geometric (and dielectric attenuation, units 1/m, cannot be added to a
   * resistance in Ohm/m). The effective permittivity and loss feed the per-
   * line transmission-line parameters in calc_line_params() instead, where the
   * dielectric loss enters the shunt side of the line correctly. */

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

/* Substrate height for signal conductor `line_index` (1-based): the vertical
 * gap between the bottom of the trace and the top of the ground plane,
 * cond[0]. For a microstrip the substrate fills exactly this gap, so the
 * dielectric height is a property of the geometry -- not a separate input.
 * Returns <= 0 if the trace is not above the ground plane. */
double substrate_height(const conductor *cond, int line_index)
{
  return cond[line_index].y - (cond[0].y + cond[0].h);
}

/* Per-line (quasi-TEM) transmission-line parameters.
 *
 * This is where the dielectric finally affects a reported result. The series
 * R/L matrices (above) are dielectric-independent; here we add the shunt side
 * of the line. For each signal conductor i we take the diagonal self-terms of
 * the final N x N impedance matrix z as the per-line series R and L, then use
 * the quasi-TEM relation LC = eff_er/c^2 (L is dielectric-independent because
 * mu_r ~ 1) to recover C, Z0, attenuation and the complex propagation gamma.
 *
 * Approximation: using the diagonal self-terms treats each line in isolation;
 * it does not model inter-line capacitive coupling under an inhomogeneous
 * dielectric (that would require a full electrostatic P-matrix solve). This is
 * the standard single-line characterization. */
void calc_line_params(ZMAT *z, double Omega, conductor *cond, int N)
{
  const double c = 2.99792458e8;      /* speed of light, m/s */
  const double NP2DB = 8.685889638;   /* Np/m -> dB/m */
  int i;

  printf("\n*** TRANSMISSION-LINE PARAMETERS (per line, quasi-TEM) at %.2f MHz ***\n\n",
         Omega/(2.0*M_PI)/1e6);
  printf("Line     eff_er       Z0(Ohm)      C(F/m)       a_c(dB/m)    a_d(dB/m)    a(dB/m)      beta(rad/m)  eff_er''\n\n");

  for (i = 1; i <= N; i++) {
    double R_ii = z->me[i-1][i-1].re;        /* Ohm/m */
    double L_ii = z->me[i-1][i-1].im / Omega; /* H/m   */
    double h_sub = substrate_height(cond, i); /* trace-to-ground gap, m */
    double eff_er, beta, C, Z0, a_c, a_d, a_tot, tand_eff, eff_er_im;

    /* Substrate height is the geometric trace-to-ground gap, so eff_er and L
     * are consistent by construction (no separate substrate_h to disagree). */
    eff_er = calc_eff_dielectric(cond[i].w, h_sub, cond[i].er);
    if (eff_er < 1.0)
      eff_er = 1.0;                          /* air / no substrate */

    if (L_ii <= 0.0) {
      /* Degenerate line: cannot form C/Z0. Report what we have. */
      printf("%3d    %+0.4e  (L<=0, skipped)\n", i, eff_er);
      continue;
    }

    beta = Omega * sqrt(eff_er) / c;         /* rad/m */
    C    = eff_er / (c * c * L_ii);          /* F/m   */
    Z0   = sqrt(L_ii / C);                   /* Ohm   */

    a_c  = R_ii / (2.0 * Z0);                /* Np/m  */
    a_d  = calc_dielectric_loss(cond[i].er, cond[i].tan_delta,
                                Omega, cond[i].w, h_sub); /* Np/m */
    a_tot = a_c + a_d;                       /* Np/m  */

    /* gamma = a_tot + j*beta. Express the dielectric loss as an effective
     * loss tangent and the imaginary part of the effective permittivity. */
    tand_eff  = (beta > 0.0) ? (2.0 * a_d / beta) : 0.0;
    eff_er_im = eff_er * tand_eff;

    printf("%3d    %+0.4e  %+0.4e  %+0.4e  %+0.4e  %+0.4e  %+0.4e  %+0.4e  %+0.4e\n",
           i, eff_er, Z0, C,
           a_c * NP2DB, a_d * NP2DB, a_tot * NP2DB,
           beta, eff_er_im);
  }

  printf("\n  gamma = alpha + j*beta  (alpha = a column above in Np/m; beta in rad/m)\n");
  printf("  Complex effective permittivity per line: eff_er - j*eff_er''\n");
}
