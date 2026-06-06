#include <stdio.h>
#include <stdlib.h>
#include "weeks.h"

element *build_elements (int M, int N, conductor *test, element *e0)
{
  int i,j,k,m;
  int nh2, nw2;
  double wl, hl, xx, dx, wt;
  double ww1, ww2, yy, dy, ht, hh1, hh2;
  element *e;

  e = (element *) calloc (M, sizeof (element));
  if (e != NULL)
    {
      m=0;
      wl = test[0].w/test[0].nw;
      hl = test[0].h/test[0].nh;
      for(j=0;j<test[0].nh;j++)
        {
          for(k=0;k<test[0].nw;k++)
            {
              if(j==0 && k==test[0].nw/2)
                {
                  /*
                  *x01 = test[0].x+wl*k;
                  *x02 = test[0].x+wl*(k+1);
                  *y01 = test[0].y;
                  *y02 = test[0].y+hl;
                  */
                  e0->x1 = test[0].x+wl*k;
                  e0->x2 = test[0].x+wl*(k+1);
                  e0->y1 = test[0].y;
                  e0->y2 = test[0].y+hl;
                }
              else
                {
                  e[m].x1 = test[0].x+wl*k;
                  e[m].x2 = test[0].x+wl*(k+1);
                  e[m].y1 = test[0].y+hl*j;
                  e[m].y2 = test[0].y+hl*(j+1);
                  m++;
                }
            }
        }
      
      for(i=1;i<=N;i++)
        {
          nh2 = test[i].nh/2;
          nw2 = test[i].nw/2;
          if (test[i].nw % 2 == 0 || test[i].nh % 2 == 0)
            fprintf(stderr, "\n  Warning: conductor %d has even nw=%d or nh=%d;"
                    " graded mesh is only symmetric for odd values\n",
                    i, test[i].nw, test[i].nh);
          xx = test[i].w/(test[i].nw * test[i].b+nw2*(1.0 - test[i].b));
          yy = test[i].h/(test[i].nh * test[i].b+nh2*(1.0 - test[i].b));
          dy = (nh2 > 0) ? yy*(1.0-test[i].b)/nh2 : 0.0;
          hh1 = 0;
          hh2 = test[i].b*yy;
          for(j=0;j<test[i].nh;j++)
            {
              dx = (nw2 > 0) ? xx*(1.0-test[i].b)/nw2 : 0.0;
              ww1 = 0;
              ww2 = test[i].b*xx;
              if (j == nh2)
                dy = -1.0*dy;
              for(k=0;k<test[i].nw;k++)
                {
                  if (k == nw2)
                    dx = -1.0*dx;
                  e[m].x1=test[i].x+ww1;
                  e[m].x2=test[i].x+ww2;
                  wt = ww2-ww1;
                  ww1 = ww2;
                  ww2 = ww2+wt+dx;
                  e[m].y1=test[i].y+hh1;
                  e[m].y2=test[i].y+hh2;
                  m++;
                }
              ht = hh2-hh1;
              hh1 = hh2;
              hh2 = hh2 + ht + dy;
            }
        }
    }
  return e;
}






