"""Source-labelled mixed polymer candidate; qualitative assumptions remain unverified.
Blender --background --python generator/polymer_mixed.py -- --out DIR [--render]
No input or reuse dependency on the work directory. No calibrated constitutive model.
"""
import argparse,bpy,json,math,sys,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from bpy_extras.object_utils import world_to_camera_view
VERSION='polymer-mixed/1.2.0'
STRETCH_FACTOR_CHOICES=(.85,1.,1.05,1.075,1.10,1.15)
EVENT_TIME_CHOICES=(12.,15.,15.5,16.,17.)
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--render',action='store_true');p.add_argument('--checks-only',action='store_true');p.add_argument('--stretch-increment-factor',type=float,choices=STRETCH_FACTOR_CHOICES,default=1.);p.add_argument('--fracture-center-material-z',type=float,default=-.15);p.add_argument('--event-time-s',type=float,choices=EVENT_TIME_CHOICES,default=16.);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
if not math.isfinite(a.fracture_center_material_z) or not -.30<=a.fracture_center_material_z<=0:p.error('fracture center material z must be in [-0.30,0], keeping whole oblique seam in authored gauge and meshing transition')
EVENT=round(a.event_time_s*30)+1; LAST=EVENT-1; CRACK_START=1+round(474*a.event_time_s/16)
C={'implementation_version':VERSION,'applicability':'gradual visually uniform extension without obvious necking then rapid oblique rupture; project mixed criterion; quantitative mechanics unknown','source_id':'video_0014','fps':30,'frames':600,'duration_s':20,'resolution':[1280,720],'units':'relative author coordinates, no mm scale','rest_material_span':4.8,'initial_free_span':4.0,'grip_material_coordinate_ranges':[[-2.4,-2.0],[2.0,2.4]],'initial_grip_embed':.4,'authored_gauge':[-1.2,1.2],'source_formal_gauge_known':False,'gauge_width':.8,'shoulder_width':1.05,'initial_thickness':.16,'max_local_stretch':1+.08*a.stretch_increment_factor,'transverse_scale':'inverse sqrt of local axial stretch, approximate constant material volume','stretch_shape':'0.3 uniform contribution plus0.7 Gaussian centered-0.15, width0.42, tapered to zero near grips','fracture_center_material_z':a.fracture_center_material_z,'fracture_slope':-.45,'fracture_jagged_amplitude':.012,'last_connected_frame':LAST,'first_separated_frame':EVENT,'event_time_s':a.event_time_s,'crack_start_frame':CRACK_START,'crack_loading_travel':.055*a.stretch_increment_factor,'last_ligament_u_range':[0,.03125],'last_ligament_thickness':.00016,'minimum_resolved_opening':1e-7,'loading_end':'upper','fixed_end':'lower','axis':'z','selected_postfracture_condition':'stop all geometry and fixtures from first separated frame; no additional recoil or bending','camera_position':[0,-22,.1],'camera_target':[0,0,.1],'camera_ortho_scale':12.4,'camera_fixed':True,'view':'fixtures and specimen only; no machine frame or backdrop','width_subdivisions':32,'thickness_layers':[-.08,-.06,-.04,-.02,0,.02,.04,.06,.076,.0792,.07984,.08],'renderer':'BLENDER_WORKBENCH','studio_light':'paint.sl','anti_alias_samples':8,'no_constitutive_solver':True,'continuous_parameter_range_approved':False}
C['stage1']={'baseline_crack_loading_travel':.055,'crack_loading_travel_coupling':'baseline0.055 times stretch_increment_factor; original loading stage coupled, not independent fracture opening control','baseline_implementation_version':'polymer-mixed/1.0.0','stretch_increment_factor':a.stretch_increment_factor,'stretch_increment_definition':'lambda_candidate-1=k*(lambda_baseline-1)','allowed_stretch_increment_factors':list(STRETCH_FACTOR_CHOICES),'default_stretch_increment_factor':1.,'position_engineering_guard':[-.30,0],'full_fracture_material_z_bounds':[a.fracture_center_material_z-.45*.5-.012,a.fracture_center_material_z+.45*.5+.012],'event_candidates_s':[t for t in EVENT_TIME_CHOICES if t!=16.],'allowed_event_times_s':list(EVENT_TIME_CHOICES),'default_regression_event_s':16,'first_crack_pre_frame':CRACK_START,'final_connected_pre_frame':LAST,'actual_first_opening_frame_expected':CRACK_START+1,'scope':'Stage1 and training-batch1 discrete mixed candidates; new values and combinations require applicable mesh, visibility and material/label checks and user acceptance. Guards do not approve continuous ranges or combinations'}
C['stretch_shape']=f'0.3 uniform plus0.7 Gaussian centered {a.fracture_center_material_z}, width0.42, tapered to zero near grips'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.fps=30;s.frame_start=1;s.frame_end=600;s.render.image_settings.file_format='PNG'
sh=s.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=True;sh.background_type='WORLD';s.world.color=(.12,.18,.24);s.display.render_aa='8';s.view_settings.view_transform='Standard'
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
poly=mat('white polymer appearance',(.83,.84,.82));cut=mat('fracture appearance',(.63,.65,.63));steel=mat('clamp steel',(.40,.45,.49));dark=mat('grip housing',(.16,.19,.22));boltmat=mat('clamp bolts',(.10,.12,.14))
def box(n,loc,size,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);q=o.modifiers.new('machined edges','BEVEL');q.width=.025;q.segments=2;o.modifiers.new('normals','WEIGHTED_NORMAL');return o
fixtures=[]
for sg in [-1,1]:
 for y in [-.28,.28]:fixtures.append((box('physical jaw '+str(sg)+str(y),(0,y,sg*2.22),(1.65,.40,.70),steel),sg))
 fixtures.append((box('clamp housing '+str(sg),(0,.08,sg*2.85),(2.35,1.15,.65),dark),sg))
 for x in [-.62,.62]:fixtures.append((box('jaw bolt '+str(sg)+str(x),(x,-.52,sg*2.22),(.18,.10,.18),boltmat),sg))
base={o.name:o.location.z for o,sg in fixtures}
bpy.ops.object.camera_add(location=C['camera_position']);cam=bpy.context.object;cam.rotation_euler=(Vector(C['camera_target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=C['camera_ortho_scale'];s.camera=cam

def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def stretch_progress(f):return smooth((min(f,LAST)-1)/(LAST-1))
def grip_mask(z):return smooth((z+2.0)/.3)*smooth((2.0-z)/.3)
def lam(z,f):return 1+.08*a.stretch_increment_factor*stretch_progress(f)*grip_mask(z)*(.3+.7*math.exp(-((z-a.fracture_center_material_z)/.42)**2))
def width0(z):return .8+.25*smooth((abs(z)-1.4)/.5)
def seam(u):return a.fracture_center_material_z-.45*u+.012*math.sin(39*u)
def crack_progress(f):return smooth((min(f,LAST)-CRACK_START)/(LAST-CRACK_START))
def opening_fraction(u,y,f):
 pp=crack_progress(f);front=-.08+.15984*pp
 return max(smooth((front-y)/.020),smooth((abs(u-.015625)-.015625)/.15)*smooth((pp-.60)/.40))
def crack_displacement(u,y,z,f):
 pp=crack_progress(f);w=opening_fraction(u,y,f)
 if C['crack_loading_travel']*pp*w<=C['minimum_resolved_opening']:w=0
 t=(z-seam(u))/(2.4-seam(u))
 return C['crack_loading_travel']*pp*(w+(1-w)*t)
def levels(part,u):
 q=seam(u)
 if part==0:return [-2.4,-2.2,-2,-1.85,-1.7,-1.5,-1.3,-1.2,-1.1,-1,-.9,-.8,-.7]+[-.7+(q+.7)*i/12 for i in range(1,13)]
 return [q+( .4-q)*i/12 for i in range(13)]+[.5,.6,.7,.8,.9,1,1.2,1.3,1.5,1.7,1.85,2,2.2,2.4]
def mapper(f):
 grid=[-2.4+4.8*i/400 for i in range(401)];mapped=[-2.4]
 for z1,z2 in zip(grid,grid[1:]):mapped.append(mapped[-1]+(z2-z1)*(lam(z1,f)+lam(z2,f))/2)
 def phi(z):
  t=max(0,min(400,(z+2.4)/4.8*400));i=min(399,int(t));return mapped[i]+(mapped[i+1]-mapped[i])*(t-i)
 return phi

def build(f):
 phi=mapper(f);verts=[];faces=[];mis=[];cache={};split=f>=EVENT
 def vertex(u,y,j,part):
  zs=levels(part,u);z=seam(u) if (part==0 and j==len(zs)-1) or (part==1 and j==0) else zs[j];scale=1/math.sqrt(lam(z,f));v=(u*width0(z)*scale,y*scale,phi(z)+(crack_displacement(u,y,z,f) if part==1 else 0));key=(part,)+v if split else v
  if key not in cache:cache[key]=len(verts);verts.append(v)
  return cache[key]
 def face(pp,mi=0):faces.append(tuple(vertex(*v) for v in pp));mis.append(mi)
 ys=C['thickness_layers'];nr=[len(levels(part,0)) for part in [0,1]]
 for part in [0,1]:
  for i in range(32):
   ua=-.5+i/32;ub=-.5+(i+1)/32
   for j in range(nr[part]-1):
    face([(ua,-.08,j,part),(ub,-.08,j,part),(ub,-.08,j+1,part),(ua,-.08,j+1,part)])
    face([(ua,.08,j+1,part),(ub,.08,j+1,part),(ub,.08,j,part),(ua,.08,j,part)])
   for ya,yb in zip(ys,ys[1:]):
    face([(ua,ya,0,part),(ua,yb,0,part),(ub,yb,0,part),(ub,ya,0,part)],1 if part==1 else 0)
    jj=nr[part]-1;face([(ub,ya,jj,part),(ub,yb,jj,part),(ua,yb,jj,part),(ua,ya,jj,part)],1 if part==0 else 0)
  for j in range(nr[part]-1):
   for ya,yb in zip(ys,ys[1:]):
    face([(-.5,ya,j,part),(-.5,ya,j+1,part),(-.5,yb,j+1,part),(-.5,yb,j,part)])
    face([(.5,yb,j,part),(.5,yb,j+1,part),(.5,ya,j+1,part),(.5,ya,j,part)])
 seen={};discard=set()
 for i,ff in enumerate(faces):
  k=tuple(sorted(ff))
  if k in seen:discard.update([i,seen[k]])
  else:seen[k]=i
 ff=[ff for i,ff in enumerate(faces) if i not in discard];used=sorted({v for face in ff for v in face});remap={v:i for i,v in enumerate(used)};verts=[verts[v] for v in used];ff=[tuple(remap[v] for v in face) for face in ff]
 mesh=bpy.data.meshes.new('retained polymer material');mesh.from_pydata(verts,[],ff);mesh.materials.append(poly);mesh.materials.append(cut);mesh.update()
 for pp,mi in zip(mesh.polygons,[v for i,v in enumerate(mis) if i not in discard]):pp.material_index=mi
 return mesh,phi(2.4)-2.4+C['crack_loading_travel']*crack_progress(f)
obj=bpy.data.objects.new('actual polymer specimen',build(1)[0]);s.collection.objects.link(obj)
def update(f):
 mesh,d=build(f);old=obj.data;obj.data=mesh;bpy.data.meshes.remove(old)
 for o,sg in fixtures:o.location.z=base[o.name]+(d if sg>0 else 0)
 s.frame_set(f);return d

def check(f,coordinates=False):
 d=update(f);dg=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dg);me=ev.to_mesh();vs=[obj.matrix_world@v.co for v in me.vertices];adj=[set() for _ in vs]
 for e in me.edges:u,v=e.vertices;adj[u].add(v);adj[v].add(u)
 seen=set();comps=[]
 for i in range(len(vs)):
  if i in seen:continue
  cc=[];q=[i];seen.add(i)
  while q:
   u=q.pop();cc.append(u)
   for v in adj[u]:
    if v not in seen:seen.add(v);q.append(v)
  comps.append(cc)
 incidence={}
 for pp in me.polygons:
  ix=list(pp.vertices)
  for aa,bb in zip(ix,ix[1:]+ix[:1]):k=tuple(sorted((aa,bb)));incidence[k]=incidence.get(k,0)+1
 me.calc_loop_triangles();volume=abs(sum(vs[t.vertices[0]].dot(vs[t.vertices[1]].cross(vs[t.vertices[2]]))/6 for t in me.loop_triangles))
 kd=KDTree(len(vs))
 for i,v in enumerate(vs):kd.insert(v,i)
 kd.balance();phi=mapper(f)
 def actual(u,y,j,part):
  zz=levels(part,u)[j];sc=1/math.sqrt(lam(zz,f));target=Vector((u*width0(zz)*sc,y*sc,phi(zz)+(crack_displacement(u,y,zz,f) if part==1 else 0)));co,index,dist=kd.find(target);assert dist<1e-5;return co
 paths={}
 for u in [-.5,0,.03125,.5]:
  for y in [-.08,.08]:
   for part in [0,1]:
    pts=[actual(u,y,j,part) for j in range(len(levels(part,u)))];paths[str((u,y,part))]=sum((b-a).length for a,b in zip(pts,pts[1:]))
 sections=[]
 for part,zz in [(0,-1.2),(0,-.8),(1,.8),(1,1.2)]:
  j=levels(part,0).index(zz);pp=[actual(u,y,j,part) for u,y in [(-.5,-.08),(.5,-.08),(.5,.08),(-.5,.08)]];area=sum((pp[i]-pp[0]).cross(pp[i+1]-pp[0]).length/2 for i in [1,2]);sections.append({'material_coordinate_z':zz,'actual_section_corner_area':area,'actual_width':(pp[1]-pp[0]).length,'actual_thickness':(pp[3]-pp[0]).length,'method':'actual matching material corner vertices; quadrilateral two-triangle area'})
 contacts=[]
 for sg in [-1,1]:
  jj=0 if sg<0 else len(levels(1,0))-1;part=0 if sg<0 else 1;points=[actual(u,y,jj,part) for u,y in [(-.5,-.08),(.5,-.08),(.5,.08),(-.5,.08)]];jaw=next(o for o,sign in fixtures if sign==sg and 'physical jaw' in o.name and o.location.y<0);ej=jaw.evaluated_get(dg);jm=ej.to_mesh();jv=[ej.matrix_world@v.co for v in jm.vertices];contacts.append({'end':'lower' if sg<0 else 'upper','actual_front_surface_gap':abs(max(v.y for v in jv)-min(v.y for v in points)),'end_material_vertices_inside_actual_jaw_z_span':all(min(v.z for v in jv)-1e-6<=v.z<=max(v.z for v in jv)+1e-6 for v in points)});ej.to_mesh_clear()
 gauge_points=[actual(0,-.08,levels(part,0).index(zz),part) for part,zz in [(0,-1.2),(1,1.2)]]
 gauge_raw_distance=gauge_points[1].z-gauge_points[0].z
 seam_lower=actual(0,-.08,len(levels(0,0))-1,0);seam_upper=actual(0,-.08,0,1);gauge_seam_opening=seam_upper.z-seam_lower.z
 gauge_length=(seam_lower.z-gauge_points[0].z)+(gauge_points[1].z-seam_upper.z)
 grip_indices=[]
 for part,j in [(0,0),(1,len(levels(1,0))-1)]:
  zz=levels(part,0)[j]; sc=1/math.sqrt(lam(zz,f)); target=Vector((0,-.08*sc,phi(zz)+(crack_displacement(0,-.08,zz,f) if part else 0))); grip_indices.append(kd.find(target)[1])
 actual_grip_path=any(all(ii in cc for ii in grip_indices) for cc in comps)
 lc=[];uc=[];lofaces={};contact_area=0
 for pp in me.polygons:
  if pp.material_index!=1:continue
  points=[vs[i] for i in pp.vertices];key=tuple(sorted(tuple(round(q,8) for q in v) for v in points))
  if pp.normal.z>0:lc.extend(points);lofaces[key]=pp.area
  else:uc.extend(points)
 for pp in me.polygons:
  if pp.material_index==1 and pp.normal.z<0:
   key=tuple(sorted(tuple(round(q,8) for q in vs[i]) for i in pp.vertices))
   if key in lofaces:contact_area+=lofaces[key]
 gaps=[]
 for v in lc:
  if not uc:break
  u=min(uc,key=lambda q:(q.x-v.x)**2+(q.y-v.y)**2);gaps.append(u.z-v.z)
 bound=[world_to_camera_view(s,cam,v) for v in vs]
 for o in [o for o,sg in fixtures]:
  eo=o.evaluated_get(dg);mm=eo.to_mesh();bound.extend(world_to_camera_view(s,cam,eo.matrix_world@v.co) for v in mm.vertices);eo.to_mesh_clear()
 seam_points=[actual(-.5+i/32,y,len(levels(0,-.5+i/32))-1,0) for i in range(33) for y in [-.08,.08]] if f==1 else []
 r={'raw_gauge_marker_axial_distance_including_crack':gauge_raw_distance,'same_material_gauge_seam_opening_axial':gauge_seam_opening,'material_gauge_definition':'sum of lower and upper same-material axial projections between gauge markers and their same-material seam boundaries, excludes seam opening; raw marker distance separately reported','actual_initial_full_fracture_material_z_bounds':[min(v.z for v in seam_points),max(v.z for v in seam_points)] if seam_points else None,'same_material_gauge_axial_projection_length':gauge_length,'gauge_length_ratio':gauge_length/2.4,'gauge_marker_material_z':[-1.2,1.2],'complete_material_sections_excluding_fracture_zone':sections,'material_graph_grip_path_exists':actual_grip_path,'evaluated_coordinate_sha256':hashlib.sha256(b''.join(struct.pack('<ddd',*v) for v in vs)).hexdigest(),'evaluated_topology_sha256':hashlib.sha256(str([tuple(pp.vertices) for pp in me.polygons]).encode()).hexdigest(),'frame':f,'time_s':(f-1)/30,'measured_components':len(comps),'component_vertex_counts':[len(cc) for cc in comps],'actual_material_vertex_count':len(vs),'actual_material_face_count':len(me.polygons),'closed_manifold_edge_incidence':all(n==2 for n in incidence.values()),'measured_material_volume':volume,'same_material_boundary_path_lengths':paths,'actual_material_sections':sections,'actual_grip_contacts':contacts,'upper_fixture_displacement':d,'fracture_gap_z_minmax':[min(gaps),max(gaps)] if gaps else None,'fracture_penetration':min(gaps)<-1e-6 if gaps else False,'actual_zero_opening_contact_area':contact_area,'top_to_bottom_material_graph_path_exists':any(any(vs[i].z<-2.0 for i in cc) and any(vs[i].z>phi(2)+d-(phi(2.4)-2.4)-.001 for i in cc) for cc in comps),'all_evaluated_meshes_in_frame':all(0<=q.x<=1 and 0<=q.y<=1 and q.z>0 for q in bound),'camera_projected_xy_bounds':[min(q.x for q in bound),max(q.x for q in bound),min(q.y for q in bound),max(q.y for q in bound)]}
 if coordinates:r['coordinates']=[list(v) for v in vs];r['fixture_coordinates']=[list(o.location) for o,sg in fixtures]
 ev.to_mesh_clear();return r
keys=sorted(set([1,241,CRACK_START,CRACK_START+1,LAST-2,LAST-1,LAST,EVENT,EVENT+1,556,600]));checks=[check(f,True) for f in keys];pre=next(r for r in checks if r['frame']==LAST);post=next(r for r in checks if r['frame']==EVENT);transition={'last_connected_frame':LAST,'first_separated_frame':EVENT,'unique_material_coordinate_sets_identical':set(tuple(v) for v in pre['coordinates'])==set(tuple(v) for v in post['coordinates']),'maximum_same_material_path_change':max(abs(v-post['same_material_boundary_path_lengths'][k]) for k,v in pre['same_material_boundary_path_lengths'].items()),'fixture_max_displacement':max(abs(x-y) for aa,bb in zip(pre['fixture_coordinates'],post['fixture_coordinates']) for x,y in zip(aa,bb)),'volume_difference':post['measured_material_volume']-pre['measured_material_volume']}
fixed=[r for r in checks if r['frame']>=EVENT];maxmotion=max(abs(x-y) for r in fixed for aa,bb in zip(post['coordinates'],r['coordinates']) for x,y in zip(aa,bb))
for r in checks:r.pop('coordinates');r.pop('fixture_coordinates')
summary={'config':C,'samples':checks,'transition':transition,'postfracture_max_material_vertex_motion':maxmotion,'scope':'actual single-object mesh edge connectivity/manifold incidence, material corner path lengths/areas, closed material volume, evaluated jaw surface contact, complementary seam clearance, actual camera projection; no force balance or general self-intersection solver'}
(out/'config.json').write_text(json.dumps(C,indent=2));(out/'mesh_checks.json').write_text(json.dumps(summary,indent=2))
if not a.checks_only:
 for f in keys:update(f);s.render.filepath=str(out/'previews'/f'frame_{f:04d}.png');bpy.ops.render.render(write_still=True)
update(600);bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene_final_state.blend'))
# Always check all600 frames; rendering remains optional.
results=[]
for f in range(1,601):
 results.append(check(f))
 if a.render:s.render.filepath=str(out/'frames'/f'frame_{f:04d}.png');bpy.ops.render.render(write_still=True)
 if f%100==0:print('CHECK_PROGRESS',f,flush=True)
initial=results[0]
for r in results:
 r['gauge_length_ratio']=r['same_material_gauge_axial_projection_length']/initial['same_material_gauge_axial_projection_length']
 for q,q0 in zip(r['actual_material_sections'],initial['actual_material_sections']):q['area_ratio_to_same_initial_section']=q['actual_section_corner_area']/q0['actual_section_corner_area']
full_summary={'frames_measured':len(results),'first_material_grip_path_loss_frame':next(r['frame'] for r in results if not r['material_graph_grip_path_exists']),'first_measured_opening_frame':next(r['frame'] for r in results if r['fracture_gap_z_minmax'] and max(r['fracture_gap_z_minmax'])>1e-7),'first_crack_pre_measurement':results[CRACK_START-1],'final_connected_pre_measurement':results[LAST-1],'all_grip_contacts':all(c['end_material_vertices_inside_actual_jaw_z_span'] for r in results for c in r['actual_grip_contacts']),'max_grip_surface_gap':max(c['actual_front_surface_gap'] for r in results for c in r['actual_grip_contacts']),'all_in_frame':all(r['all_evaluated_meshes_in_frame'] for r in results),'fracture_penetration_found':any(r['fracture_penetration'] for r in results),'all_post_event_coordinate_hashes_identical':len({r['evaluated_coordinate_sha256'] for r in results if r['frame']>=EVENT})==1,'all_post_event_fixture_displacements_identical':len({r['upper_fixture_displacement'] for r in results if r['frame']>=EVENT})==1,'volume_ratio_range':[min(r['measured_material_volume']/initial['measured_material_volume'] for r in results),max(r['measured_material_volume']/initial['measured_material_volume'] for r in results)],'area_measurement_scope':'tracked intact sections at materialz -1.2,-.8,.8,1.2; excludes whole oblique fracture zone; not a global minimum search or necking proof'}
summary['all_frame_summary']=full_summary
(out/'mesh_checks.json').write_text(json.dumps(summary,indent=2))
(out/'all_frame_mesh_checks.json').write_text(json.dumps(results,indent=2))
