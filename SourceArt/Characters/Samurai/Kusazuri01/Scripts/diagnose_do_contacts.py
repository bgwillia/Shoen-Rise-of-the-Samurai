"""Classify bounded Do contact outliers against each closed mesh island.

Blender --background --factory-startup --threads 2 --python-exit-code 1 \
 --python THIS -- [--baseline pre-lateral]
The default checks the maximum Do signed-nearest outlier in each final native clip.
No source or controller edits are saved.
"""
import argparse,json,sys,hashlib,math
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import review_kusazuri as r
out=r.OUTPUT
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline',choices=('final','pre-lateral'),default='final')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
suffix='' if args.baseline=='final' else '-pre-lateral'
input_report=out/('motion-validation'+suffix+'.json')
input_fixture=out/('hinge-reference-poses'+suffix+'.json')
arch=json.loads(input_report.read_text())
fixture=json.loads(input_fixture.read_text())
assert fixture['source_sha256']==arch['source_sha256']
assert fixture['motion_script_sha256']==arch['motion_script_sha256']
review=r.Review()
if args.baseline=='final':
    assert review.source_hash==arch['source_sha256']
    assert review.motion_hash==arch['motion_script_sha256']
cache={}

def islands(ob,dg):
    points,faces=r.evaluated(ob,dg)
    if ob.name not in cache:
        parent=list(range(len(points)))
        def find(a):
            while parent[a]!=a:
                parent[a]=parent[parent[a]];a=parent[a]
            return a
        for face in faces:
            for v in face[1:]:parent[find(v)]=find(face[0])
        groups={}
        for i,face in enumerate(faces):groups.setdefault(find(face[0]),[]).append(i)
        cache[ob.name]=list(groups.values())
    result=[]
    for ii,indices in enumerate(cache[ob.name]):
        selected=[faces[i] for i in indices]
        used=sorted({v for face in selected for v in face})
        lookup={old:new for new,old in enumerate(used)}
        vertices=[points[i] for i in used]
        remapped=[tuple(lookup[v] for v in face) for face in selected]
        edges={}
        for face in remapped:
            for a,b in zip(face,face[1:]+face[:1]):
                key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
        result.append({'name':ob.name,'island':ii,'tree':BVHTree.FromPolygons(vertices,remapped,all_triangles=True),
          'low':[min(v[i] for v in vertices) for i in range(3)],'high':[max(v[i] for v in vertices) for i in range(3)],
          'closed':all(n==2 for n in edges.values()),'vertices':vertices,'faces':remapped})
    return result

def point_solids(point,solids):
    candidates=[]
    for solid in solids:
        if not all(solid['low'][i]-1e-7<=point[i]<=solid['high'][i]+1e-7 for i in range(3)):continue
        tree=solid['tree'];location,normal,face,distance=tree.find_nearest(point)
        votes=[]
        for direction in (Vector((.931,.317,.177)).normalized(),Vector((-.223,.877,.425)).normalized(),Vector((.331,-.271,.904)).normalized()):
            count=0;start=point.copy()
            for _ in range(256):
                hit,_,_,_=tree.ray_cast(start,direction,10)
                if hit is None:break
                count+=1;start=hit+direction*1e-6
            votes.append(count%2)
        winding=None
        if len(set(votes))>1:
            # A ray can land on a triangulation edge. Resolve disagreements
            # with the signed solid angle of every triangle in this island.
            angles=[]
            for face in solid['faces']:
                a,b,c=(solid['vertices'][i]-point for i in face)
                denominator=(a.length*b.length*c.length+a.dot(b)*c.length+
                             b.dot(c)*a.length+c.dot(a)*b.length)
                angles.append(2*math.atan2(a.dot(b.cross(c)),denominator))
            winding=math.fsum(angles)/(4*math.pi)
        candidates.append({'object':solid['name'],'island':solid['island'],'closed':solid['closed'],
          'inside_ray_votes':votes,'winding_number_if_rays_disagree':winding,
          'inside':abs(winding)>.5 if winding is not None else bool(votes[0]),
          'surface_distance_mm':distance*1000})
    return candidates

requests=[]
for clip in arch['coverage']:
    record=max((c for c in arch['checks'] if c.get('clip')==clip),key=lambda c:c['totals']['do']['maximum_sampled_penetration_estimate_mm'])
    name=max(record['surface_intersections']['do'],key=lambda name:record['surface_intersections']['do'][name]['maximum_sampled_penetration_estimate_mm'])
    requests.append((record['pose'],[name]))
if args.baseline=='pre-lateral':
    requests=[('A_Run:29',['Kusazuri_01_Side_R_Interior']),('A_Walk:41',['Kusazuri_01_Front_Center_Trim']),('A_Run:50',['Kusazuri_01_Front_Center_Interior','Kusazuri_01_Front_Center'])]
rows=[]
for pose,names in requests:
    record=next(c for c in arch['checks'] if c['pose']==pose)
    review.apply(record)
    frozen=next(p for p in fixture['poses'] if p['pose']==pose)
    assert frozen['panels']==record['hinge_targets']['panels']
    for panel in frozen['panels']:
        review.armor.pose.bones[panel['bone']].matrix=Matrix(panel['target_blender_cm'])
        bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get()
    solids=[island for ob in review.do for island in islands(ob,dg)]
    assert all(solid['closed'] for solid in solids), 'Do containment requires closed islands'
    do_tree=r.tree_from(review.do,dg)
    for name in names:
        old=record['surface_intersections']['do'][name]
        points,faces=r.evaluated(bpy.data.objects[name],dg)
        overlaps=do_tree.overlap(BVHTree.FromPolygons(points,faces,all_triangles=True))
        vertices=sorted({v for _,f in overlaps for v in faces[f]})
        index=old['deepest_sample']['armor_vertex'];point=points[index]
        contained=[];ambiguous=0
        for v in vertices:
            candidates=point_solids(points[v],solids)
            ambiguous+=sum(len(set(x['inside_ray_votes']))>1 for x in candidates)
            inside=[x for x in candidates if x['inside']]
            if inside:contained.append({'vertex':v,'point_metres':list(points[v]),'solids':inside,'maximum_distance_to_containing_solid_surface_mm':max(x['surface_distance_mm'] for x in inside)})
        row={'pose':pose,'component':name,'reference_estimate_mm':old['maximum_sampled_penetration_estimate_mm'],
          'reference_outlier_reproduction_error_m':(point-Vector(old['deepest_sample']['point_metres'])).length,
          'reference_outlier_point_metres':list(point),'outlier_aabb_candidates':point_solids(point,solids),
          'triangle_pairs_reproduced':len(overlaps),'contact_triangle_vertices_tested':len(vertices),
          'contact_vertices_inside_any_closed_Do_solid':len(contained),'ray_disagreements_resolved_by_winding':ambiguous,
          'maximum_sampled_distance_to_containing_Do_solid_surface_mm':max((x['maximum_distance_to_containing_solid_surface_mm'] for x in contained),default=0),
          'deepest_contained_sample':max(contained,key=lambda x:x['maximum_distance_to_containing_solid_surface_mm'],default=None),
          'inside_solid_objects':sorted({x['object'] for sample in contained for x in sample['solids']})}
        rows.append(row);print('DO_SOLID_CHECK '+json.dumps(row),flush=True)
payload={'baseline':args.baseline,'command_arguments':sys.argv,'input_report':str(input_report.relative_to(r.ROOT)),'input_report_sha256':r.sha256(input_report),'input_fixture':str(input_fixture.relative_to(r.ROOT)),'input_fixture_sha256':r.sha256(input_fixture),'review_script_sha256':r.sha256(Path(r.__file__)),'source_sha256':review.source_hash,'reference_source_sha256':arch['source_sha256'],'reference_motion_script_sha256':arch['motion_script_sha256'],
 'scope':'Restore explicitly selected frozen panel targets. Final mode checks the largest Do signed-nearest outlier per native clip on matching frozen source/controller. Pre-lateral mode replays the archived four points on unchanged panel/Do geometry; tail and material edits do not alter these panels. Point reproduction error must be zero before interpreting the old comparison. Per connected closed Do island, classify contact vertices by three independent ray parity tests, resolving disagreements with closed-island signed solid-angle winding. Surface distance is per containing solid, not exact penetration of a union or unsampled triangle interiors.',
 'probe_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'probe_script':Path(__file__).read_text(),'checks':rows,'source_file_unchanged':r.sha256(review.source)==review.source_hash}
assert payload['source_file_unchanged']
assert all(row['reference_outlier_reproduction_error_m']<1e-6 for row in rows)
r.write_json(out/('do-final-outlier-solid-containment.json' if args.baseline=='final' else 'do-outlier-solid-containment.json'),payload)
print('DO_SOLID_DIAGNOSTIC_COMPLETE',flush=True)
