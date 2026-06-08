/*
 * The function 'Lp' is the solution of the four-fold integral in
 * eq. (5) in W. T. Weeks et al, "Resistive and Inductive Skin Effect
 * in Rectangular Conductors", IBM J. RES. DEVELOP, Vol 23, No. 6
 * Nov. 1979.
 * 
 * It is assumed that the permeability is equal to that of free space
 * (4 * PI * 1e-7).
 *
 * No attempt have been made to optimize the calculations. The
 * calculations can be speeded up a bit by "writing out" the function
 * 'F' and combining terms.
 *
 *
 */
#include <math.h> 
#include <stdio.h>
#include "weeks.h"
#include "lpp.h"


static double F(double x, double y, double x2, double y2)
{
  if((x == 0.0) && (y == 0.0))
    return 0.0;
  else if (x == 0.0)
    return ((y2*y2)*logl(y2)/24);
  else if (y == 0.0)
    return ((x2*x2)*logl(x2)/24);
  return ((x2*x2-6*x2*y2+y2*y2)*logl(x2+y2)/24-x*y*(x2*atanl(y/x)+y2*atanl(x/y))/3);  
}

double lp(element *e1, element *e2)
{
  double temp;
  double x11, x112, x12, x122, x21, x212, x22, x222;
  double y11, y112, y12, y122, y21, y212, y22, y222;
  
  x11 = e1->x1 - e2->x1;
  x112 = x11 * x11;
  x12 = e1->x1 - e2->x2;
  x122 = x12 * x12;
  x21 = e1->x2 - e2->x1;
  x212 = x21 * x21;
  x22 = e1->x2 - e2->x2;
  x222 = x22 * x22;
  y11 = e1->y1 - e2->y1;
  y112 = y11 * y11;
  y12 = e1->y1 - e2->y2;
  y122 = y12 * y12;
  y21 = e1->y2 - e2->y1;
  y212 = y21 * y21;
  y22 = e1->y2 - e2->y2;
  y222 = y22 * y22;
  
  temp = F(x11,y11,x112,y112)-F(x11,y12,x112,y122)-F(x12,y11,x122,y112)+F(x12,y12,x122,y122)
       - F(x11,y21,x112,y212)+F(x11,y22,x112,y222)+F(x12,y21,x122,y212)-F(x12,y22,x122,y222)
       - F(x21,y11,x212,y112)+F(x21,y12,x212,y122)+F(x22,y11,x222,y112)-F(x22,y12,x222,y122)
       + F(x21,y21,x212,y212)-F(x21,y22,x212,y222)-F(x22,y21,x222,y212)+F(x22,y22,x222,y222);
  temp /= fabs((e2->x2-e2->x1)*(e2->y2-e2->y1)*(e1->x2-e1->x1)*(e1->y2-e1->y1)); 
  return (1.e-7*(temp+25.0/6.0));
}






