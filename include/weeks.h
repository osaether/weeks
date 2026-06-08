typedef struct {
    double w;              /* width */
    double h;              /* height */
    double x;              /* x position */
    double y;              /* y position */
    double b;              /* mesh density parameter */
    int nw;                /* number of width divisions */
    int nh;                /* number of height divisions */
    int n;                 /* total number of elements (nw * nh) */
    
    /* Dielectric material properties. The substrate *height* is NOT stored
     * here: it is the trace-to-ground separation, derived from the geometry
     * (signal y minus ground-plane top). See substrate_height() in calcl.c. */
    double er;             /* relative permittivity (dielectric constant) */
    double tan_delta;      /* loss tangent (dielectric loss) */
} conductor;

#define MAX_CONDUCTORS 10

conductor *getinput(FILE *, int *);

typedef struct {
    double x1, x2, y1, y2;
} element;

element *build_elements(int, int, conductor *, element *);

/* lp() is declared in lpp.h; the dielectric helpers in calcl.h. */
