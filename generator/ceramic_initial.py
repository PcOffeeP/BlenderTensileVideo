"""Qualitative ceramic tensile candidate. Blender --background --python ... -- --out DIR [--render].
The discrete baseline is not a constitutive material model or calibrated source reconstruction.
All geometry is retained when the complementary fracture faces separate during the final load step.
"""
import argparse, bpy, hashlib, json, math, struct, sys
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
VERSION = 'ceramic-initial/1.2.0'
p = argparse.ArgumentParser(); p.add_argument('--out', required=True); p.add_argument('--render', action='store_true'); p.add_argument('--checks-only', action='store_true'); p.add_argument('--render-frames', help='comma separated frame indices for targeted rerender')
p.add_argument('--fracture-center-z', type=float, default=-0.4, help='fracture center in initial material z coordinates; entire transverse seam must remain inside authored gauge')
p.add_argument('--final-disconnection-time-s', type=float, default=16.0, choices=[12.0,13.0,15.0,16.0,17.0], help='20-second demo final graph disconnection time; 16 is original baseline, 12/13/15/17 discrete candidates; new values pending material/visual qualification')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
selected_frames=sorted({int(v) for v in a.render_frames.split(',')}) if a.render_frames else None
if selected_frames and not all(1<=v<=600 for v in selected_frames):p.error('--render-frames entries must be within1..600')
if not math.isfinite(a.fracture_center_z) or not (-1.5 < a.fracture_center_z-.07 and a.fracture_center_z+.07 < 1.5):
 p.error('complete fracture seam center +/-0.07 must lie strictly inside initial-material authored gauge (-1.5,1.5); this engineering guard does not approve a continuous parameter range')
first_separated=int(round(a.final_disconnection_time_s*30))+1
last_connected=first_separated-1
crack_start=first_separated-120
out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
C = {'implementation_version': VERSION, 'applicability': 'one uncalibrated monolithic ceramic small-deformation brittle tensile demonstration', 'fps':30,'frames':600,'duration_s':20,'resolution':[1280,720], 'units':'dimensionless relative coordinates, no asserted mm scale', 'free_span':5.0,'width_gauge':0.70,'width_shoulders':1.30,'thickness':0.20,'embed_each_jaw':0.48,'authored_gauge':[-1.5,1.5], 'source_formal_gauge_known':False,'fracture_center_z':a.fracture_center_z,'crack_shape':'complementary mildly irregular transverse surface, source-unresolved assumption', 'last_connected_frame':last_connected,'first_separated_frame':first_separated,'event_time_s':a.final_disconnection_time_s,'moving_end':'upper','fixed_end':'lower','axis':'z','prefracture_extension':0.012,'crack_loading_travel':0.028,'crack_start_frame':crack_start,'last_ligament_thickness':0.0002,'last_ligament_u_range':[0,0.03125],'last_ligament_contact_after_cut':True,'minimum_resolved_opening':1e-7,'total_grip_travel':0.040,'stop_from_frame':first_separated,'postfracture_motion':0,'camera_fixed':True,'camera_ortho_scale':17.2,'camera_position':[0,-22,0],'solver':'prescribed geometry, no constitutive solver','no_removed_material':True,'no_fragment_shortening':True}
C.update({'parameter_scope':'stage1 and training-batch1 finite discrete candidates; new values pending material/visual qualification; continuous ranges and coupled combinations unapproved', 'baseline_implementation_version':'ceramic-initial/1.0.1', 'parameter_definitions':{'fracture_center_z':{'unit':'initial dimensionless material z','default':-0.4,'engineering_guard':'finite center +/-0.07 strictly inside (-1.5,1.5)'},'final_disconnection_time_s':{'unit':'simulation seconds from frame1=0','default':16.0,'discrete_values':[12.0,13.0,15.0,16.0,17.0]}}, 'fracture_zone_initial_material_z_bounds':[a.fracture_center_z-.07,a.fracture_center_z+.07], 'crack_development_event_interval_s':4.0, 'crack_interpolation_duration_frames':119, 'frame_timestamp_convention':'time_s=(frame-1)/30; encoded duration600/30=20s', 'authored_first_crack_opening_frame':crack_start+1, 'gauge_marker_material_z':[-1.4,1.4], 'section_material_z':[(a.fracture_center_z-.07-1.5)/2,(a.fracture_center_z+.07+1.5)/2], 'section_measurement':'evaluated outer edges intersect initial material z plane; projected xy polygon area and 3D polygon vector area; entire crack envelope excluded', 'volume_applicability':'uncalibrated elastic-like geometric volume; no incompressibility or force-equilibrium assertion', 'scene_file_scope':'saved final state only; full animation reconstructed by reusable generator', 'equations':{'elastic_extension':'prefracture_extension*S((min(frame,last_connected)-1)/(last_connected-1))','crack_progress':'S((min(frame,last_connected)-crack_start)/(last_connected-crack_start))','seam':'fracture_center_z+0.045*sin(15*u)+0.025*sin(39*u)','cut':'separate vertex indices from first_separated without coordinate movement'},'render_engine':'BLENDER_WORKBENCH','studio_light':'paint.sl','anti_aliasing':'8','world_color':[.31,.43,.55],'camera_target':[0,0,0],'specimen_color':[.81,.79,.70],'fracture_face_color':[.57,.55,.49],'mesh_surface_subdivisions_u_t':[32,32],'material_thickness_y_layers':[-.1,-.075,-.05,-.025,0,.025,.05,.075,.095,.099,.0998,.1],'encoding':{'codec':'libx264','crf':18,'pixel_format':'yuv420p','movflags':'+faststart'}})
C.update({'geometry_constants':{'embedded_z_endpoints':[-2.98,2.98],'width_equation':'0.7 if abs(material_z)<=1.4;1.3 if>=2.4; otherwise0.7+0.6*S((abs(material_z)-1.4)/1.0)','seam_amplitudes':[.045,.025],'seam_frequencies':[15,39],'crack_front_start_y':-.1,'crack_front_travel_y':.1998,'depth_opening_scale':.025,'lateral_center_u':.015625,'lateral_half_width_u':.015625,'lateral_scale_u':.15,'lateral_opening_progress_start':.60,'lateral_opening_progress_span':.40,'elastic_free_span_z':[-2.5,2.5]},'local_open_fraction_equation':'w=max(S((-.1+.1998*p-y)/.025),S((abs(u-.015625)-.015625)/.15)*S((p-.60)/.40))','upper_crack_displacement_equation':'if crack_loading_travel*p*w<=minimum_resolved_opening, set w=0; delta_z=crack_loading_travel*p*(w+(1-w)*t)','shading':{'light':'STUDIO','color_type':'MATERIAL','show_shadows':True,'show_cavity':True,'cavity_type':'BOTH','curvature_ridge_factor':1.1,'curvature_valley_factor':1.4,'show_specular_highlight':True,'background_type':'WORLD','view_transform':'Standard'},'material_colors':{'ceramic':[.81,.79,.70],'fracture':[.57,.55,.49],'steel':[.47,.51,.54],'jaw':[.19,.22,.25],'machine':[.28,.36,.42],'bolts':[.08,.09,.11]}})
C.update({'parameter_design_documents':['docs/history/video-v1/fracture-variation-stage1.md','docs/history/video-v1/training-batch1-design.md'], 'batch1_new_discrete_values':{'final_disconnection_time_s':[13.0]}, 'batch1_new_value_qualification':'pending_material_and_visual_checks; parser support does not establish applicability or acceptance'})
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
def crack_progress(f):return smooth((min(f,last_connected)-crack_start)/(last_connected-crack_start))
def disp(f):return C['prefracture_extension']*smooth((min(f,last_connected)-1)/(last_connected-1))+C['crack_loading_travel']*crack_progress(f)
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
def seam(u):return C['fracture_center_z']+.045*math.sin(15*u)+.025*math.sin(39*u)
def build(f):
 verts=[];faces=[];mids=[];cache={};rest_z=[];split=f>=first_separated;ext=C['prefracture_extension']*smooth((min(f,last_connected)-1)/(last_connected-1))
 def vertex(u,y,t,part):
  zz=seam(u)
  z=(-2.98+(zz+2.98)*t) if part==0 else (zz+(2.98-zz)*t)
  if (part==0 and t==1) or (part==1 and t==0):z=zz
  x=u*width(z);initial_z=z;z+=ext*max(0,min(1,(z+2.5)/5))
  if part==1:z+=upper_crack_displacement(u,y,t,f)
  v=(x,y,z);key=v
  if split:key=(part,)+key
  if key not in cache:cache[key]=len(verts);verts.append(v);rest_z.append(initial_z)
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
 ff=[v for i,v in enumerate(faces) if i not in discard];used=sorted({v for face in ff for v in face});remap={v:i for i,v in enumerate(used)};verts=[verts[v] for v in used];rest_z=[rest_z[v] for v in used];ff=[tuple(remap[v] for v in face) for face in ff]
 mesh=bpy.data.meshes.new('ceramic retained material');mesh.from_pydata(verts,[],ff);attribute=mesh.attributes.new('initial_material_z','FLOAT','POINT')
 for datum,z in zip(attribute.data,rest_z):datum.value=z
 mesh.materials.append(ceramic);mesh.materials.append(cutmat);mesh.update()
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
 ext=C['prefracture_extension']*smooth((min(f,last_connected)-1)/(last_connected-1));paths=[]
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
  diffs=[];upper_by_xy={(round(v.x,7),round(v.y,7)):v for v in uc}
  for v in lc:
   u=upper_by_xy[(round(v.x,7),round(v.y,7))];diffs.append(u.z-v.z)
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
 r={'frame':f,'time_s':(f-1)/30,'measured_components':len(components),'component_vertices':[len(cc) for cc in components],'evaluated_vertices':len(vs),'evaluated_faces':len(me.polygons),'closed_manifold_edge_incidence':all(v==2 for v in edge_counts.values()),'measured_material_volume':volume,'same_material_lower_upper_edge_lengths':paths,'actual_section_thickness':max(v.y for v in vs)-min(v.y for v in vs),'grip_surface_contact_max_errors':jawcontact,'grip_contact_sampling':'only outside material surfaces y=+/-0.1; interior thickness-layer vertices on embedded end faces are not jaw-contact candidates','grip_material_embed_sampled_lengths':overlap,'upper_jaw_z_displacement':disp(f),'complementary_fracture_gap_z_minmax':gap,'fracture_penetration':gap is not None and min(gap)<-1e-6,'last_bonded_ligament_thickness':(.0002 if f==last_connected else None),'final_zero_opening_contact_patch_thickness':(.0002 if f>=first_separated else None),'actual_matching_fracture_face_contact_area':contact_area,'actual_matching_contact_polygons':contact_polygons,'actual_coincident_unwelded_vertex_duplicates':shared_position_vertices,'top_to_bottom_material_graph_path_exists':bool(top_components & bottom_components)}
 sections=[];rz=[d.value for d in me.attributes['initial_material_z'].data]
 for section_z in C['section_material_z']:
  points={}
  for edge in me.edges:
   i,j=edge.vertices;lo,hi=rz[i],rz[j]
   if (lo<section_z<hi) or (hi<section_z<lo):
    q=vs[i].lerp(vs[j],(section_z-lo)/(hi-lo));points[(round(q.x,7),round(q.y,7))]=q
  ordered=sorted(points.values(),key=lambda q:math.atan2(q.y,q.x));av=Vector((0,0,0))
  for aa,bb in zip(ordered,ordered[1:]+ordered[:1]):av+=aa.cross(bb)/2
  sections.append({'initial_material_z':section_z,'outside_entire_fracture_zone':not C['fracture_zone_initial_material_z_bounds'][0]<=section_z<=C['fracture_zone_initial_material_z_bounds'][1],'measured_projected_area_xy':abs(av.z),'measured_vector_area_3d':av.length,'evaluated_outer_edge_intersections':len(ordered)})
 # Track the same material edge points at u=-0.5,y=-0.1 by interpolation between actual evaluated mesh vertices.
 def material_point(z):
  part=0 if z<seam(-.5) else 1;points=[]
  for j in range(33):
   zz=seam(-.5);rest=(-2.98+(zz+2.98)*j/32) if part==0 else (zz+(2.98-zz)*j/32)
   target_z=rest+ext*max(0,min(1,(rest+2.5)/5))+(upper_crack_displacement(-.5,-.1,j/32,f) if part==1 else 0)
   actual,ind,distance=kd.find(Vector((-.5*width(rest),-.1,target_z)));assert distance<1e-5
   points.append((rest,actual))
  for (za,aa),(zb,bb) in zip(points,points[1:]):
   if za<=z<=zb:return aa.lerp(bb,(z-za)/(zb-za))
  raise AssertionError('material point outside edge range')
 markers=[material_point(z) for z in C['gauge_marker_material_z']]
 segment_lengths=[]
 for z in C['section_material_z']:
  span=min(abs(z-C['fracture_center_z'])-.07,1.5-abs(z))*.5
  pa,pb=material_point(z-span),material_point(z+span)
  segment_lengths.append({'initial_material_z_interval':[z-span,z+span],'actual_endpoint_distance':(pb-pa).length,'actual_axial_projection_length':pb.z-pa.z,'measurement':'same intact material edge segment; outside full crack envelope'})
 crack_z=[rz[i] for pp in me.polygons if pp.material_index==1 for i in pp.vertices]
 actual_crack_bounds=[min(crack_z),max(crack_z)] if crack_z else None
 assert actual_crack_bounds is None or (-1.5<actual_crack_bounds[0] and actual_crack_bounds[1]<1.5)
 r.update({'actual_fracture_face_initial_material_z_bounds':actual_crack_bounds,'complete_fracture_zone_inside_authored_gauge':actual_crack_bounds is None or (-1.5<actual_crack_bounds[0] and actual_crack_bounds[1]<1.5),'same_material_gauge_marker_coordinates':[list(v) for v in markers],'same_material_gauge_axial_projection_length':markers[1].z-markers[0].z,'gauge_length_includes_crack_opening':f>crack_start,'intact_same_material_segments':segment_lengths,'intact_material_sections':sections,'mesh_coordinates_topology_sha256':hashlib.sha256(b''.join(struct.pack('<fff',*v) for v in vs)+b''.join(struct.pack('<I',len(pp.vertices))+b''.join(struct.pack('<I',i) for i in pp.vertices) for pp in me.polygons)).hexdigest(),'fixture_positions_sha256':hashlib.sha256(b''.join(struct.pack('<fff',*o.location) for o,sg in fixtures)).hexdigest()})
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
keyframes=sorted({1,crack_start//2,crack_start,crack_start+1,crack_start+60,crack_start+90,last_connected-1,last_connected,first_separated,min(first_separated+60,600),600});checks=[check(f,True) for f in keyframes]
last=next(r for r in checks if r['frame']==last_connected);first=next(r for r in checks if r['frame']==first_separated)
pre_unique=set(tuple(v) for v in last['coordinates']);post_unique=set(tuple(v) for v in first['coordinates'])
assert pre_unique==post_unique
transition={'last_connected_frame':last_connected,'first_separated_frame':first_separated,'actual_unique_vertex_coordinate_sets_identical':pre_unique==post_unique,'unique_coordinate_count':len(pre_unique),'max_fixture_motion':max(abs(x-y) for aa,bb in zip(last['fixture_coordinates'],first['fixture_coordinates']) for x,y in zip(aa,bb)),'max_same_material_front_rear_path_change':max(abs(v-first['actual_front_rear_material_paths'][k]) for k,v in last['actual_front_rear_material_paths'].items()),'volume_change':first['measured_material_volume']-last['measured_material_volume'],'zero_opening_contact_area':first['actual_matching_fracture_face_contact_area'],'connectivity_measurement':'single specimen object evaluated edge adjacency graph; path from embedded bottom to embedded top exists at last_connected and absent at first_separated; coincident contact vertices are separate indices, coordinate welding would falsely re-bond them'}
for r in checks:r.pop('coordinates');r.pop('fixture_coordinates')
post=[check(f,True) for f in [first_separated,first_separated+1,min(first_separated+60,600),600]]
stop=max(abs(x-y) for r in post for aa,bb in zip(post[0]['coordinates'],r['coordinates']) for x,y in zip(aa,bb));fixstop=max(abs(x-y) for r in post for aa,bb in zip(post[0]['fixture_coordinates'],r['fixture_coordinates']) for x,y in zip(aa,bb))
if not a.checks_only and not a.render_frames:
 for f in keyframes:
  update(f);s.render.filepath=str(out/'previews'/('frame_%04d.png'%f));bpy.ops.render.render(write_still=True)
(out/'mesh_checks.json').write_text(json.dumps({'config':C,'transition':transition,'samples':checks,'post_event_max_material_vertex_motion':stop,'post_event_max_fixture_motion':fixstop,'scope':'actual evaluated vertices and edge graph, closed mesh edge incidence, signed material volume, tracked material boundary lengths, jaw inner face contact; exact complementary seam vertex clearance; no general triangle self intersection solver or force equilibrium validation'},indent=2))
C['fixtures_initial']=[{'name':o.name,'location':[o.location.x,o.location.y,base[o.name]],'dimensions':list(o.dimensions),'moving_sign':sg} for o,sg in fixtures]
C['fixed_machine_geometry']=[{'name':o.name,'location':list(o.location),'dimensions':list(o.dimensions)} for o in s.objects if o.type=='MESH' and o!=obj and o.name not in base]
(out/'config.json').write_text(json.dumps(C,indent=2));update(600);bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene_final_state.blend'))
if a.render or a.checks_only or a.render_frames:
 allchecks=[];post_mesh_hash=None;post_fixture_hash=None
 for f in (selected_frames or range(1,601)):
  row=check(f);allchecks.append(row)
  assert row['grip_surface_contact_max_errors'] and max(row['grip_surface_contact_max_errors'])<1e-6
  assert row['closed_manifold_edge_incidence'] and not row['fracture_penetration']
  assert row['top_to_bottom_material_graph_path_exists']==(f<first_separated)
  assert row['measured_components']==(1 if f<first_separated else 2)
  if f>=first_separated:
   if post_mesh_hash is None:post_mesh_hash=row['mesh_coordinates_topology_sha256'];post_fixture_hash=row['fixture_positions_sha256']
   assert row['mesh_coordinates_topology_sha256']==post_mesh_hash and row['fixture_positions_sha256']==post_fixture_hash
  if a.render or a.render_frames:
   s.render.filepath=str(out/'frames'/('frame_%04d.png'%f));bpy.ops.render.render(write_still=True)
 baseline=allchecks[0] if allchecks[0]['frame']==1 else check(1)
 for row in allchecks:
  row['same_material_gauge_axial_projection_lambda']=row['same_material_gauge_axial_projection_length']/baseline['same_material_gauge_axial_projection_length']
  row['material_volume_ratio_to_initial']=row['measured_material_volume']/baseline['measured_material_volume']
  for section,initial in zip(row['intact_material_sections'],baseline['intact_material_sections']):
   section['projected_area_ratio_to_initial']=section['measured_projected_area_xy']/initial['measured_projected_area_xy'];section['vector_area_ratio_to_initial']=section['measured_vector_area_3d']/initial['measured_vector_area_3d']
  for segment,initial in zip(row['intact_same_material_segments'],baseline['intact_same_material_segments']):segment['endpoint_distance_lambda']=segment['actual_endpoint_distance']/initial['actual_endpoint_distance']
 if not selected_frames:
  opened=[row for row in allchecks if row['complementary_fracture_gap_z_minmax'] is not None and row['complementary_fracture_gap_z_minmax'][1]>C['minimum_resolved_opening']]
  disconnected=[row for row in allchecks if not row['top_to_bottom_material_graph_path_exists']]
  summary={'frames_checked':len(allchecks),'actual_first_nonzero_crack_opening_frame':opened[0]['frame'] if opened else None,'actual_first_disconnection_frame':disconnected[0]['frame'] if disconnected else None,'actual_last_connected_frame':disconnected[0]['frame']-1 if disconnected else None,'post_event_all_frame_material_and_fixture_hashes_identical':True,'max_jaw_contact_error':max(max(row['grip_surface_contact_max_errors']) for row in allchecks),'volume_ratio_minmax':[min(row['material_volume_ratio_to_initial'] for row in allchecks),max(row['material_volume_ratio_to_initial'] for row in allchecks)],'last_before_crack':allchecks[crack_start-1],'last_before_disconnection':allchecks[last_connected-1],'scope':'actual evaluated 600-frame geometry checks; visual encoding, independent review, user acceptance pending'}
  (out/'all_frame_summary.json').write_text(json.dumps(summary,indent=2))
 (out/('selected_frame_mesh_checks.json' if a.render_frames else 'all_frame_mesh_checks.json')).write_text(json.dumps(allchecks,indent=2))
