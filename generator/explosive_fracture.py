"""Qualitative full-scene composite fracture candidate with independently moving fragments.

This fixed illustrative construction is not a calibrated material, fracture,
contact, or fluid solver. Source video_0026 supplies an event reference, but
its small/obscured specimen does not reveal individual fragment trajectories.
Run: Blender --background -t 2 --python-exit-code 1 --python generator/explosive_fracture.py -- --out DIR --render
"""
import argparse
import hashlib
import json
import math
import random
import struct
import sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

VERSION = 'composite-explosive-candidate/0.1.0'
p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
p.add_argument('--render', action='store_true')
p.add_argument('--checks-only', action='store_true')
p.add_argument('--render-frames', help='comma-separated one-based diagnostic frame numbers')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
selected = sorted({int(x) for x in a.render_frames.split(',')}) if a.render_frames else None
if selected and not all(1 <= x <= 600 for x in selected):
    p.error('frames must lie within 1..600')
if a.render and selected:
    p.error('choose --render or --render-frames')
out = Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
FPS, FRAMES, EVENT, NROWS, NCOLS = 30, 600, 451, 6, 7
WIDTH, THICKNESS, LOWER, UPPER, FREE = .92, .14, -2.42, 2.42, 1.68
TRAVEL = .08
BASE_TOP = -3.595
SEED = 1625
rng = random.Random(SEED)


def smooth(x):
    x = max(0., min(1., x))
    return x*x*(3.-2.*x)


def clip(poly, aa, bb, cc):
    result = []
    for x, y in zip(poly, poly[1:]+poly[:1]):
        fx = aa*x[0]+bb*x[1]-cc
        fy = aa*y[0]+bb*y[1]-cc
        ix, iy = fx <= 1e-12, fy <= 1e-12
        if ix:
            result.append(x)
        if ix != iy:
            t = fx/(fx-fy)
            result.append((x[0]+t*(y[0]-x[0]), x[1]+t*(y[1]-x[1])))
    return result


def area_centroid(poly):
    cross = [x[0]*y[1]-y[0]*x[1] for x, y in zip(poly, poly[1:]+poly[:1])]
    area = sum(cross)/2
    assert area > 1e-10
    cx = sum((x[0]+y[0])*k for x, y, k in zip(poly, poly[1:]+poly[:1], cross))/(6*area)
    cz = sum((x[1]+y[1])*k for x, y, k in zip(poly, poly[1:]+poly[:1], cross))/(6*area)
    return area, (cx, cz)


# The cells tile exactly the authored gauge volume before fracture. They are
# mathematical polygons, not a claim about real plies or fragment count.
zlo, zhi = -FREE, FREE+TRAVEL
midz = (zlo+zhi)/2
sites = []
for row in range(NROWS):
    for col in range(NCOLS):
        x = -WIDTH/2 + WIDTH*(col+.5+rng.uniform(-.46, .46))/NCOLS
        z = zlo + (zhi-zlo)*(row+.5+rng.uniform(-.46, .46))/NROWS
        sites.append((x, z))
Z_METRIC = .29
polys = []
for i, (x, z) in enumerate(sites):
    poly = [(-WIDTH/2, zlo), (WIDTH/2, zlo), (WIDTH/2, zhi), (-WIDTH/2, zhi)]
    for j, (u, v) in enumerate(sites):
        if i == j:
            continue
        poly = clip(poly, 2*(u-x), 2*Z_METRIC**2*(v-z), u*u-x*x+Z_METRIC**2*(v*v-z*z))
    assert len(poly) >= 3
    area, centre = area_centroid(poly)
    row, col = divmod(i, NCOLS)
    depth_group = (2*row+col)%12
    y_lane = (depth_group-5.5)*.37
    polys.append({'polygon': poly, 'area': area, 'centre': centre, 'site': (x, z),
                  'angle': rng.uniform(-1.45, 1.45), 'colour': rng.randrange(4),
                  'x_jitter': rng.uniform(-.32,.32),
                  'y_destination': y_lane+math.copysign(.35,y_lane)+rng.uniform(-.008,.008),
                  'z_drift': .12*(z-midz)+rng.uniform(-.75,.75),
                  'fall_start': .30+rng.uniform(-.06,.12)})
assert abs(sum(x['area'] for x in polys)-WIDTH*(zhi-zlo)) < 1e-8


def vertex_key(v):
    return tuple(round(x,8) for x in v)


def polygon_edges(poly):
    return {tuple(sorted((vertex_key(a),vertex_key(b)))) for a,b in zip(poly,poly[1:]+poly[:1])}


# Keep all cells touching a grip-side end attached as irregular residuals.
# A small connected central set is retained as a larger free segment, so the
# hypothetical failure is not a sheet of uniformly sized tiles.
lower_ids=[i for i,q in enumerate(polys) if sum(abs(v[1]-zlo)<1e-8 for v in q['polygon'])>=2]
upper_ids=[i for i,q in enumerate(polys) if sum(abs(v[1]-zhi)<1e-8 for v in q['polygon'])>=2]
assert lower_ids and upper_ids and not set(lower_ids)&set(upper_ids)
inner=set(range(len(polys)))-set(lower_ids)-set(upper_ids)
edges=[polygon_edges(q['polygon']) for q in polys]
seed=min(inner,key=lambda i:abs(polys[i]['centre'][0])+.3*abs(polys[i]['centre'][1]-midz))
central=[seed]
while len(central)<4:
    neighbours=[i for i in inner-set(central) if any(edges[i]&edges[j] for j in central)]
    assert neighbours
    central.append(min(neighbours,key=lambda i:abs(polys[i]['centre'][0])+.3*abs(polys[i]['centre'][1]-midz)))


def merge_piece(ids):
    area=sum(polys[i]['area'] for i in ids)
    centre=tuple(sum(polys[i]['centre'][axis]*polys[i]['area'] for i in ids)/area for axis in [0,1])
    site=tuple(sum(polys[i]['site'][axis]*polys[i]['area'] for i in ids)/area for axis in [0,1])
    base=dict(polys[ids[0]])
    base.update({'tiles':[polys[i]['polygon'] for i in ids],'source_cell_ids':ids,'area':area,'centre':centre,'site':site})
    return base


pieces=[merge_piece(central)]+[merge_piece([i]) for i in sorted(inner-set(central))]
lower_tiles=[polys[i]['polygon'] for i in lower_ids]
upper_tiles=[polys[i]['polygon'] for i in upper_ids]

CONFIG = {
    'implementation_version': VERSION, 'output_purpose': 'full_scene_candidate',
    'applicability': 'one qualitative composite-strip candidate inspired by a high-rate tensile experiment; display loading is not rate-calibrated',
    'reference_source_id': 'video_0026', 'source_event_boundary_frames_zero_based': [336, 337],
    'material_visual_reference': {'authors':'Zhang et al.','figure':19,'test':'CFRP/epoxy tensile test, 234 s^-1',
        'url':'https://curate.curtin.edu.au/articles/journal_contribution/Static_and_dynamic_material_properties_of_CFRP_epoxy_laminates/31607107',
        'scope':'selected high-speed experiment frames provide qualitative visible failure evidence; not quantitative fragment trajectories or the loading conditions in video_0026'},
    'duration_s': 20, 'fps': FPS, 'frames': FRAMES, 'resolution': [1280, 720],
    'frame_timestamp_convention': 'time_s=(frame-1)/30', 'units': 'dimensionless author coordinates',
    'specimen_width': WIDTH, 'specimen_thickness': THICKNESS,
    'initial_specimen_endpoints_z': [LOWER, UPPER], 'gauge_partition_z': [zlo, zhi],
    'loading_end': 'upper', 'fixed_end': 'lower', 'upper_jaw_travel': TRAVEL,
    'last_intact_frame_one_based': EVENT, 'last_intact_time_s': (EVENT-1)/FPS,
    'first_partitioned_frame_one_based': EVENT+1, 'first_partitioned_time_s': EVENT/FPS,
    'fragment_seed': SEED, 'fragment_count_authored': len(pieces),
    'fragment_partition': 'Voronoi cells tile the free volume; boundary cells stay with grips and four connected inner cells form a larger free segment; all geometry is authored',
    'fragment_initial_and_final_sites': [{'source_cell_ids':q['source_cell_ids'],'site': q['site'], 'centre': q['centre'], 'area': q['area'], 'angle_rad': q['angle'], 'x_jitter':q['x_jitter'], 'y_destination':q['y_destination'], 'vertical_initial_velocity':q['z_drift']} for q in pieces],
    'motion': {'release_response_s': .055, 'lateral_site_multiplier': 3.5, 'lateral_direction_offset': .85,
               'rotation_start_s': .04, 'rotation_duration_s': .55, 'fall_start_s': 0, 'gravity_dimensionless': 2.7,
               'settling_model': 'prescribed kinematics and simplified vertical supports; not rigid-body dynamics'},
    'jaws': {'initial_centres_z': [-2.25, 2.25], 'inner_x_planes': [-WIDTH/2, WIDTH/2],
             'side_block_dimensions': [.30,.42,.50], 'cap_dimensions': [1.32,.70,.14]},
    'camera': {'projection': 'orthographic', 'position': [0,-25,0], 'target': [0,0,0], 'ortho_scale': 15.0},
    'renderer': 'BLENDER_WORKBENCH', 'parameter_range_accepted': False,
    'limitations': ['fragment count, shapes, three-dimensional motion and simulated timing are author-defined',
                    'reference frame contains motion blur, instrumentation and unclear individual fragment identities',
                    'source high-rate loading is not reproduced; 20 s presentation and fragment velocities are authored',
                    'no constitutive, contact-force, inertia, air, or fracture propagation solver',
                    '2D convex projection overlap and fixture slab checks are not a general swept 3D collision solver',
                    'video_0026 belongs to fold_0_train, fold_1_train and fold_2_val; model-specific exposure and licensing unknown',
                    'no ROI processing or model inference']}

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
s = bpy.context.scene
s.render.engine = 'BLENDER_WORKBENCH'
s.render.resolution_x, s.render.resolution_y = 1280, 720
s.render.resolution_percentage = 100
s.render.fps = FPS
s.frame_start, s.frame_end = 1, FRAMES
s.render.image_settings.file_format = 'PNG'
s.display.render_aa = '8'
sh = s.display.shading
sh.light = 'STUDIO'
sh.studio_light = 'paint.sl'
sh.color_type = 'MATERIAL'
sh.show_shadows = True
sh.show_cavity = True
sh.cavity_type = 'BOTH'
sh.show_specular_highlight = True
sh.background_type = 'WORLD'
s.world.color = (.56,.59,.63)
s.view_settings.view_transform = 'Standard'


def material(name, colour):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*colour, 1)
    return m


specmats = [material('authored composite shade '+str(i), (.065+i*.009,.074+i*.009,.080+i*.009)) for i in range(4)]
steel = material('light gray steel', (.66,.69,.70))
frame_mat = material('machine frame', (.32,.36,.39))
dark = material('jaw fasteners', (.13,.15,.16))


def box(name, location, dimensions, mat, bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new('rounded edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        obj.modifiers.new('weighted normals', 'WEIGHTED_NORMAL')
    return obj


jaws, caps, rods, jaw_fixtures = {}, {}, {}, []
for end, sign in [('lower',-1),('upper',1)]:
    z = sign*2.25
    for side in [-1,1]:
        jaw = box(f'{end} jaw {side}', (side*(WIDTH/2+.15),0,z), (.30,.42,.50), steel)
        jaws[(end,side)] = jaw
        jaw_fixtures.append((jaw,end))
        screw = box(f'{end} jaw screw {side}', (side*(WIDTH/2+.41),-.03,z), (.22,.25,.16), dark,.035)
        jaw_fixtures.append((screw,end))
    caps[end] = box(end+' jaw holder', (0,.02,z+sign*.32), (1.32,.70,.14), steel)
    rods[end] = box(end+' transmission rod', (0,.02,z+sign*.70), (.32,.40,.60), frame_mat)
machine = [box('upper machine beam',(0,.20,3.72),(9.0,.70,.25),frame_mat),
           box('lower machine beam and support surface',(0,.20,-3.72),(9.0,5.50,.25),frame_mat)]
for x in [-4.35,4.35]:
    machine.append(box('machine column '+str(x),(x,.20,0),(.30,.55,7.32),frame_mat))
machine.append(box('machine base',(0,.20,-3.99),(9.55,5.70,.24),steel))
bpy.ops.object.camera_add(location=(0,-25,0))
cam = bpy.context.object
cam.rotation_euler = (Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 15.0
s.camera = cam


collision_loops={}


def union_prism_mesh(name, polys_2d, depth, mat):
    coordinates=[]; lookup={}; loops=[]; edge_counts={}
    for poly in polys_2d:
        loop=[]
        for point in poly:
            key=vertex_key(point)
            if key not in lookup:
                lookup[key]=len(coordinates);coordinates.append(key)
            loop.append(lookup[key])
        assert len(set(loop))==len(loop)
        loops.append(loop)
        for left,right in zip(loop,loop[1:]+loop[:1]):
            key=tuple(sorted((left,right)));edge_counts[key]=edge_counts.get(key,0)+1
    verts=[]
    for x,z in coordinates:
        verts.extend([(x,-depth/2,z),(x,depth/2,z)])
    faces=[]
    for loop in loops:
        faces.append(tuple(2*i for i in reversed(loop)))
        faces.append(tuple(2*i+1 for i in loop))
    for (left,right),count in edge_counts.items():
        assert count in (1,2)
        if count==1:
            # Choose boundary orientation from its owning polygon.
            direction=next((a,b) for loop in loops for a,b in zip(loop,loop[1:]+loop[:1]) if {a,b}=={left,right})
            a,b=direction;faces.append((2*a,2*b,2*b+1,2*a+1))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name,mesh)
    s.collection.objects.link(obj)
    collision_loops[name]=[[2*i for i in loop] for loop in loops]
    return obj


def rect(z0,z1):
    return [(-WIDTH/2,z0),(WIDTH/2,z0),(WIDTH/2,z1),(-WIDTH/2,z1)]

lower_x=sorted({vertex_key(v)[0] for poly in lower_tiles for v in poly if abs(v[1]-zlo)<1e-8}|{-WIDTH/2,WIDTH/2})
upper_x=sorted({vertex_key(v)[0] for poly in upper_tiles for v in poly if abs(v[1]-zhi)<1e-8}|{-WIDTH/2,WIDTH/2})
lower_base=[(-WIDTH/2,LOWER),(WIDTH/2,LOWER)]+[(x,zlo) for x in reversed(lower_x)]
upper_base=[(x,zhi) for x in upper_x]+[(WIDTH/2,UPPER+TRAVEL),(-WIDTH/2,UPPER+TRAVEL)]
intact = union_prism_mesh('intact connected specimen', [rect(LOWER,UPPER)], THICKNESS, specmats[0])
lower_stump = union_prism_mesh('lower retained specimen', [lower_base]+lower_tiles, THICKNESS, specmats[0])
upper_stump = union_prism_mesh('upper retained specimen', [upper_base]+upper_tiles, THICKNESS, specmats[0])
fragments = []
for i, q in enumerate(pieces):
    cx, cz = q['centre']
    local = [[(x-cx,z-cz) for x,z in tile] for tile in q['tiles']]
    obj = union_prism_mesh('specimen fragment %02d'%i, local, THICKNESS, specmats[q['colour']])
    fragments.append(obj)


def dimensions(obj, depgraph):
    ev = obj.evaluated_get(depgraph)
    mesh = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in mesh.vertices]
    ev.to_mesh_clear()
    return [[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)]


def rotated_local(q, angle):
    cx,cz=q['centre']; co,si=math.cos(angle),math.sin(angle)
    return [((x-cx)*co+(z-cz)*si, -(x-cx)*si+(z-cz)*co) for tile in q['tiles'] for x,z in tile]


# Final support heights conservatively stack the authored pieces by x bounds.
# They are prescribed display positions, not contact dynamics.
final_shapes=[]
for q in pieces:
    x,z=q['centre']; site_x,site_z=q['site']
    dx=3.5*site_x + (.85 if site_x>=0 else -.85)+q['x_jitter']
    angle=q['angle']; local=rotated_local(q,angle)
    final_shapes.append({'x':x+dx,'y':q['y_destination'],'z':z, 'local':local,
        'left':x+dx+min(pt[0] for pt in local),'right':x+dx+max(pt[0] for pt in local),
        'low':min(pt[1] for pt in local),'high':max(pt[1] for pt in local)})
for i in sorted(range(len(pieces)), key=lambda n:final_shapes[n]['z']):
    q=final_shapes[i]
    bottom=BASE_TOP+2e-6
    for other in final_shapes:
        if 'settled_top' in other and abs(q['y']-other['y']) < THICKNESS+1e-6 and q['left'] < other['right']+.015 and q['right'] > other['left']-.015:
            bottom=max(bottom,other['settled_top']+2e-6)
    q['settled_center_z'] = bottom-q['low']
    q['settled_top'] = q['settled_center_z']+q['high']
    assert q['settled_center_z'] < q['z']


def update(frame):
    t=(frame-1)/FPS
    elapsed=max(0.,(frame-EVENT)/FPS)
    travel=TRAVEL*smooth(min(frame-1, EVENT-1)/(EVENT-1))
    fractured=frame>EVENT
    intact.hide_render=fractured
    intact.hide_viewport=fractured
    lower_stump.hide_render=not fractured
    lower_stump.hide_viewport=not fractured
    upper_stump.hide_render=not fractured
    upper_stump.hide_viewport=not fractured
    for obj in fragments:
        obj.hide_render=not fractured
        obj.hide_viewport=not fractured
    # Only the pre-fracture intact body is stretched. Endpoints are authored;
    # actual volume and jaw contacts are measured below.
    intact.scale.z=(UPPER-LOWER+travel)/(UPPER-LOWER)
    intact.location.z=LOWER-LOWER*intact.scale.z
    for obj,end in jaw_fixtures:
        obj.location.z=-2.25 if end=='lower' else 2.25+travel
    caps['lower'].location.z=-2.57
    caps['upper'].location.z=2.57+travel
    for end,lo,hi in [('lower',-3.595,-2.64),('upper',2.64+travel,3.595)]:
        rods[end].location.z=(lo+hi)/2
        rods[end].scale.z=(hi-lo)/.60
    sep=1-math.exp(-elapsed/.055)
    rotp=smooth((elapsed-.04)/.55)
    for obj,q,target in zip(fragments,pieces,final_shapes):
        cx,cz=q['centre']; sx,sz=q['site']
        dx=(3.5*sx+(.85 if sx>=0 else -.85)+q['x_jitter'])*sep
        # A slight upward/downward component after clearing the held ends is
        # only a visual authored motion, not a measured release velocity.
        drift=q['z_drift']*elapsed
        fall=.5*2.7*elapsed**2
        obj.location=(cx+dx,q['y_destination']*sep,max(cz+drift-fall,target['settled_center_z']))
        obj.rotation_euler=(0,q['angle']*rotp,0)
    s.frame_set(frame)
    return t,travel,sep


def polygon(obj, dg):
    ev=obj.evaluated_get(dg);m=ev.to_mesh()
    pts=[ev.matrix_world@v.co for v in m.vertices]
    # Each recorded loop is a convex tile; an irregular connected residual
    # can contain several tiles with shared actual mesh vertices.
    loops=[[(float(pts[i].x),float(pts[i].z)) for i in loop] for loop in collision_loops[obj.name]]
    poly=[v for loop in loops for v in loop]
    m.calc_loop_triangles()
    vol=abs(sum(pts[t.vertices[0]].dot(pts[t.vertices[1]].cross(pts[t.vertices[2]]))/6 for t in m.loop_triangles))
    edgecounts={}
    for face in m.polygons:
        vs=list(face.vertices)
        for x,y in zip(vs,vs[1:]+vs[:1]):
            k=tuple(sorted((x,y)));edgecounts[k]=edgecounts.get(k,0)+1
    # Measure actual mesh graph components, not configured object count.
    adj=[[] for _ in m.vertices]
    for edge in m.edges:
        x,y=edge.vertices;adj[x].append(y);adj[y].append(x)
    seen=set(); components=0
    for i in range(len(adj)):
        if i in seen:continue
        components+=1;seen.add(i);todo=[i]
        while todo:
            k=todo.pop()
            for v in adj[k]:
                if v not in seen:seen.add(v);todo.append(v)
    minimum_area=min(face.area for face in m.polygons)
    result={'name':obj.name,'poly':poly,'loops':loops,'points':pts,'volume':vol,'components':components,
            'closed':all(v==2 for v in edgecounts.values()),'min_area':minimum_area}
    ev.to_mesh_clear()
    return result


def sat(a,b):
    # Exact in the x/z plane for the convex extrusions used here. Returns
    # a separating gap (>0) or the negative minimum overlap (<0).
    min_overlap=float('inf');max_gap=0.
    for poly in (a,b):
        for p,q in zip(poly,poly[1:]+poly[:1]):
            dx,dz=q[0]-p[0],q[1]-p[1]
            length=math.hypot(dx,dz)
            nx,nz=-dz/length,dx/length
            pa=[x*nx+z*nz for x,z in a];pb=[x*nx+z*nz for x,z in b]
            overlap=min(max(pa),max(pb))-max(min(pa),min(pb))
            if overlap<0:max_gap=max(max_gap,-overlap)
            else:min_overlap=min(min_overlap,overlap)
    return max_gap if max_gap>0 else -min_overlap


def bounds2(poly):
    return [min(x for x,z in poly),max(x for x,z in poly),min(z for x,z in poly),max(z for x,z in poly)]


def bounds_overlap(a,b,eps=1e-7):
    return not (a[1]<b[0]-eps or b[1]<a[0]-eps or a[3]<b[2]-eps or b[3]<a[2]-eps)


def measure(frame):
    t,travel,sep=update(frame)
    dg=bpy.context.evaluated_depsgraph_get();dg.update()
    active=[intact] if frame<=EVENT else [lower_stump,upper_stump]+fragments
    bodies=[polygon(obj,dg) for obj in active]
    all_pts=[p for b in bodies for p in b['points']]
    component_count=sum(b['components'] for b in bodies)
    path_across=any(min(v.z for v in b['points'])< -2.0 and max(v.z for v in b['points'])>2.0+travel for b in bodies)
    overlap=[];minimum_gap=None; checks=0; contact_edges=[]
    for i,b in enumerate(bodies):
        for j,c in enumerate(bodies[i+1:],i+1):
            if not bounds_overlap(bounds2(b['poly']),bounds2(c['poly'])):continue
            ya=[v.y for v in b['points']];yb=[v.y for v in c['points']]
            ygap=max(min(ya)-max(yb),min(yb)-max(ya))
            if ygap>1e-6:continue
            gaps=[max(sat(bl,cl),ygap) for bl in b['loops'] for cl in c['loops'] if bounds_overlap(bounds2(bl),bounds2(cl))]
            if not gaps:continue
            gap=min(gaps);checks+=len(gaps)
            minimum_gap=gap if minimum_gap is None else min(minimum_gap,gap)
            if gap< -1e-6:overlap.append([b['name'],c['name'],gap])
            if gap<=1e-6:contact_edges.append((i,j))
    contact_path=path_across
    if frame>EVENT:
        neighbours=[set() for _ in bodies]
        for i,j in contact_edges:neighbours[i].add(j);neighbours[j].add(i)
        seen={0};todo=[0]
        while todo:
            i=todo.pop()
            for j in neighbours[i]:
                if j not in seen:seen.add(j);todo.append(j)
        contact_path=1 in seen
    fixtures=[]
    fixture_objects=[obj for obj,end in jaw_fixtures]+list(caps.values())+list(rods.values())+machine
    for obj in fixture_objects:
        bb=dimensions(obj,dg)
        fixtures.append((obj.name,[(bb[0][0],bb[2][0]),(bb[0][1],bb[2][0]),(bb[0][1],bb[2][1]),(bb[0][0],bb[2][1])],bb[1]))
    fixture_overlap=[]
    for b in bodies:
        for name,rectpoly,yrange in fixtures:
            if bounds_overlap(bounds2(b['poly']),bounds2(rectpoly)):
                ys=[v.y for v in b['points']]
                ygap=max(min(ys)-yrange[1],yrange[0]-max(ys))
                gaps=[max(sat(loop,rectpoly),ygap) for loop in b['loops'] if bounds_overlap(bounds2(loop),bounds2(rectpoly))]
                if gaps and min(gaps)< -1e-6:fixture_overlap.append([b['name'],name,min(gaps)])
    cap_clearance=min(min(v.z for v in all_pts)-(-2.50), (2.50+travel)-max(v.z for v in all_pts)) if frame<=EVENT else None
    lower=next(b for b in bodies if b['name'] in ('lower retained specimen','intact connected specimen'))
    upper=next(b for b in bodies if b['name'] in ('upper retained specimen','intact connected specimen'))
    def held_contact(body,end):
        left=dimensions(jaws[(end,-1)],dg);right=dimensions(jaws[(end,1)],dg)
        zlo=max(left[2][0],right[2][0]);zhi=min(left[2][1],right[2][1])
        ylo=max(left[1][0],right[1][0]);yhi=min(left[1][1],right[1][1])
        embedded=[v for v in body['points'] if zlo-1e-7<=v.z<=zhi+1e-7 and ylo-1e-7<=v.y<=yhi+1e-7]
        return bool(embedded) and abs(min(v.x for v in embedded)-left[0][1])<2e-6 and abs(max(v.x for v in embedded)-right[0][0])<2e-6
    lower_contact=held_contact(lower,'lower')
    upper_contact=held_contact(upper,'upper')
    support_bounds=dimensions(machine[1],dg)
    support_gaps=[]
    if frame>EVENT:
        for b in bodies[2:]:
            pts=b['points']
            within=all(support_bounds[0][0]-1e-6<=v.x<=support_bounds[0][1]+1e-6 and support_bounds[1][0]-1e-6<=v.y<=support_bounds[1][1]+1e-6 for v in pts)
            support_gaps.append(min(v.z for v in pts)-support_bounds[2][1] if within else None)
    projected=[world_to_camera_view(s,cam,v) for v in all_pts]
    for obj in fixture_objects:
        ev=obj.evaluated_get(dg);m=ev.to_mesh();projected += [world_to_camera_view(s,cam,ev.matrix_world@v.co) for v in m.vertices];ev.to_mesh_clear()
    box=[min(p.x for p in projected),max(p.x for p in projected),min(p.y for p in projected),max(p.y for p in projected)]
    h=hashlib.sha256()
    for b in bodies:
        for v in b['points']:h.update(struct.pack('<ddd',v.x,v.y,v.z))
    return {'frame':frame,'time_s':t,'author_separation_progress':sep,'upper_jaw_travel':travel,
            'components_measured':component_count,'mesh_path_between_jaws':path_across,'material_contact_path_between_jaws':contact_path,
            'all_meshes_closed_and_nondegenerate':all(b['closed'] and b['min_area']>0 for b in bodies),
            'actual_volume':sum(b['volume'] for b in bodies),'actual_mesh_hash':h.hexdigest(),
            'lower_jaw_contact':lower_contact,'upper_jaw_contact':upper_contact,
            'overlapping_material_pairs':overlap,'overlapping_fixture_pairs':fixture_overlap,
            'pair_projection_tests':checks,'minimum_candidate_pair_gap':minimum_gap,
            'fragment_support_gaps':support_gaps,
            'min_material_z':min(v.z for v in all_pts),'max_material_z':max(v.z for v in all_pts),
            'same_specimen_length_pre_event':max(v.z for v in all_pts)-min(v.z for v in all_pts) if frame<=EVENT else None,
            'same_section_area_pre_event':(max(v.x for v in all_pts)-min(v.x for v in all_pts))*(max(v.y for v in all_pts)-min(v.y for v in all_pts)) if frame<=EVENT else None,
            'all_specimen_and_machine_in_frame':all(0<=v<=1 for v in box),'projected_bounds':box}

frames=selected or (range(1,FRAMES+1) if (a.render or a.checks_only) else [1,301,450,451,452,453,454,457,466,481,511,541,600])
rows=[]
for f in frames:
    r=measure(f);rows.append(r)
    assert r['all_meshes_closed_and_nondegenerate'] and r['lower_jaw_contact'] and r['upper_jaw_contact'] and r['all_specimen_and_machine_in_frame']
    assert not r['overlapping_material_pairs'], (f,r['overlapping_material_pairs'][:3])
    assert not r['overlapping_fixture_pairs'], (f,r['overlapping_fixture_pairs'][:3])
    assert r['min_material_z'] >= BASE_TOP-1e-6
    assert r['material_contact_path_between_jaws'] == (f<=EVENT), (f,r['material_contact_path_between_jaws'])
    if a.render or selected or not a.checks_only:
        s.render.filepath=str(out/'frames'/f'frame_{f:04d}.png')
        bpy.ops.render.render(write_still=True)
if not selected and (a.render or a.checks_only):
    pre=rows[EVENT-1];post=rows[EVENT];last=rows[-1]
    stable_rows=[r for r in rows if r['time_s']>=18.5]
    stable=[r['actual_mesh_hash'] for r in stable_rows]
    assert all(all(g is not None and abs(g)<1e-5 for g in r['fragment_support_gaps']) for r in stable_rows)
    summary={'frames_checked':len(rows),'topological_partition_frame_one_based':EVENT+1,
      'first_sampled_no_contact_path_frame_one_based':next(r['frame'] for r in rows if not r['material_contact_path_between_jaws']),
      'before_event_measured_components':pre['components_measured'],'after_event_measured_components':post['components_measured'],
      'volume_initial_to_pre_event_ratio':pre['actual_volume']/rows[0]['actual_volume'],
      'volume_pre_to_after_partition_ratio':post['actual_volume']/pre['actual_volume'],
      'actual_volume_minmax': [min(r['actual_volume'] for r in rows),max(r['actual_volume'] for r in rows)],
      'all_component_meshes_closed':all(r['all_meshes_closed_and_nondegenerate'] for r in rows),
      'all_lower_and_upper_jaw_contacts':all(r['lower_jaw_contact'] and r['upper_jaw_contact'] for r in rows),
      'projected_convex_material_penetrations':sum(len(r['overlapping_material_pairs']) for r in rows),
      'projected_convex_fixture_aabb_penetrations':sum(len(r['overlapping_fixture_pairs']) for r in rows),
      'all_specimen_and_machine_in_frame':all(r['all_specimen_and_machine_in_frame'] for r in rows),
      'stable_material_hashes_after_18_5_s':len(set(stable))==1,
      'all_fragments_supported_after_18_5_s':True,
      'final_fragment_support_gap_range':[min(last['fragment_support_gaps']),max(last['fragment_support_gaps'])],
      'scope':'actual evaluated convex extruded x/z projection at sampled frames; no general swept or arbitrary 3D collision solver; independent material review and user acceptance are separate'}
    (out/'all_frame_summary.json').write_text(json.dumps(summary,indent=2))
(out/('selected_frame_mesh_checks.json' if selected else 'all_frame_mesh_checks.json')).write_text(json.dumps(rows,indent=2))
(out/'config.json').write_text(json.dumps(CONFIG,indent=2))
update(600)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene_final_state.blend'))
print('EXPLOSIVE_DONE',VERSION,str(out),flush=True)
