"""Reference-directed joinery and restrained exterior aging for this shrine."""
import math, random
from mathutils import Vector

def finish_shrine(env):
    mesh, beam, tube, block = (env[k] for k in ('mesh','beam','tube','block'))
    groups=env['groups']
    def tint(ob,rgb):
        color=ob.data.color_attributes.get('ArtTint') or ob.data.color_attributes.new(name='ArtTint',type='FLOAT_COLOR',domain='CORNER')
        for f in ob.data.polygons:
            k=random.uniform(.94,1.04)
            for li in f.loop_indices:color.data[li].color=(*(v*k for v in rgb),1)
        return ob
    # A visible hierarchy of bearing blocks and small projecting beam ends.
    for x in (-1.045,1.045):
        for y in (-.72,1.02):
            for zz,ww,dd in ((2.55,.24,.21),(2.66,.34,.28),(2.74,.43,.22)):
                block('Stepped shrine bracket',(x,y,zz),(ww,dd,.08),group='Joinery',bevel=.012)
            for side in (-1,1):
                beam('Short transverse bearing arm',(x,y,2.68),(x+side*.31,y,2.72),.07,.075,group='Joinery',rough=.002)
            beam('Exposed shouldered beam end',(x,y-.28,2.58),(x,y+.27,2.58),.11,.12,group='Joinery')
    # Narrow door panel framing adds inset depth; discreet forged plates stay dark.
    for sign in (-1,1):
        for x in (sign*.07,sign*.64):
            beam('Door recessed panel stile',(x,-.813,1.25),(x,-.813,2.10),.035,.025,group='Door',rough=.001)
        for z in (1.35,2.015):
            beam('Door fine panel rail',(sign*.08,-.820,z),(sign*.64,-.820,z),.030,.025,group='Door',rough=.001)
    # Local grain wear follows the hand-cut timbers; each board has its own value.
    for group in ('MainShrine','WallBoards','Door','Platform','Railing','RoofTimber','Gables','Joinery','Ridge'):
        for ob in groups.get(group,[]):
            if not ob.data.materials or 'Timber' not in ob.data.materials[0].name:continue
            k=random.uniform(.76,1.12)
            tint(ob,(k,k*.99,k*.94))
    # Hairline drying splits are visible at close range, not deep cartoon grooves.
    for x in (-1.04,1.04):
        for j in range(5):
            xx=x+random.uniform(-.047,.047);z=random.uniform(1.09,2.12);h=random.uniform(.08,.28)
            mesh('Timber fine split',[(xx,-.811,z),(xx-.0018,-.812,z+h*.45),(xx+.001,-.811,z+h),(xx+.002,-.812,z+h*.4)],[(0,1,2,3)],'Iron',group='Joinery')
    # Wear each stone nose very slightly, with a few chipped, uneven corners.
    for ob in groups.get('Steps',[]):
        if 'tread' not in ob.name:continue
        for v in ob.data.vertices:
            p=v.co
            p.z-=.013*math.exp(-p.x*p.x/.19)
            p.x+=random.uniform(-.012,.012)
            p.y+=random.uniform(-.007,.007)
        tint(ob,(random.uniform(.76,1.0),random.uniform(.78,1.0),random.uniform(.80,1.02)))
    # Thin irregular patches cling to damp joints and horizontal stone edges.
    def moss_patch(center,sx,sy,group='StoneMoss'):
        cx,cy,cz=center;n=11;vv=[(cx,cy,cz+.007)]
        for i in range(n):
            a=math.tau*i/n;r=random.uniform(.67,1.13)
            vv.append((cx+sx*r*math.cos(a),cy+sy*r*math.sin(a),cz+random.uniform(-.003,.005)))
        ob=mesh('Moss in sheltered stone joint',vv,[(0,i+1,(i+1)%n+1) for i in range(n)],'Stone',group=group)
        tint(ob,(random.uniform(.29,.43),random.uniform(.45,.59),random.uniform(.16,.24)))
    for sign in (-1,1):
        for i in range(24):
            y=random.uniform(-1.37,1.40);x=sign*random.uniform(1.37,1.62)
            moss_patch((x,y,.599+random.uniform(-.004,.005)),random.uniform(.025,.10),random.uniform(.035,.13))
        for i in range(9):
            moss_patch((random.uniform(-1.48,1.48),sign*1.38,.599),random.uniform(.045,.12),random.uniform(.025,.065))
    for i in range(5):
        y=-2.70+i*.275
        for sign in (-1,1):moss_patch((sign*random.uniform(.55,.66),y,.16*(i+1)+.004),.075,.13)
    # A few stone chips and short grass tufts root the perimeter to the village ground.
    for i in range(36):
        x=random.choice((-1,1))*random.uniform(1.78,2.45);y=random.uniform(-3.1,1.7)
        r=random.uniform(.025,.06)
        ob=block('Loose fieldstone chip',(x,y,r*.34),(r*1.6,r,r*.65),'Stone','GroundDetails',r*.18)
        tint(ob,(.75,.76,.69))
    for i in range(42):
        if i<24:
            x=random.choice((-1,1))*random.uniform(1.65,1.82);y=random.uniform(-1.6,1.58)
        else:
            x=random.choice((-1,1))*random.uniform(2.52,2.67);y=random.uniform(-3.30,1.9)
        for j in range(random.randint(4,7)):
            ang=random.uniform(0,math.tau);h=random.uniform(.06,.21);w=random.uniform(.004,.009);lean=random.uniform(.02,.10)
            q=Vector((math.cos(ang),math.sin(ang),0));r=Vector((-q.y,q.x,0));a=Vector((x,y,.005))
            verts=[a-r*w,a+r*w,a+q*lean*.4+r*w*.5+Vector((0,0,h*.55)),a+q*lean*.4-r*w*.5+Vector((0,0,h*.55)),a+q*lean+Vector((0,0,h))]
            ob=mesh('Sparse shrine verge grass',verts,[(0,1,2,3),(3,2,4)],'Timber',group='GroundDetails')
            tint(ob,(.78,1.02,.47))

