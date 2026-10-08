"""Source-constrained qualitative polymer candidates, implementation 1.0.

Blender --background --python generator/polymer_initial.py -- --style dogbone|film
  --out <directory> [--keys-only]
Uses no files in _work; renders frames and evaluated-mesh measurements.
Specific material constitutive properties are unknown. This is author-controlled
geometry animation, not calibrated mechanics or approval of a parameter range.
"""
import bpy, math, json, sys, argparse
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

VERSION = 'polymer-initial/1.0'
ap=argparse.ArgumentParser(); ap.add_argument('--style',choices=['dogbone','film'],required=True)
ap.add_argument('--out',required=True); ap.add_argument('--keys-only',action='store_true')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
film=args.style=='film'; N=180; K=12 if film else 90; fps=30; rupture=16.0
cfg={'implementation_version':VERSION,'style':args.style,'duration_s':20,'fps':fps,'resolution':[960,540],
 'rupture_s':rupture,'end_motion_s':18.5,'axis':'Z','fixed_end':'lower','loading_end':'upper',
 'rest_exposed_span_author_units':3.0 if film else 2.8,'max_local_axial_stretch':2.05 if film else 3.0,
 'film_uniform_width':0.46,'dogbone_gauge_width':0.26,'dogbone_end_width':0.70,
 'thickness_author_units':0.024 if film else 0.075,'initial_grip_embed':0.20,
 'post_relaxation_gauge_stretch':1.85 if film else 1.18,'camera_fixed':True,'camera_position':[3,-25,4.6],'camera_target':[0,0,2.2],'orthographic_scale':15.5,
 'cross_section':'rectangular strip','axial_intervals':180,'fracture_material_ring':K,'renderer':'BLENDER_WORKBENCH','anti_alias_samples':8,
 'contact_jaw_size':[1.12,.4,.24],'contact_jaw_z_center_offset':.10,'color': [.76,.71,.08] if film else [.105,.12,.135],
 'model':'prescribed material-coordinate stretch and finite damped flexible unloading; no deleted material',
 'motion_configuration':{'loading_curve':'smoothstep(t/16)','unload_curve':'smoothstep(tau/.45)',
 'finite_motion_duration_s':2.5,'fade':'exp(-1.65*tau)*smoothstep((2.5-tau)/.65)',
 'upper_bend_radian_amplitude':2.2 if film else .36,'upper_bend_angular_frequency':7.5,
 'lower_bend_radian_amplitude':0 if film else .38,'lower_bend_angular_frequency':8,
 'upper_settled_bend_radians':.05 if film else 0,'fixed_grip_rings':12,
 'mask': 'smoothstep((u-.065)/.045)*smoothstep((.935-u)/.045)' if film else 'smoothstep((u-.10)/.13)*smoothstep((.90-u)/.13)',
 'transverse_scale':'inverse square root of local axial stretch','cross_section_orientation':'local centerline tangent normal'},
 'range_status':'only this discrete candidate; not calibrated physics or approved continuous range'}

def smooth(x): x=max(0.,min(1.,x)); return x*x*(3-2*x)
def mask(u):
 if film: return smooth((u-.065)/.045)*smooth((.935-u)/.045)
 return smooth((u-.10)/.13)*smooth((.90-u)/.13)
def width0(u): return .46 if film else .70-.44*mask(u)
REST=cfg['rest_exposed_span_author_units']+.4
def calc(t):
 p=smooth(t/rupture); broken=t>=rupture
 tau=max(0.,t-rupture); unload=smooth(tau/.45) if broken else 0
 # Source0097 shows strong shortening;0025 retains a long flexible strip.
 target=cfg['post_relaxation_gauge_stretch']
 local=[1+(cfg['max_local_axial_stretch']-1)*p*mask(i/N) for i in range(N+1)]
 if broken: local=[v+(1+(target-1)*mask(i/N)-v)*unload for i,v in enumerate(local)]
 lengths=[REST/N*(local[i]+local[i+1])/2 for i in range(N)]
 loaded=[1+(cfg['max_local_axial_stretch']-1)*mask(i/N) for i in range(N+1)]
 stop_span=sum(REST/N*(loaded[i]+loaded[i+1])/2 for i in range(N))
 pre_span=sum(lengths); bottom=-1.6 if film else -1.5
 top=bottom+(stop_span if broken else pre_span)
 center=[Vector((0,0,bottom))]
 for i,L in enumerate(lengths): center.append(center[-1]+Vector((0,0,L)))
 if broken:
  duration=2.5; fade=math.exp(-tau*1.65)*smooth((duration-tau)/.65) if tau<duration else 0
  # Tangent integration preserves each axial material segment's arc length.
  lower=[Vector((0,0,bottom))]
  for i in range(K):
   f=max(0,(i+1-12)/max(1,K-12)); angle=(.38 if not film else 0)*fade*math.sin(tau*8)*f*f
   lower.append(lower[-1]+Vector((math.sin(angle)*lengths[i],0,math.cos(angle)*lengths[i])))
  upper={N:Vector((0,0,top))}
  for i in range(N-1,K-1,-1):
   f=max(0,(N-i-12)/max(1,N-K-12)); angle=((2.2 if film else .36)*fade*math.sin(tau*7.5)+(.05 if film else 0)*smooth(tau/.5))*f*f
   upper[i]=upper[i+1]+Vector((math.sin(angle)*lengths[i],0,-math.cos(angle)*lengths[i]))
  center=lower+[upper[i] for i in range(K+1,N+1)]
  upper_cut=upper[K]
 else: upper_cut=center[K]
 verts=[]
 def width_axis(i,cut=False):
  if cut: tangent=center[K+1]-upper_cut
  elif i==0: tangent=center[1]-center[0]
  elif i==N: tangent=center[N]-center[N-1]
  elif broken and i==K: tangent=center[K]-center[K-1]
  elif broken and i==K+1: tangent=center[K+2]-upper_cut
  else: tangent=center[i+1]-center[i-1]
  tangent.normalize(); return Vector((tangent.z,0,-tangent.x))
 for i,c in enumerate(center):
  w=width0(i/N)/math.sqrt(local[i]); h=cfg['thickness_author_units']/math.sqrt(local[i])
  for x,y in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]: verts.append(tuple(c+width_axis(i)*x+Vector((0,y,0))))
 if broken:
  w=width0(K/N)/math.sqrt(local[K]); h=cfg['thickness_author_units']/math.sqrt(local[K])
  for x,y in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]: verts.append(tuple(upper_cut+width_axis(K,True)*x+Vector((0,y,0))))
 faces=[]
 for i in range(N):
  a=4*i; b=4*(i+1)
  if broken and i==K: a=4*(N+1)
  for j in range(4): faces.append((a+j,a+(j+1)%4,b+(j+1)%4,b+j))
 faces += [(3,2,1,0),tuple(4*N+j for j in range(4))]
 if broken: faces += [tuple(4*K+j for j in range(4)),tuple(4*(N+1)+j for j in [3,2,1,0])]
 return verts,faces,bottom,top

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene; scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=960; scene.render.resolution_y=540; scene.render.resolution_percentage=100
scene.render.fps=fps; scene.frame_start=1; scene.frame_end=600
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.display.shading.light='STUDIO'; scene.display.shading.studiolight_rotate_z=.45
scene.display.shading.color_type='MATERIAL'; scene.display.shading.show_shadows=False
scene.display.shading.show_cavity=True; scene.display.shading.cavity_type='BOTH'
scene.display.shading.show_specular_highlight=True; scene.display.shading.background_type='WORLD'
scene.world.color=(.045,.058,.073); scene.display.render_aa='8'
def mat(name,c,metal=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*c,1); m.metallic=metal; m.roughness=.3; return m
poly=mat('source_yellow_film' if film else 'source_black_polymer',(.76,.71,.08) if film else (.105,.12,.135))
steel=mat('brushed steel',(.36,.40,.46),1); dark=mat('jaw housing',(.10,.12,.15),1)
mesh=bpy.data.meshes.new('material_coordinate_mesh'); obj=bpy.data.objects.new('specimen',mesh); scene.collection.objects.link(obj); obj.data.materials.append(poly)
def box(name,pos,size,material,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos); ob=bpy.context.object; ob.name=name; ob.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); ob.data.materials.append(material)
 if bevel: mod=ob.modifiers.new('machined_edges','BEVEL'); mod.width=bevel; mod.segments=2; ob.modifiers.new('normals','WEIGHTED_NORMAL')
 return ob
# Front/back jaw surfaces meet the specimen in the declared embedded grip section.
jaws=[]
for end in ['lower','upper']:
 for y in [-.20-cfg['thickness_author_units']/2,.20+cfg['thickness_author_units']/2]:
  jaw=box(end+'_contact_jaw', (0,y,0),(1.12,.4,.24),steel)
  jaws.append((jaw,end,y))
 for x in [-.36,.36]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.075,depth=.055,location=(x,-.47,0),rotation=(math.pi/2,0,0))
  ob=bpy.context.object; ob.name=end+'_jaw_bolt'; ob.data.materials.append(dark); jaws.append((ob,end,-.47))
box('left_test_frame',(-2.35,.6,2.2),(.3,.5,10),steel)
box('right_test_frame',(2.35,.6,2.2),(.3,.5,10),steel)
box('lab_backdrop',(0,1.4,2.2),(13,.15,14),mat('backdrop',(.48,.52,.56)))
box('test_base',(0,.4,-2.1),(5.4,1.4,.3),dark)
box('top_crossmember',(0,.4,7.0),(5.3,.7,.35),dark)
bpy.ops.object.camera_add(location=(3,-25,4.6)); camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,2.2))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'; camera.data.ortho_scale=15.5; scene.camera=camera
def update(frame):
 t=(frame-1)/fps; v,f,bottom,top=calc(t); mesh.clear_geometry(); mesh.from_pydata(v,[],f); mesh.update()
 for ob,end,y in jaws:
  ob.location.z=(bottom+.10) if end=='lower' else (top-.10)
 return t
def components(m):
 adj=[[] for _ in m.vertices]
 for e in m.edges:
  a,b=e.vertices; adj[a].append(b); adj[b].append(a)
 seen=set(); groups=[]
 for a in range(len(adj)):
  if a in seen: continue
  stack=[a]; seen.add(a); g=[]
  while stack:
   q=stack.pop(); g.append(q)
   for k in adj[q]:
    if k not in seen: seen.add(k); stack.append(k)
  groups.append(g)
 return groups
def measure(frame):
 t=update(frame); dg=bpy.context.evaluated_depsgraph_get(); dg.update(); ev=obj.evaluated_get(dg); m=ev.to_mesh(); m.calc_loop_triangles()
 volume=abs(sum(m.vertices[tri.vertices[0]].co.dot(m.vertices[tri.vertices[1]].co.cross(m.vertices[tri.vertices[2]].co))/6 for tri in m.loop_triangles))
 v=[tuple(p.co) for p in m.vertices]; g=components(m)
 # Grip section penetrates into the actual jaw z interval by .20 author units.
 contact=[]
 for end,ring in [('lower',0),('upper',N)]:
  pts=[m.vertices[ring*4+j].co for j in range(4)]
  jaw=next(o for o,e,y in jaws if e==end and y<-.1)
  dg.update(); jm=jaw.evaluated_get(dg).to_mesh(); jw=[jaw.matrix_world@q.co for q in jm.vertices]
  zlo=min(q.z for q in jw); zhi=max(q.z for q in jw)
  contact.append({'end':end,'material_ring_z':sum(p.z for p in pts)/4,'actual_evaluated_jaw_z_bounds':[zlo,zhi],
    'axial_grip_overlap':all(zlo-1e-6<=p.z<=zhi+1e-6 for p in pts),
    'actual_front_contact_face_y':max(q.y for q in jw), 'specimen_front_face_y':min(p.y for p in pts),
    'surface_gap':abs(max(q.y for q in jw)-min(p.y for p in pts)), 'specimen_half_thickness':abs(pts[0].y),
    'note':'actual front jaw surface meets specimen surface; endpoint ring lies inside jaw z interval'})
  jaw.evaluated_get(dg).to_mesh_clear()
 minz=[]
 for group in g: minz.append([min(m.vertices[i].co.z for i in group),max(m.vertices[i].co.z for i in group)])
 gap=minz[1][0]-minz[0][1] if len(g)==2 else 0
 # Actual ring-centroid segment lengths and cross-section area from evaluated vertices.
 rings=[sum((m.vertices[4*i+j].co for j in range(4)),Vector())/4 for i in range(N+1)]
 arc=sum((rings[i+1]-(sum((m.vertices[4*(N+1)+j].co for j in range(4)),Vector())/4 if t>=rupture and i==K else rings[i])).length for i in range(N))
 gauge_i=N//2; pts=[m.vertices[gauge_i*4+j].co for j in range(4)]; area=(pts[1]-pts[0]).length*(pts[3]-pts[0]).length
 projected=[world_to_camera_view(scene,camera,Vector(p)) for p in v]
 for jaw,end,y in jaws:
  je=jaw.evaluated_get(dg); jmesh=je.to_mesh(); projected += [world_to_camera_view(scene,camera,jaw.matrix_world@p.co) for p in jmesh.vertices]; je.to_mesh_clear()
 framing=[min(p.x for p in projected),max(p.x for p in projected),min(p.y for p in projected),max(p.y for p in projected)]
 result={'projected_specimen_and_jaw_bounds':framing,'all_specimen_and_jaws_inside_frame':all(0<=x<=1 for x in framing),'frame':frame,'time_s':t,'measured_components':len(g),'volume_author_units3':volume,'material_arc_length':arc,
  'central_cross_section_area':area,'grip_measurements':contact,'component_z_bounds':minz,'axial_gap':gap,
  'vertices':v,'jaw_positions':[tuple(o.location) for o,e,y in jaws]}
 ev.to_mesh_clear(); return result

sample_frames=[1,121,301,451,480,481,482,486,496,511,541,556,571,600]
checks=[measure(f) for f in (sample_frames if args.keys_only else range(1,601))]
baseline=checks[0]['volume_author_units3']
for r in checks: r['volume_ratio_to_initial']=r['volume_author_units3']/baseline
last=checks[-1]; prev=checks[-2]
motion=max((Vector(a)-Vector(b)).length for a,b in zip(last['vertices'],prev['vertices']))
postmax=max((Vector(a)-Vector(b)).length for r0,r1 in zip(checks,checks[1:]) if r0['time_s']>=18.5 for a,b in zip(r0['vertices'],r1['vertices']))
summary={'frames_measured':len(checks),'all_grip_endpoints_in_actual_jaws':all(g['axial_grip_overlap'] for r in checks for g in r['grip_measurements']),
 'max_contact_surface_gap':max(g['surface_gap'] for r in checks for g in r['grip_measurements']),
 'all_specimen_and_jaws_inside_frame':all(r['all_specimen_and_jaws_inside_frame'] for r in checks),
 'volume_ratio_bounds':[min(r['volume_ratio_to_initial'] for r in checks),max(r['volume_ratio_to_initial'] for r in checks)],
 'first_two_component_frame':next(r['frame'] for r in checks if r['measured_components']==2),
 'minimum_axial_component_gap_after_first_split':min(r['axial_gap'] for r in checks if r['time_s']>16),
 'max_vertex_step_after_18_5s':postmax, 'rigid_grip_regions_verified_by_construction_and_endpoint_contact':'all12gripmaterialrings have strain1 and zero prescribed bend'}
for r in checks: del r['vertices']
report={'all_frame_summary':summary,'configuration':cfg,'evaluated_mesh_checks':checks,'motion_19_to_19_9667_max_vertex_delta':motion,
 'limits':['prescribed mesh motion, not constitutive prediction','material identity from source spreadsheet',
 '3D fracture microgeometry unresolved in source; planar edge used','no external physics validation or user acceptance'],
 'camera_transform':list(camera.matrix_world[0])+list(camera.matrix_world[1])+list(camera.matrix_world[2])}
(out/'mesh_checks.json').write_text(json.dumps(report,indent=2))
(out/'configuration.json').write_text(json.dumps(cfg,indent=2))
keys=[1,241,451,480,482,496,526,556,600]
for frame in keys:
 scene.frame_set(frame); update(frame); scene.render.filepath=str(out/f'key_{frame:04d}.png'); bpy.ops.render.render(write_still=True)
update(1); bpy.ops.wm.save_as_mainfile(filepath=str(out/(args.style+'_initial.blend')))
if not args.keys_only:
 frames=out/'frames'; frames.mkdir(exist_ok=True)
 for frame in range(1,601):
  scene.frame_set(frame); update(frame); scene.render.filepath=str(frames/f'{frame:06d}.png'); bpy.ops.render.render(write_still=True)
print('POLYMER_DONE',args.style,str(out),flush=True)
