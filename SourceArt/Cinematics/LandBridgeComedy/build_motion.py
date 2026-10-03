import json,math
import numpy as np
from pathlib import Path
D=json.load(open('/private/tmp/cine-native-poses.json'));names=D['names'];parents=D['parents']
def norm(a):return a/max(np.linalg.norm(a),1e-10)
def mul(a,b):
 av=a[:3];bv=b[:3];return np.r_[a[3]*bv+b[3]*av+np.cross(av,bv),a[3]*b[3]-np.dot(av,bv)]
def inv(q):return q*np.array([-1,-1,-1,1])
def rot(q,v):return v+2*np.cross(q[:3],np.cross(q[:3],v)+q[3]*v)
def axis(a,t):return np.r_[norm(np.array(a))*math.sin(t/2),math.cos(t/2)]
def between(a,b):
 a=norm(a);b=norm(b);return norm(np.r_[np.cross(a,b),1+np.dot(a,b)])
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def mixq(a,b,t):
 if np.dot(a,b)<0:b=-b
 return norm(a*(1-t)+b*t)
def pose(raw):return {n:(np.array(v[0],float),np.array(v[1],float)) for n,v in raw.items()}
idle=pose(D['idle'][0]);walk=list(map(pose,D['walk']))
def descendant(n,ancestor):
 while n in parents:
  if n==ancestor:return True
  n=parents[n]
 return False
tracks={n:[[],[]] for n in names}
for frame in range(361):
 t=frame/30
 if t<4.7:
  a=walk[int(t*30)%len(walk)];blend=smooth((t-4.1)/.6)
  P={n:(a[n][0]*(1-blend)+idle[n][0]*blend,mixq(a[n][1],idle[n][1],blend)) for n in names}
 else:
  P={n:(v[0].copy(),v[1].copy()) for n,v in idle.items()}
  # Two deliberately separated thrusts with anticipation and recovery.
  pulse=0
  for start in [7.15,8.65]:
   z=t-start
   if 0<=z<.25:pulse=-.30*smooth(z/.25)
   elif .25<=z<.5:pulse=-.30+1.3*smooth((z-.25)/.25)
   elif .5<=z<.72:pulse=1
   elif .72<=z<1.15:pulse=1-smooth((z-.72)/.43)
  ready=smooth((t-6.4)/.6)*(1-.35*smooth((t-10.4)/.7))
  shift=np.array([0,27*pulse,-9*ready-5*max(pulse,0)])
  for n in names:
   if descendant(n,'pelvis'):P[n]=(P[n][0]+shift,P[n][1])
  # Counterlean torso while hips move forward; arms stay clear of the skirt.
  spine=P['spine_01'][0].copy();lean=axis([1,0,0],math.radians(22*pulse))
  for n in names:
   if descendant(n,'spine_01'):P[n]=(spine+rot(lean,P[n][0]-spine),mul(lean,P[n][1]))
  # Slightly spread arms, preserving the original articulated hand pose.
  for side,sign in [('l',-1),('r',1)]:
   bn='upperarm_'+side;pivot=P[bn][0].copy();q=axis([0,1,0],math.radians(sign*20*ready))
   for n in names:
    if descendant(n,bn):P[n]=(pivot+rot(q,P[n][0]-pivot),mul(q,P[n][1]))
  # Analytical two-bone legs: original foot positions are fixed during the gag.
  for side in ['l','r']:
   h='thigh_'+side;k='calf_'+side;f='foot_'+side
   hip=P[h][0];foot=idle[f][0].copy();oldH=idle[h][0];oldK=idle[k][0];oldF=idle[f][0]
   upper=np.linalg.norm(oldK-oldH);lower=np.linalg.norm(oldF-oldK);dv=foot-hip;dist=np.linalg.norm(dv);direction=norm(dv)
   pole=np.array([0.,1.,0.]);pole=norm(pole-direction*np.dot(pole,direction))
   along=(upper**2-lower**2+dist**2)/(2*dist);height=math.sqrt(max(0,upper**2-along**2));knee=hip+direction*along+pole*height
   q1=between(oldK-oldH,knee-hip);q2=between(oldF-oldK,foot-knee)
   for n in names:
    if descendant(n,f):P[n]=idle[n]
    elif descendant(n,k):P[n]=(knee+rot(q2,idle[n][0]-oldK),mul(q2,idle[n][1]))
    elif descendant(n,h):P[n]=(hip+rot(q1,idle[n][0]-oldH),mul(q1,idle[n][1]))
 for n in names:
  p,q=P[n];par=parents[n]
  if par in P:
   pp,pq=P[par];p=rot(inv(pq),p-pp);q=mul(inv(pq),q)
  tracks[n][0].append(p.tolist());tracks[n][1].append(q.tolist())
Path('/private/tmp/cine-tracks.json').write_text(json.dumps(tracks))
print('Generated 361 frames,',len(names),'bone tracks')
