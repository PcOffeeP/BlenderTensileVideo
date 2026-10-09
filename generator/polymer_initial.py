"""Source-constrained qualitative polymer candidates, implementation 1.3.0.

Blender --background --python generator/polymer_initial.py -- --style dogbone|film
  --out <directory> [--keys-only]
Uses no files in _work; renders frames and evaluated-mesh measurements.
Specific material constitutive properties are unknown. This is author-controlled
geometry animation, not calibrated mechanics or approval of a parameter range.
"""
import bpy, math, json, sys, argparse, hashlib, struct
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

VERSION = 'polymer-initial/1.3.0'
STRETCH_FACTOR_CHOICES=(.85,.90,.925,.95,.975,1.,1.15)
EVENT_TIME_CHOICES=(12.,15.,16.,16.5,17.)
ap=argparse.ArgumentParser(); ap.add_argument('--style',choices=['dogbone','film'],required=True)
ap.add_argument('--out',required=True); ap.add_argument('--keys-only',action='store_true')
ap.add_argument('--checks-only',action='store_true')
ap.add_argument('--stretch-increment-factor',type=float,choices=STRETCH_FACTOR_CHOICES,default=1.)
ap.add_argument('--fracture-material-fraction',type=float,default=None)
ap.add_argument('--event-time-s',type=float,choices=EVENT_TIME_CHOICES,default=16.)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
film=args.style=='film'; N=180; fps=30; rupture=args.event_time_s
if film and (args.stretch_increment_factor!=1. or args.fracture_material_fraction is not None or rupture!=16.): ap.error('variation parameters apply only to dogbone; film keeps its accepted fixed configuration')
fraction=12/N if film else (.5 if args.fracture_material_fraction is None else args.fracture_material_fraction)
if not film and (not math.isfinite(fraction) or not .4<=fraction<=.6 or abs(fraction*N-round(fraction*N))>1e-7): ap.error('dogbone fracture fraction must be a material ring in [0.4,0.6], inside authored gauge')
K=round(fraction*N); EVENT=round(rupture*fps)+1; STOP=rupture+2.5
cfg={'implementation_version':VERSION,'style':args.style,'duration_s':20,'fps':fps,'resolution':[960,540],
 'rupture_s':rupture,'end_motion_s':STOP,'axis':'Z','fixed_end':'lower','loading_end':'upper',
 'rest_exposed_span_author_units':3.0 if film else 2.8,'max_local_axial_stretch':2.05 if film else 1+2*args.stretch_increment_factor,
 'film_uniform_width':0.46,'dogbone_gauge_width':0.26,'dogbone_end_width':0.70,
 'thickness_author_units':0.024 if film else 0.075,'initial_grip_embed':0.20,
 'post_relaxation_gauge_stretch':1.85 if film else 1.18,'camera_fixed':True,'camera_position':[3,-25,4.6],'camera_target':[0,0,2.45],'orthographic_scale':18.0,
 'cross_section':'rectangular strip','axial_intervals':180,'fracture_material_ring':K,'renderer':'BLENDER_WORKBENCH','anti_alias_samples':8,
 'contact_jaw_size':[1.12,.4,.24],'contact_jaw_z_center_offset':.10,'color': [.76,.71,.08] if film else [.105,.12,.135],
 'model':'prescribed material-coordinate stretch and finite damped flexible unloading; no deleted material',
 'machine_connection':{'revision_scope':'only visible mechanical support and camera envelope; specimen unchanged',
 'lower_chain':['lower_contact_jaw','lower_grip_cap','lower_load_rod','test_base','test_frame'],
 'upper_chain':['upper_contact_jaw','upper_grip_cap','upper_load_rod','moving_crosshead','hollow_guide_sleeves','test_frame'],
 'moving_crosshead_size':[4.10,1.38,.30],'moving_crosshead_y':.30,'moving_crosshead_above_upper_material_end':.55,
 'grip_cap_size':[1.12,.95,.14],'grip_cap_center_offset':.09,'load_rod_radius':.12,
 'upper_rod_z_offsets':[.16,.40],'lower_rod_base_z':-1.95,
 'guide_rail_size':[.30,.50,9.25],'guide_rail_x':[-2.35,2.35],'guide_rail_y':.60,
 'guide_rail_z_center':2.525,'fixed_top_crossmember_z':7.15,'fixed_top_crossmember_size':[5.3,.7,.35],
 'hollow_sleeve_outer_section':[.60,.78],'hollow_sleeve_inner_section':[.32,.52],
 'hollow_sleeve_height':.64,'nominal_guide_clearance_per_side':.01,
 'scope':'qualitative load path and guide geometry; no calibrated machine actuator or stress model'},
 'motion_configuration':{'loading_curve':f'smoothstep(t/{rupture})','unload_curve':'smoothstep(tau/.45)',
 'finite_motion_duration_s':2.5,'fade':'exp(-1.65*tau)*smoothstep((2.5-tau)/.65)',
 'upper_bend_radian_amplitude':2.2 if film else .36,'upper_bend_angular_frequency':7.5,
 'lower_bend_radian_amplitude':0 if film else .38,'lower_bend_angular_frequency':8,
 'upper_settled_bend_radians':.05 if film else 0,'fixed_grip_rings':12,
 'mask': 'smoothstep((u-.065)/.045)*smoothstep((.935-u)/.045)' if film else 'smoothstep((u-.10)/.13)*smoothstep((.90-u)/.13)',
 'transverse_scale':'inverse square root of local axial stretch','cross_section_orientation':'local centerline tangent normal'},
 'range_status':'only this discrete candidate; not calibrated physics or approved continuous range'}

cfg['stage1']={'stretch_increment_factor':args.stretch_increment_factor,'stretch_increment_definition':'lambda_candidate-1=k*(lambda_baseline-1)','baseline_max_local_axial_stretch':2.05 if film else 3.,'fracture_material_fraction':fraction,'authored_gauge_fraction':[.23,.77] if not film else None,'gauge_marker_rings':[54,126] if not film else [30,150],'first_topology_split_frame':EVENT,'first_crack_pre_frame':EVENT-1,'final_connected_pre_frame':EVENT-1,'post_motion_stop_frame':round(STOP*fps)+1,'engineering_position_guard':[.4,.6] if not film else None,'source_formal_gauge':'unknown','allowed_stretch_increment_factors':list(STRETCH_FACTOR_CHOICES) if not film else [1.],'allowed_event_times_s':list(EVENT_TIME_CHOICES) if not film else [16.],'default_stretch_increment_factor':1.,'default_event_time_s':16.,'scope':'Stage1 and training-batch1 variation inputs apply only to dogbone; film is fixed. New values and combinations require applicable checks and user acceptance; dogbone factor1.15 remains supported for diagnosis but failed fixed-camera framing and is excluded from training-batch1. Ring-grid position guard is not range approval.','baseline_implementation_version':'polymer-initial/1.1.1','film_stage1_parameters_open':False}

def smooth(x): x=max(0.,min(1.,x)); return x*x*(3-2*x)
def mask(u):
 if film: return smooth((u-.065)/.045)*smooth((.935-u)/.045)
 return smooth((u-.10)/.13)*smooth((.90-u)/.13)
def width0(u): return .46 if film else .70-.44*mask(u)
REST=cfg['rest_exposed_span_author_units']+.4
# Preserve the baseline frame; extra selected loading travel requires equal fixed
# rail/top-member extension so the moving guides retain the original clearance.
base_span=sum(REST/N*((1+2*mask(i/N))+(1+2*mask((i+1)/N)))/2 for i in range(N))
selected_span=sum(REST/N*((1+(cfg['max_local_axial_stretch']-1)*mask(i/N))+(1+(cfg['max_local_axial_stretch']-1)*mask((i+1)/N)))/2 for i in range(N))
frame_extension=max(0.,selected_span-base_span) if not film else 0.
cfg['machine_connection']['fixed_frame_extension_for_selected_loading_travel']=frame_extension
cfg['machine_connection']['guide_rail_size'][2]+=frame_extension
cfg['machine_connection']['guide_rail_z_center']+=frame_extension/2
cfg['machine_connection']['fixed_top_crossmember_z']+=frame_extension
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
rails=[box('left_test_frame',(-2.35,.6,2.525+frame_extension/2),(.3,.5,9.25+frame_extension),steel),
 box('right_test_frame',(2.35,.6,2.525+frame_extension/2),(.3,.5,9.25+frame_extension),steel)]
box('lab_backdrop',(0,1.4,2.2),(13,.15,14),mat('backdrop',(.48,.52,.56)))
base=box('test_base',(0,.4,-2.1),(5.4,1.4,.3),dark)
fixed_crossmember=box('top_crossmember',(0,.4,7.15+frame_extension),(5.3,.7,.35),dark)
caps={end:box(end+'_grip_cap',(0,0,0),(1.12,.95,.14),dark) for end in ['lower','upper']}
def rod(name):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.12,depth=1,location=(0,0,0))
 ob=bpy.context.object; ob.name=name; ob.data.materials.append(steel); return ob
rods={end:rod(end+'_load_rod') for end in ['lower','upper']}
crosshead=box('moving_crosshead',(0,.30,0),(4.10,1.38,.30),dark)
# Four physical walls make each sleeve hollow. The moving crosshead contacts the
# inner wall; its opening leaves .01 clearance around the fixed rectangular rail.
sleeves=[]
for x in [-2.35,2.35]:
 for sx in [-1,1]:
  sleeves.append(box('guide_side_wall',(x+sx*.23,.60,0),(.14,.78,.64),steel,bevel=0))
 for sy in [-1,1]:
  sleeves.append(box('guide_front_back_wall',(x,.60+sy*.325,0),(.32,.13,.64),steel,bevel=0))
mechanism=list(caps.values())+list(rods.values())+[crosshead]+sleeves+rails+[base,fixed_crossmember]
bpy.ops.object.camera_add(location=(3,-25,4.6)); camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,2.45))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'; camera.data.ortho_scale=18.0; scene.camera=camera
def update(frame):
 t=(frame-1)/fps; v,f,bottom,top=calc(t); mesh.clear_geometry(); mesh.from_pydata(v,[],f); mesh.update()
 for ob,end,y in jaws:
  ob.location.z=(bottom+.10) if end=='lower' else (top-.10)
 caps['lower'].location.z=bottom-.09; caps['upper'].location.z=top+.09
 for end,lo,hi in [('lower',-1.95,bottom-.16),('upper',top+.16,top+.40)]:
  rods[end].location.z=(lo+hi)/2; rods[end].scale.z=hi-lo
 crosshead.location.z=top+.55
 for ob in sleeves: ob.location.z=crosshead.location.z
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
def world_bounds(ob,dg):
 ev=ob.evaluated_get(dg); m=ev.to_mesh(); points=[ob.matrix_world@p.co for p in m.vertices]
 result=[[min(p[a] for p in points),max(p[a] for p in points)] for a in range(3)]
 ev.to_mesh_clear(); return result
def machine_measurements(dg,bottom,top):
 bounds={o.name:world_bounds(o,dg) for o in mechanism}
 def gap(a,b,axis):
  aa=bounds[a.name][axis]; bb=bounds[b.name][axis]
  return max(aa[0],bb[0])-min(aa[1],bb[1])
 contacts=[]
 for end in ['lower','upper']:
  jaw=next(o for o,e,y in jaws if e==end and y<-.1)
  jb=world_bounds(jaw,dg); cb=bounds[caps[end].name]
  contact_gap=(cb[2][0]-jb[2][1]) if end=='upper' else (jb[2][0]-cb[2][1])
  contacts.append({'joint':end+'_jaw_to_cap','axial_surface_gap':contact_gap})
  contacts.append({'joint':end+'_cap_to_load_rod','axial_surface_gap':gap(caps[end],rods[end],2)})
 contacts.append({'joint':'lower_rod_to_base','axial_surface_gap':gap(rods['lower'],base,2)})
 contacts.append({'joint':'upper_rod_to_crosshead','axial_surface_gap':gap(rods['upper'],crosshead,2)})
 for side in [-1,1]:
  wall=next(o for o in sleeves if o.name.startswith('guide_side_wall') and abs(o.location.x-side*2.12)<1e-5)
  contacts.append({'joint':f'crosshead_to_{side}_guide_sleeve','lateral_surface_gap':gap(crosshead,wall,0)})
 clearances=[]
 for rail in rails:
  x=rail.location.x; rb=bounds[rail.name]
  walls=[o for o in sleeves if abs(o.location.x-x)<.4]
  left=next(o for o in walls if o.name.startswith('guide_side_wall') and o.location.x<x)
  right=next(o for o in walls if o.name.startswith('guide_side_wall') and o.location.x>x)
  front=next(o for o in walls if o.name.startswith('guide_front_back_wall') and o.location.y<.6)
  back=next(o for o in walls if o.name.startswith('guide_front_back_wall') and o.location.y>.6)
  clearances.append({'rail':rail.name,'actual_evaluated_hollow_sleeve_clearances':[
   rb[0][0]-bounds[left.name][0][1],bounds[right.name][0][0]-rb[0][1],
   rb[1][0]-bounds[front.name][1][1],bounds[back.name][1][0]-rb[1][1]]})
 return {'contacts':contacts,'guide_clearances':clearances,
  'actual_sleeve_to_fixed_top_crossmember_clearances':[bounds[fixed_crossmember.name][2][0]-bounds[o.name][2][1] for o in sleeves],
  'actual_crosshead_to_fixed_top_crossmember_clearance':bounds[fixed_crossmember.name][2][0]-bounds[crosshead.name][2][1],
  'upper_cap_to_specimen_end_clearance':bounds[caps['upper'].name][2][0]-top,
  'lower_cap_to_specimen_end_clearance':bottom-bounds[caps['lower'].name][2][1],
  'crosshead_z':crosshead.location.z,'upper_jaw_to_crosshead_z_offset':crosshead.location.z-(top-.10),
  'lower_rod_evaluated_bounds':bounds[rods['lower'].name],
  'note':'fixed frame-to-base and top member joints are designed fastening overlaps; moving hollow guides have positive clearance, not solid boxes intersecting rails'}
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
 for ob in mechanism:
  oe=ob.evaluated_get(dg); om=oe.to_mesh(); projected += [world_to_camera_view(scene,camera,ob.matrix_world@p.co) for p in om.vertices]; oe.to_mesh_clear()
 framing=[min(p.x for p in projected),max(p.x for p in projected),min(p.y for p in projected),max(p.y for p in projected)]
 g0,g1=cfg['stage1']['gauge_marker_rings']; gauge=sum((rings[i+1]-rings[i]).length for i in range(g0,g1)) if t<rupture else None
 sections=[]
 for i in range(g0,g1+1):
  if abs(i-K)<=1:continue
  pp=[m.vertices[4*i+j].co for j in range(4)]; aa=(pp[1]-pp[0]).cross(pp[3]-pp[0]).length
  sections.append({'material_ring':i,'material_fraction':i/N,'area':aa,'area_ratio_to_same_initial_section':aa/(width0(i/N)*cfg['thickness_author_units'])})
 result={'same_material_gauge_arc_length':gauge,'gauge_length_ratio':gauge/(REST*(g1-g0)/N) if gauge is not None else None,'complete_material_sections_excluding_fracture_rings':sections,'minimum_complete_section_ratio':min(q['area_ratio_to_same_initial_section'] for q in sections),'fracture_section_area_available':t<rupture,'actual_fracture_material_fraction':K/N,'actual_initial_fracture_material_fraction_from_ring_centroid':(rings[K].z-rings[0].z)/(rings[N].z-rings[0].z) if frame==1 else None,'material_graph_grip_path_exists':any(0 in gg and 4*N in gg for gg in g),'evaluated_coordinate_sha256':hashlib.sha256(b''.join(struct.pack('<ddd',*q) for q in v)).hexdigest(),'evaluated_topology_sha256':hashlib.sha256(str([tuple(pp.vertices) for pp in m.polygons]).encode()).hexdigest(),'machine_connections':machine_measurements(dg,v[0][2],v[4*N][2]),'projected_specimen_jaw_and_machine_bounds':framing,'all_specimen_and_jaws_inside_frame':all(0<=x<=1 for x in framing),'frame':frame,'time_s':t,'measured_components':len(g),'volume_author_units3':volume,'material_arc_length':arc,
  'central_cross_section_area':area,'grip_measurements':contact,'component_z_bounds':minz,'axial_gap':gap,
  'vertices':v,'jaw_positions':[tuple(o.location) for o,e,y in jaws]}
 ev.to_mesh_clear(); return result

sample_frames=[1,121,301,451,480,481,482,486,496,511,541,556,571,600]
checks=[measure(f) for f in range(1,601)]
baseline=checks[0]['volume_author_units3']
initial_sections={q['material_ring']:q['area'] for q in checks[0]['complete_material_sections_excluding_fracture_rings']}
initial_gauge_length=checks[0]['same_material_gauge_arc_length']
for r in checks:
 r['volume_ratio_to_initial']=r['volume_author_units3']/baseline
 if r['same_material_gauge_arc_length'] is not None:r['gauge_length_ratio']=r['same_material_gauge_arc_length']/initial_gauge_length
 for q in r['complete_material_sections_excluding_fracture_rings']:q['area_ratio_to_same_initial_section']=q['area']/initial_sections[q['material_ring']]
 r['minimum_complete_section_ratio']=min(q['area_ratio_to_same_initial_section'] for q in r['complete_material_sections_excluding_fracture_rings'])
last=checks[-1]; prev=checks[-2]
motion=max((Vector(a)-Vector(b)).length for a,b in zip(last['vertices'],prev['vertices']))
postmax=max((Vector(a)-Vector(b)).length for r0,r1 in zip(checks,checks[1:]) if r0['time_s']>=STOP for a,b in zip(r0['vertices'],r1['vertices']))
summary={'frames_measured':len(checks),'all_grip_endpoints_in_actual_jaws':all(g['axial_grip_overlap'] for r in checks for g in r['grip_measurements']),
 'max_contact_surface_gap':max(g['surface_gap'] for r in checks for g in r['grip_measurements']),
 'all_specimen_and_jaws_inside_frame':all(r['all_specimen_and_jaws_inside_frame'] for r in checks),
 'volume_ratio_bounds':[min(r['volume_ratio_to_initial'] for r in checks),max(r['volume_ratio_to_initial'] for r in checks)],
 'first_two_component_frame':next(r['frame'] for r in checks if r['measured_components']==2),
 'minimum_axial_component_gap_after_first_split':min(r['axial_gap'] for r in checks if r['time_s']>rupture),
 'max_vertex_step_after_motion_stop':postmax,'motion_stop_s':STOP,'first_measured_positive_component_gap_frame':next(r['frame'] for r in checks if r['axial_gap']>1e-6),'first_crack_pre_measurement':next(r for r in checks if r['frame']==EVENT-1).copy(),'final_connected_pre_measurement':next(r for r in checks if r['frame']==EVENT-1).copy(), 'post_event_upper_jaw_position_step':max((Vector(aa)-Vector(bb)).length for r,q in zip(checks,checks[1:]) if r['frame']>=EVENT for aa,bb in zip(r['jaw_positions'],q['jaw_positions'])), 'rigid_grip_regions_verified_by_construction_and_endpoint_contact':'all12gripmaterialrings have strain1 and zero prescribed bend'}
summary['machine_connections']={
 'max_absolute_joint_surface_gap':max(abs(next(v for k,v in c.items() if k.endswith('surface_gap'))) for r in checks for c in r['machine_connections']['contacts']),
 'minimum_actual_guide_clearance':min(v for r in checks for c in r['machine_connections']['guide_clearances'] for v in c['actual_evaluated_hollow_sleeve_clearances']),
 'minimum_actual_cap_to_specimen_end_clearance':min(r['machine_connections'][k] for r in checks for k in ['upper_cap_to_specimen_end_clearance','lower_cap_to_specimen_end_clearance']),
 'minimum_actual_sleeve_to_fixed_top_crossmember_clearance':min(v for r in checks for v in r['machine_connections']['actual_sleeve_to_fixed_top_crossmember_clearances']),
 'minimum_actual_crosshead_to_fixed_top_crossmember_clearance':min(r['machine_connections']['actual_crosshead_to_fixed_top_crossmember_clearance'] for r in checks),
 'crosshead_relative_to_upper_jaw_z_offset_range':[min(r['machine_connections']['upper_jaw_to_crosshead_z_offset'] for r in checks),max(r['machine_connections']['upper_jaw_to_crosshead_z_offset'] for r in checks)],
 'all_machine_and_specimen_inside_frame':all(r['all_specimen_and_jaws_inside_frame'] for r in checks)}
for r in checks: del r['vertices']
for k in ['first_crack_pre_measurement','final_connected_pre_measurement']: summary[k].pop('vertices',None)
report={'all_frame_summary':summary,'configuration':cfg,'evaluated_mesh_checks':checks,'motion_19_to_19_9667_max_vertex_delta':motion,
 'limits':['prescribed mesh motion, not constitutive prediction','material identity from source spreadsheet',
 '3D fracture microgeometry unresolved in source; planar edge used','no external physics validation or user acceptance'],
 'camera_transform':list(camera.matrix_world[0])+list(camera.matrix_world[1])+list(camera.matrix_world[2])}
(out/'mesh_checks.json').write_text(json.dumps(report,indent=2))
(out/'configuration.json').write_text(json.dumps(cfg,indent=2))
if not summary['all_specimen_and_jaws_inside_frame'] and not args.checks_only:raise RuntimeError('selected loading travel extends the fixed machine outside the fixed camera; see mesh_checks.json; do not render/promote before presentation decision')
keys=sorted(set([1,241,round(EVENT*.9),EVENT-1,EVENT,EVENT+1,EVENT+15,round(STOP*fps)+1,600]))
for frame in ([] if args.checks_only else keys):
 scene.frame_set(frame); update(frame); scene.render.filepath=str(out/f'key_{frame:04d}.png'); bpy.ops.render.render(write_still=True)
update(1); bpy.ops.wm.save_as_mainfile(filepath=str(out/(args.style+'_initial.blend')))
if not args.keys_only and not args.checks_only:
 frames=out/'frames'; frames.mkdir(exist_ok=True)
 for frame in range(1,601):
  scene.frame_set(frame); update(frame); scene.render.filepath=str(frames/f'{frame:06d}.png'); bpy.ops.render.render(write_still=True)
print('POLYMER_DONE',args.style,str(out),flush=True)
