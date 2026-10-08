"""Qualitative ceramic tensile candidate. Blender --background --python ... -- --out DIR [--render].
The discrete baseline is not a constitutive material model or calibrated source reconstruction.
All geometry is retained when the complementary fracture faces separate during the final load step.
"""
import argparse, bpy, json, math, sys
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
VERSION = 'ceramic-initial/1.0.1'
p = argparse.ArgumentParser(); p.add_argument('--out', required=True); p.add_argument('--render', action='store_true'); p.add_argument('--checks-only', action='store_true'); p.add_argument('--render-frames', help='comma separated frame indices for targeted rerender')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
selected_frames=sorted({int(v) for v in a.render_frames.split(',')}) if a.render_frames else None
if selected_frames and not all(1<=v<=600 for v in selected_frames):p.error('--render-frames entries must be within1..600')
out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
C = {'implementation_version': VERSION, 'applicability': 'one uncalibrated monolithic ceramic small-deformation brittle tensile demonstration', 'fps':30,'frames':600,'duration_s':20,'resolution':[1280,720], 'units':'dimensionless relative coordinates, no asserted mm scale', 'free_span':5.0,'width_gauge':0.70,'width_shoulders':1.30,'thickness':0.20,'embed_each_jaw':0.48,'authored_gauge':[-1.5,1.5], 'source_formal_gauge_known':False,'fracture_center_z':-0.4,'crack_shape':'complementary mildly irregular transverse surface, source-unresolved assumption', 'last_connected_frame':480,'first_separated_frame':481,'event_time_s':16.0,'moving_end':'upper','fixed_end':'lower','axis':'z','prefracture_extension':0.012,'crack_loading_travel':0.028,'crack_start_frame':361,'last_ligament_thickness':0.0002,'last_ligament_u_range':[0,0.03125],'last_ligament_contact_after_cut':True,'minimum_resolved_opening':1e-7,'total_grip_travel':0.040,'stop_from_frame':481,'postfracture_motion':0,'camera_fixed':True,'camera_ortho_scale':17.2,'camera_position':[0,-22,0],'solver':'prescribed geometry, no constitutive solver','no_removed_material':True,'no_fragment_shortening':True}
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
s=bpy.context.scene; s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.fps=30;s.frame_start=1;s.frame_end=600;s.render.image_settings.file_format='PNG'
sh=s.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=1.1;sh.curvature_valley_factor=1.4;sh.show_specular_highlight=True;sh.background_type='WORLD';s.world.color=(.31,.43,.55);s.display.render_aa='8';s.view_settings.view_transform='Standard'
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
ceramic=mat('off white ceramic qualitative appearance',(.81,.79,.70));cutmat=mat('new fracture surface',(.57,.55,.49));steel=mat('satin steel',(.47,.51,.54));jawmat=mat('grip jaws',(.19,.22,.25));machine=mat('machine frame',(.28,.36,.42));dark=mat('bolts',(.08,.09,.11))
def box(name,loc,dims,m,bevel=.035):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:
  q=o.modifiers.new('machined edges','BEVEL');q.width=bevel;q.segments=3;o.modifiers.new('normal weighting','WEIGHTED_NORMAL')
 return o
fixtures=[]
for sign in [-1,1]:
 for y in [-.30,.30]: fixtures.append((box(('lower' if sign<0 else 'upper')+' physical jaw '+str(y),(0,y,sign*2.85),(1.65,.4,.70),jawmat),sign))
 fixtures.append((box('fixture load body '+str(sign),(0,.05,sign*3.31),(2.1,1.15,.30),steel),sign))
 fixtures.append((box('load transfer rod '+str(sign),(0,.05,sign*3.73),(.62,.72,.60),steel),sign))
 for x in [-.77,.77]: fixtures.append((box('jaw fastener '+str(sign)+str(x),(x,-.53,sign*2.85),(.18,.09,.18),dark,.045),sign))
# Fixed machine with visible connections: jaw -> body -> rod -> beam -> columns -> base.
box('upper machine crossbeam',(0,.08,4.17),(6.65,1.0,.50),machine)
box('lower machine base',(0,.08,-4.17),(6.65,1.15,.50),machine)
for x in [-3.12,3.12]:box('machine support column '+str(x),(x,.08,0),(.48,.60,8.0),machine)
box('floor base',(0,.08,-4.56),(7.35,1.7,.28),steel)
bpy.ops.object.camera_add(location=C['camera_position']);cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=C['camera_ortho_scale'];s.camera=cam
base={o.name:o.location.z for o,sign in fixtures}
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def crack_progress(f):return smooth((min(f,480)-361)/119)
def disp(f):return C['prefracture_extension']*smooth((min(f,480)-1)/479)+C['crack_loading_travel']*crack_progress(f)
def local_open_fraction(u,y,f):
 p=crack_progress(f);front=-.1+.1998*p
 depth=smooth((front-y)/.025)
 lateral=smooth((abs(u-.015625)-.015625)/.15)*smooth((p-.60)/.40)
 return max(depth,lateral)
def upper_crack_displacement(u,y,t,f):
 w=local_open_fraction(u,y,f)
 if C['crack_loading_travel']*crack_progress(f)*w<=C['minimum_resolved_opening']:w=0.0
 return C['crack_loading_travel']*crack_progress(f)*(w+(1-w)*t)
def width(z):
 if abs(z)<=1.40:return .70
 if abs(z)>=2.40:return 1.30
 return .70+.60*smooth((abs(z)-1.4)/1.0)
def seam(u):return -.40+.045*math.sin(15*u)+.025*math.sin(39*u)
def build(f):
 verts=[];faces=[];mids=[];cache={};material_rings={};split=f>=481;ext=C['prefracture_extension']*smooth((min(f,480)-1)/479)
 def vertex(u,y,t,part):
  zz=seam(u)
  z=(-2.98+(zz+2.98)*t) if part==0 else (zz+(2.98-zz)*t)
  if (part==0 and t==1) or (part==1 and t==0):z=zz
  x=u*width(z);z+=ext*max(0,min(1,(z+2.5)/5))
  if part==1:z+=upper_crack_displacement(u,y,t,f)
  v=(x,y,z);key=v
  if split:key=(part,)+key
  if key not in cache:cache[key]=len(verts);verts.append(v)
  return cache[key]
 ys=[-.1,-.075,-.05,-.025,0,.025,.05,.075,.095,.099,.0998,.1]
 def face(points,mi=0):faces.append(tuple(vertex(*q) for q in points));mids.append(mi)
 for part in [0,1]:
  for i in range(32):
   ua=-.5+i/32;ub=-.5+(i+1)/32
   for j in range(32):
    ta=j/32;tb=(j+1)/32
    face([(ua,-.1,ta,part),(ub,-.1,ta,part),(ub,-.1,tb,part),(ua,-.1,tb,part)])
    face([(ua,.1,tb,part),(ub,.1,tb,part),(ub,.1,ta,part),(ua,.1,ta,part)])
   for ya,yb in zip(ys,ys[1:]):
    face([(ua,ya,0,part),(ua,yb,0,part),(ub,yb,0,part),(ub,ya,0,part)],1 if part==1 else 0)
    face([(ub,ya,1,part),(ub,yb,1,part),(ua,yb,1,part),(ua,ya,1,part)],1 if part==0 else 0)
  for j in range(32):
   ta=j/32;tb=(j+1)/32
   for ya,yb in zip(ys,ys[1:]):
    face([(-.5,ya,ta,part),(-.5,ya,tb,part),(-.5,yb,tb,part),(-.5,yb,ta,part)])
    face([(.5,yb,ta,part),(.5,yb,tb,part),(.5,ya,tb,part),(.5,ya,ta,part)])

 seen={};discard=set()
 for i,face in enumerate(faces):
  k=tuple(sorted(face))
  if k in seen:discard.update([i,seen[k]])
  else:seen[k]=i
 ff=[v for i,v in enumerate(faces) if i not in discard];used=sorted({v for face in ff for v in face});remap={v:i for i,v in enumerate(used)};verts=[verts[v] for v in used];ff=[tuple(remap[v] for v in face) for face in ff]
 mesh=bpy.data.meshes.new('ceramic retained material');mesh.from_pydata(verts,[],ff);mesh.materials.append(ceramic);mesh.materials.append(cutmat);mesh.update()
 for face,mi in zip(mesh.polygons,[v for i,v in enumerate(mids) if i not in discard]):face.material_index=mi
 return mesh
obj=bpy.data.objects.new('actual ceramic specimen',build(1));s.collection.objects.link(obj)
def update(f):
 old=obj.data;obj.data=build(f);bpy.data.meshes.remove(old)
 for o,sg in fixtures:o.location.z=base[o.name]+(disp(f) if sg>0 else 0)
 s.frame_set(f)
def check(f,coords=False):
 update(f);dg=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dg);me=ev.to_mesh();vs=[obj.matrix_world@v.co for v in me.vertices];adj=[set() for _ in vs]
 for e in me.edges:u,v=e.vertices;adj[u].add(v);adj[v].add(u)
 seen=set();components=[]
 for i in range(len(vs)):
  if i in seen:continue
  q=[i];seen.add(i);cc=[]
  while q:
   u=q.pop();cc.append(u)
   for v in adj[u]:
    if v not in seen:seen.add(v);q.append(v)
  components.append(cc)
 me.calc_loop_triangles();volume=abs(sum(vs[t.vertices[0]].dot(vs[t.vertices[1]].cross(vs[t.vertices[2]]))/6 for t in me.loop_triangles))
 edge_counts={}
 for pp in me.polygons:
  ids=list(pp.vertices)
  for aa,bb in zip(ids,ids[1:]+ids[:1]):k=tuple(sorted((aa,bb)));edge_counts[k]=edge_counts.get(k,0)+1
 kd=KDTree(len(vs))
 for i,v in enumerate(vs):kd.insert(v,i)
 kd.balance()
 top_components={j for j,cc in enumerate(components) if any(vs[i].z>2.8 for i in cc)}
 bottom_components={j for j,cc in enumerate(components) if any(vs[i].z<-2.8 for i in cc)}
 # Physical clamping contact against evaluated planar jaw inner faces; vertices in jaws remain present.
 jawcontact=[];overlap=[]
 for sg in [-1,1]:
  d=disp(f) if sg>0 else 0;grip=[v for v in vs if (v.z<-2.5 if sg<0 else v.z>2.5+d)]
  inner=[]
  for o,sign in fixtures:
   if sign==sg and 'physical jaw' in o.name:
    eo=o.evaluated_get(dg);jm=eo.to_mesh();ys=[(eo.matrix_world@v.co).y for v in jm.vertices];inner.append(max(ys) if o.location.y<0 else min(ys));eo.to_mesh_clear()
  surface=[v for v in grip if abs(abs(v.y)-.1)<1e-6]
  jawcontact.append(max(min(abs(v.y-y) for y in inner) for v in surface));overlap.append(max(v.z for v in grip)-min(v.z for v in grip))
 # Same material edge paths: geometry built in stable vertex insertion order. Extract longitudinal edge at u=-.5, y=-.1 from each half with unique t coordinate.
 ext=C['prefracture_extension']*smooth((min(f,480)-1)/479);paths=[]
 for part in [0,1]:
  pts=[]
  for j in range(33):
   zz=seam(-.5);z=(-2.98+(zz+2.98)*j/32) if part==0 else (zz+(2.98-zz)*j/32);x=-.5*width(z);z+=ext*max(0,min(1,(z+2.5)/5));z+=upper_crack_displacement(-.5,-.1,j/32,f) if part==1 else 0
   target=Vector((x,-.1,z));actual=kd.find(target)[0];assert (actual-target).length<1e-5;pts.append(actual)
  paths.append(sum((b-a).length for a,b in zip(pts,pts[1:])))
 gap=None;contact_area=0.0;contact_polygons=0;shared_position_vertices=0
 if any(pp.material_index==1 for pp in me.polygons):
  lc=[];uc=[]
  for pp in me.polygons:
   if pp.material_index==1:
    (lc if pp.normal.z>0 else uc).extend(vs[i] for i in pp.vertices)
  diffs=[]
  for v in lc:
   u=min(uc,key=lambda u:(u.x-v.x)**2+(u.y-v.y)**2);diffs.append(u.z-v.z)
  gap=[min(diffs),max(diffs)]
  lower_faces={}
  for pp in me.polygons:
   if pp.material_index==1 and pp.normal.z>0:lower_faces[tuple(sorted(tuple(round(q,8) for q in vs[i]) for i in pp.vertices))]=pp.area
  for pp in me.polygons:
   if pp.material_index==1 and pp.normal.z<0:
    k=tuple(sorted(tuple(round(q,8) for q in vs[i]) for i in pp.vertices))
    if k in lower_faces:contact_area+=lower_faces[k];contact_polygons+=1
  positions={}
  for v in vs:
   k=tuple(round(q,8) for q in v);positions[k]=positions.get(k,0)+1
  shared_position_vertices=sum(n-1 for n in positions.values() if n>1)
 r={'frame':f,'time_s':(f-1)/30,'measured_components':len(components),'component_vertices':[len(cc) for cc in components],'evaluated_vertices':len(vs),'evaluated_faces':len(me.polygons),'closed_manifold_edge_incidence':all(v==2 for v in edge_counts.values()),'measured_material_volume':volume,'same_material_lower_upper_edge_lengths':paths,'actual_section_thickness':max(v.y for v in vs)-min(v.y for v in vs),'grip_surface_contact_max_errors':jawcontact,'grip_contact_sampling':'only outside material surfaces y=+/-0.1; interior thickness-layer vertices on embedded end faces are not jaw-contact candidates','grip_material_embed_sampled_lengths':overlap,'upper_jaw_z_displacement':disp(f),'complementary_fracture_gap_z_minmax':gap,'fracture_penetration':gap is not None and min(gap)<-1e-6,'last_bonded_ligament_thickness':(.0002 if f==480 else None),'final_zero_opening_contact_patch_thickness':(.0002 if f>=481 else None),'actual_matching_fracture_face_contact_area':contact_area,'actual_matching_contact_polygons':contact_polygons,'actual_coincident_unwelded_vertex_duplicates':shared_position_vertices,'top_to_bottom_material_graph_path_exists':bool(top_components & bottom_components)}
 if coords:
  r['coordinates']=[list(v) for v in vs];r['fixture_coordinates']=[list(o.location) for o,sg in fixtures]
  paths={}
  for u in [-.5,0,.03125,.5]:
   for y in [-.1,.1]:
    for part in [0,1]:
     pts=[]
     for j in range(33):
      zz=seam(u);z=(-2.98+(zz+2.98)*j/32) if part==0 else (zz+(2.98-zz)*j/32);x=u*width(z);z+=ext*max(0,min(1,(z+2.5)/5));z+=upper_crack_displacement(u,y,j/32,f) if part==1 else 0
      point,ind,dist=kd.find(Vector((x,y,z)));assert dist<1e-5;pts.append(point)
     paths['u='+str(u)+',y='+str(y)+',part='+str(part)]=sum((b-a).length for a,b in zip(pts,pts[1:]))
  r['actual_front_rear_material_paths']=paths
 ev.to_mesh_clear();return r
keyframes=[1,241,361,421,451,479,480,481,540,600];checks=[check(f,True) for f in keyframes]
last=next(r for r in checks if r['frame']==480);first=next(r for r in checks if r['frame']==481)
pre_unique=set(tuple(v) for v in last['coordinates']);post_unique=set(tuple(v) for v in first['coordinates'])
assert pre_unique==post_unique
transition={'last_connected_frame':480,'first_separated_frame':481,'actual_unique_vertex_coordinate_sets_identical':pre_unique==post_unique,'unique_coordinate_count':len(pre_unique),'max_fixture_motion':max(abs(x-y) for aa,bb in zip(last['fixture_coordinates'],first['fixture_coordinates']) for x,y in zip(aa,bb)),'max_same_material_front_rear_path_change':max(abs(v-first['actual_front_rear_material_paths'][k]) for k,v in last['actual_front_rear_material_paths'].items()),'volume_change':first['measured_material_volume']-last['measured_material_volume'],'zero_opening_contact_area':first['actual_matching_fracture_face_contact_area'],'connectivity_measurement':'single specimen object evaluated edge adjacency graph; path from embedded bottom to embedded top exists at480 and absent at481; coincident contact vertices are separate indices, coordinate welding would falsely re-bond them'}
for r in checks:r.pop('coordinates');r.pop('fixture_coordinates')
post=[check(f,True) for f in [481,482,540,600]]
stop=max(abs(x-y) for r in post for aa,bb in zip(post[0]['coordinates'],r['coordinates']) for x,y in zip(aa,bb));fixstop=max(abs(x-y) for r in post for aa,bb in zip(post[0]['fixture_coordinates'],r['fixture_coordinates']) for x,y in zip(aa,bb))
if not a.checks_only and not a.render_frames:
 for f in keyframes:
  update(f);s.render.filepath=str(out/'previews'/('frame_%04d.png'%f));bpy.ops.render.render(write_still=True)
(out/'mesh_checks.json').write_text(json.dumps({'config':C,'transition':transition,'samples':checks,'post_event_max_material_vertex_motion':stop,'post_event_max_fixture_motion':fixstop,'scope':'actual evaluated vertices and edge graph, closed mesh edge incidence, signed material volume, tracked material boundary lengths, jaw inner face contact; exact complementary seam vertex clearance; no general triangle self intersection solver or force equilibrium validation'},indent=2))
(out/'config.json').write_text(json.dumps(C,indent=2));update(600);bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene_final_state.blend'))
if a.render or a.checks_only or a.render_frames:
 allchecks=[]
 for f in (selected_frames or range(1,601)):
  allchecks.append(check(f))
  if a.render or a.render_frames:
   s.render.filepath=str(out/'frames'/('frame_%04d.png'%f));bpy.ops.render.render(write_still=True)
 (out/('selected_frame_mesh_checks.json' if a.render_frames else 'all_frame_mesh_checks.json')).write_text(json.dumps(allchecks,indent=2))
