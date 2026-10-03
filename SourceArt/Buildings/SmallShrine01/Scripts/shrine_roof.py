"""The priority reference's long-eave shrine roof, authored in metres."""
import math, random
from mathutils import Vector

def build_roof(env):
    mesh, beam, tube, block=(env[k] for k in ('mesh','beam','tube','block'))
    ridge_y=.24
    # A high compact ridge and restrained sweep; the long face shelters the entry.
    def point(side,t,x):
        run=2.15 if side<0 else 1.38
        drop=1.26 if side<0 else 1.20
        y=ridge_y+side*run*t
        z=3.92-(drop+.55)*t+.55*t*t+.018*(abs(x)/1.82)**5*t
        return Vector((x,y,z))
    def solid_band(name,side,t0,t1,lift,thickness,group,edge_variation=.0):
        # One continuous strip per course: no separate curled tile sheets.
        nx=84;nt=4;verts=[];uv=[]
        for lower in (0,1):
            for j in range(nt+1):
                t=t0+(t1-t0)*j/nt
                for i in range(nx+1):
                    x=-1.82+3.64*i/nx
                    p=point(side,t,x)
                    ripple=.005*math.sin(x*17+side*.7)+.004*math.sin(x*33+t*10)
                    p.z+=lift-thickness*lower+ripple+(.018*j/nt if group=='RoofCourses' else 0)
                    if j==nt:
                        p.y+=side*edge_variation*(.6*math.sin(x*43)+.4*math.sin(x*73))
                    verts.append(p);uv.append((x*1.28,(2.15 if side<0 else 1.38)*t*1.7))
        rows=nx+1;n=(nt+1)*rows;faces=[]
        for j in range(nt):
            for i in range(nx):
                k=j*rows+i;faces.append((k,k+1,k+rows+1,k+rows));faces.append((n+k+rows,n+k+rows+1,n+k+1,n+k))
        for i in range(nx):
            faces.append((i+1,i,n+i,n+i+1));k=nt*rows+i;faces.append((k,k+1,n+k+1,n+k))
        for j in range(nt):
            a=j*rows;b=(j+1)*rows;faces.append((a,b,n+b,n+a))
            a=j*rows+nx;b=(j+1)*rows+nx;faces.append((b,a,n+a,n+b))
        ob=mesh(name,verts,faces,'Thatch',uv,group)
        for f in ob.data.polygons:f.use_smooth=f.index<nt*nx*2
        return ob
    for side in (-1,1):
        # Thick layered base is fully closed on every eave and gable edge.
        solid_band('Dense thatched roof body',side,0,1,.07,.16,'Roof',.008)
        rows=18 if side<0 else 13
        for row in range(rows):
            # Upper courses overlap down the pitch and carry a clear cut lower edge.
            t0=row/rows;t1=min(1.006,(row+1.20)/rows)
            solid_band('Overlapping horizontal roof course',side,t0,t1,.093,.034,'RoofCourses',.009)
        # Layered cut reeds form the thick eave rather than a thin fascia texture.
        run=2.15 if side<0 else 1.38
        for i in range(195):
            x=-1.82+3.64*(i+random.random()*.4)/195
            for j in range(2):
                p=point(side,1,x);p.z+=random.uniform(-.065,.086);p.y+=side*random.uniform(.005,.016)
                q=p+Vector((random.uniform(-.002,.002),-side*random.uniform(.025,.07),.015))
                tube('Fine cut thatch end',[q,p],random.uniform(.0017,.0028),'Thatch','RoofEdgeReeds',5)
        # Distinct slim exposed rafter tails, aligned with the roof slope.
        for i in range(15):
            x=-1.68+i*.24
            pts=[point(side,j/24,x)-Vector((0,0,.14)) for j in range(25)]
            tube('Curved shrine rafter',pts,.039,'Timber','RoofTimber',4)
        a=point(side,.965,-1.89);b=point(side,.965,1.89);a.z-=.15;b.z-=.15
        beam('Long eave under fascia',a,b,.085,.115,group='RoofTimber',rough=.002)
    # Side bargeboards trace both pitches, with real depth and softened joinery.
    for sign in (-1,1):
        x=sign*1.84
        for side in (-1,1):
            vv=[];ff=[];uv=[]
            for i in range(33):
                t=i/32;p=point(side,t,x)
                for dx,dz in [(-.040,-.13),(.040,-.13),(.040,.026),(-.040,.026)]:
                    vv.append((p.x+dx,p.y,p.z+dz));uv.append((dx*2+.3,t*2.5))
            for i in range(32):
                for j in range(4):ff.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
            ff += [(3,2,1,0),tuple(range(128,132))]
            ob=mesh('Side gable layered verge',vv,ff,'Timber',uv,'RoofTimber')
            bevel=ob.modifiers.new('Worn verge edges','BEVEL');bevel.width=.006;bevel.segments=2
            normal=ob.modifiers.new('Verge broad faces','WEIGHTED_NORMAL');normal.keep_sharp=True
            tube('Lower side verge',[(p.x,p.y,p.z-.195) for p in [point(side,i/32,x) for i in range(33)]],.032,'Timber','RoofTimber',6)
        # Recessed cedar boards fill the side gable above the structural tie.
        gx=sign*1.09
        for i in range(20):
            y=-.73+i*.094
            side=-1 if y<ridge_y else 1
            t=abs(y-ridge_y)/(2.15 if side<0 else 1.38)
            z=point(side,t,gx).z-.16
            beam('Side gable fitted cedar board',(gx,y,2.62),(gx,y,z),.05,.091,group='Gables',rough=.001)
        beam('Side gable principal tie',(gx,-.89,2.74),(gx,1.16,2.74),.14,.14,group='Gables')
        beam('Side gable king post',(gx,ridge_y,2.69),(gx,ridge_y,3.86),.13,group='Gables')
        beam('Side gable collar',(gx,-.49,3.23),(gx,.87,3.23),.075,.09,group='Gables')
        for side in (-1,1):
            beam('Side gable angled brace',(gx,ridge_y,2.83),(gx,ridge_y+side*.51,3.35),.065,.065,group='Gables')
        # Bearer ends step beneath the side overhang; no unsupported floating roof.
        for y in (-.72,1.02):
            for z,w in [(2.65,.25),(2.75,.34)]:block('Gable bracket capital',(gx,y,z),(w,.23,.085),group='RoofTimber',bevel=.009)
            beam('Side overhang bearing arm',(sign*.97,y,2.72),(sign*1.69,y,2.76),.105,.115,group='RoofTimber')
    # Crown: dense thatch roll held between two stacked weathered curb timbers.
    tube('Ridge thatch roll',[(-1.80,ridge_y,3.99),(0,ridge_y,4.02),(1.80,ridge_y,3.99)],.14,'Thatch','Ridge',16)
    for y,z,w,d in [(ridge_y-.17,4.02,.10,.15),(ridge_y+.17,4.02,.10,.15),(ridge_y,4.10,.20,.12)]:
        beam('Stacked ridge timber',(-1.91,y,z),(1.91,y,z),w,d,group='Ridge',rough=.003)
    for x in (-1.26,-.63,0,.63,1.26):
        tube('Katsuogi ridge cross log',[(x,ridge_y-.40,4.15),(x,ridge_y,4.17),(x,ridge_y+.40,4.15)],.074,'Timber','Ridge',12)
        # Two coarse binding loops; fine rope texture comes from the village maps.
        for yy in (ridge_y-.24,ridge_y+.24):
            pts=[(x+.074*math.cos(i*math.tau/24),yy+.015*i/24,4.16+.074*math.sin(i*math.tau/24)) for i in range(25)]
            tube('Ridge lashing',pts,.009,'Rope','Ridge',6)
    for x in (-1.50,1.50):
        for side in (-1,1):
            beam('Crossed shrine chigi',(x,ridge_y-side*.23,3.94),(x,ridge_y+side*.43,4.62),.09,.08,group='Ridge',rough=.001)
    env['roof_reference_note']='Long-eave entrance and side gables follow the primary reference 3/4 view.'
