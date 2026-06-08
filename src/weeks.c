#include <stdio.h>
#include <time.h>
#include <math.h>
#include <stdlib.h>
#include "machine.h"
#include "zmatrix2.h"
#include "weeks.h"
#include "calcl.h"

extern double global_frequency;

#ifndef PI
#define PI 3.141592653589793116
#endif

int main(void)
{
  int i, j, k, m;
  conductor *test;
  element *e, e0;
  time_t tb, ts, t1;
  int M,N,tk,ti, n0;

  double f, Omega;
  ZMAT *Z=ZMNULL, *Y=ZMNULL, *z=ZMNULL,*y=ZMNULL;
  FILE *fp;
  
  fprintf(stderr, "\n========================================\n");
  fprintf(stderr, "Microstrip Resistance Calculator\n");
  fprintf(stderr, "With Dielectric Substrate Support\n");
  fprintf(stderr, "YAML Input Format\n");
  fprintf(stderr, "========================================\n");

  tb = time(&tb);
  setbuf(stdout, (char *)NULL);
  setbuf(stderr, (char *)NULL);

  if ((fp = fopen("test.yaml", "r")) == NULL)
    {
      fprintf(stderr, "ERROR: Cannot open input file '%s'\n", "test.yaml");
      fprintf(stderr, "Please create a YAML input file with conductor definitions.\n");
      exit(EXIT_FAILURE);
    }
    
  fprintf(stderr, "\nReading YAML input file...");
  test = getinput (fp, &N);
  fclose(fp);
  if(test == NULL)
    exit(EXIT_FAILURE);
  N--;
  
  /* Use frequency from YAML file */
  f = global_frequency;
  Omega = 2.0*PI*f;
  
  fprintf(stderr, "\n");

  fprintf(stderr, "\n\nBuilding partial elements...");

  n0 = M = test[0].nw*test[0].nh-1;
  for(i=1;i<=N;i++)
    M += test[i].nw*test[i].nh;
  e = build_elements(M, N, test, &e0);
  if (e == NULL)
    exit(EXIT_FAILURE);
  fprintf(stderr, "\nNumber of elements: %d", M);

  /* Display dielectric information. The substrate height is the trace-to-
   * ground gap, derived from geometry (not an input). */
  fprintf(stderr, "\n\nDielectric Properties:");
  fprintf(stderr, "\n  Ground plane (line0): εr=%.2f", test[0].er);

  for(i=1; i<=N; i++) {
    fprintf(stderr, "\n  Line %d: εr=%.2f, substrate h=%.2e m (from geometry)",
            i, test[i].er, substrate_height(test, i));
    if(test[i].tan_delta > 0.0)
      fprintf(stderr, ", tan δ=%.4f", test[i].tan_delta);
  }

  t1 = time(&t1);
  Z = zm_get(M,M);
  fprintf(stderr,"\n\nCalculating partial inductances with dielectric...");
  
  /* Call modified calcl with conductor array for dielectric info */
  calcl(Z, e, Omega, e0, test, N);
  
  free(e);
  e = NULL;
  fprintf(stderr, " -> %lu seconds", (unsigned long)(time(NULL)-t1));

  fprintf(stderr,"\n\nInverting matrix of partial impedances:\n");

  Y = zm_inverse(Z, Z);
  
  y = zm_get(N, N);

  ti = n0;
  for(i=0;i<N;i++)
  {
    tk = n0;      
    for(k=0;k<N;k++)
    {
      y->me[i][k].re = 0.0;
      y->me[i][k].im = 0.0;
      for(j=0; j<test[i+1].n; j++)
      {
        for(m=0;m<test[k+1].n;m++)
        {
          y->me[i][k].re += Y->me[ti+j][tk+m].re;
          y->me[i][k].im += Y->me[ti+j][tk+m].im;
        }
      }
      tk += test[k+1].n;
    }
    ti += test[i+1].n;
  }
  /* test[] is freed after calc_line_params() below, which still needs the
   * per-conductor dielectric/geometry fields. */
  z = zm_inverse(y, y);
  y = ZMNULL;  

  /* ===== RESULTS OUTPUT ===== */
  printf("\n\n========================================\n");
  printf("RESULTS\n");
  printf("========================================\n");
  printf("\nFREQUENCY: %e Hz (%.2f MHz)\n", f, f/1e6);
    
  printf("\n*** RESISTANCE MATRIX (Ohm/m) ***\n\n");
  printf("    ");
  for(j=1;j<=N;j++)
    printf("%12d",j);
  printf("\n\n");
  for(i=0;i<N;i++) {
    printf("%3d ",i+1);
    for(j=0;j<N;j++)
      printf("%+0.4e ",z->me[i][j].re);
    printf("\n");
  }

  printf("\n*** INDUCTANCE MATRIX (H/m) ***\n\n");
  printf("    ");
  for(j=1;j<=N;j++)
    printf("%12d",j);
  printf("\n\n");

  for(i=0;i<N;i++) {
    printf("%3d ",i+1);
    for(j=0;j<N;j++)
      printf("%+0.4e ",z->me[i][j].im/Omega);
    printf("\n");
  }
  
  printf("\n*** IMPEDANCE MAGNITUDE (Ohm) at %.2f MHz ***\n\n", f/1e6);
  printf("    ");
  for(j=1;j<=N;j++)
    printf("%12d",j);
  printf("\n\n");

  for(i=0;i<N;i++) {
    printf("%3d ",i+1);
    for(j=0;j<N;j++) {
      double magnitude = sqrt(z->me[i][j].re * z->me[i][j].re + 
                              z->me[i][j].im * z->me[i][j].im);
      printf("%+0.4e ", magnitude);
    }
    printf("\n");
  }

  /* Per-line transmission-line parameters (Z0, C, attenuation, propagation).
   * Reads the diagonal self-terms of z, so it must run before ZM_FREE(z). */
  calc_line_params(z, Omega, test, N);

  free(test);
  test = 0;
  ZM_FREE(z);
  ZM_FREE(Z);   /* same pointer as Y after zm_inverse(Z,Z) */
  ts = time(&ts);

  /* Dominant memory cost is the M x M complex impedance matrix, plus the
   * working copy zm_inverse allocates internally during factorization. */
  size_t matrix_mem = 2 * (size_t)M * (size_t)M * sizeof(complex);
  printf("\n========================================\n");
  printf("Time used: %lu seconds\n", (unsigned long)(ts-tb));
  printf("Matrix memory (approx.): %zu kbytes\n", matrix_mem / 1024);
  printf("========================================\n");

  return 0;
}
