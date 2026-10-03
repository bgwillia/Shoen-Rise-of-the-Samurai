"""Rasterize this authored layout into terrain material weights, not road geometry."""
import numpy as np, json, math, ast
from PIL import Image
from pathlib import Path
ROOT=Path(__file__).resolve().parent
# Share the fixed layout's interpolation; no route search or route generation.
tree=ast.parse((ROOT/'build.py').read_text());ns={'math':math}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='catmull'],type_ignores=[]),'layout','exec'),ns)
N=8192;step=1500/N
mask=np.zeros((N,N,4),dtype=np.uint8)
for route in json.loads((ROOT/'layout.json').read_text())['routes']:
 pts=ns['catmull'](route['points']);channel={'main':0,'village':1,'farm':2}[route['kind']]
 for k,(a,b) in enumerate(zip(pts,pts[1:])):
  width=route['width'];radius=width*.5;shoulder=.9 if channel==0 else .4
  cx,cy=(a[0]+b[0])/2,(a[1]+b[1])/2
  if route['name']=='Village_FordLumberBranch':radius+=1.55*math.exp(-((cx+236)**2+(cy+63)**2)/220)
  pad=radius+shoulder+.6
  x0=max(0,int((min(a[0],b[0])-pad+750)/step));x1=min(N,int((max(a[0],b[0])+pad+750)/step)+1)
  y0=max(0,int((min(a[1],b[1])-pad+750)/step));y1=min(N,int((max(a[1],b[1])+pad+750)/step)+1)
  yy,xx=np.mgrid[y0:y1,x0:x1];x=(xx+.5)*step-750;y=(yy+.5)*step-750
  dx=b[0]-a[0];dy=b[1]-a[1];t=np.clip(((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy),0,1)
  d=np.hypot(x-a[0]-t*dx,y-a[1]-t*dy)
  # Continuous world-space perturbation, soft worn shoulders and faint double wheel wear.
  wav=.04*np.sin(x*.43+y*.27)+.025*np.sin(x*.91-y*.57)
  f=np.clip((radius+shoulder-d+wav)/(shoulder+.28),0,1);f=f*f*(3-2*f)
  fade=1 if channel!=2 else min(1,(len(pts)-k)/14)
  v=(f*255*fade).astype(np.uint8)
  mask[y0:y1,x0:x1,channel]=np.maximum(mask[y0:y1,x0:x1,channel],v)
  if channel==0:
   ruts=np.exp(-((d-.9)/.21)**2)*f*.7
   mask[y0:y1,x0:x1,3]=np.maximum(mask[y0:y1,x0:x1,3],(ruts*255).astype(np.uint8))
Image.fromarray(mask,'RGBA').save(ROOT/'RoadsPaths_01_surface-mask.png')
print('Saved 8192 x 8192 terrain weights')
