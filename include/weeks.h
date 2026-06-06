/* Modified WEEKS.H with dielectric support for MWEEKS
 * Added support for FR4 and other dielectric materials
 */

typedef struct {
    double w;              /* width */
    double h;              /* height */
    double x;              /* x position */
    double y;              /* y position */
    double b;              /* mesh density parameter */
    int nw;                /* number of width divisions */
    int nh;                /* number of height divisions */
    int n;                 /* total number of elements (nw * nh) */
    
    /* Dielectric properties (new) */
    double er;             /* relative permittivity (dielectric constant) */
    double substrate_h;    /* substrate height (distance to ground plane) */
    double tan_delta;      /* loss tangent (dielectric loss) */
} conductor;

#define MAX_CONDUCTORS 10

conductor *getinput (FILE *, int *);

typedef struct {
    double x1, x2, y1, y2;
} element;

element *build_elements (int, int, conductor *, element *);

/* lp() is declared in lpp.h; the dielectric helpers in calcl.h. */
