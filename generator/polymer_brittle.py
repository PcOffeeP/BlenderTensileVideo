"""Qualitative pale-green brittle polymer flat strip; reference video_0032.

Blender -b --python generator/polymer_brittle.py -- --out <directory> [--keys-only]
Fixed discrete source-constrained configuration. Does not depend on _work.
Not calibrated constitutive mechanics or approval of a continuous parameter range.
"""
import bpy, math, json, sys, argparse, hashlib, struct
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

IMPLEMENTATION='polymer-brittle/1.1.0'
parser=argparse.ArgumentParser(); parser.add_argument('--out',required=True); parser.add_argument('--keys-only',action='store_true')
parser.add_argument('--checks-only',action='store_true')
parser.add_argument('--fracture-material-fraction',type=float,default=.5)
parser.add_argument('--event-time-s',type=float,choices=[12.,15.,16.,17.],default=16.)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
if not math.isfinite(args.fracture_material_fraction) or not .45<=args.fracture_material_fraction<=.55 or abs(args.fracture_material_fraction*160-round(args.fracture_material_fraction*160))>1e-7:parser.error('fracture fraction must be a material ring in [0.45,0.55]')
EVENT=round(args.event_time_s*30)+1
CONFIG={'implementation_version':IMPLEMENTATION,'scope':'only pale-green near-uniform flat-strip small-deformation brittle visual style referenced to video_0032; not all polymers',
 'duration_s':20,'fps':30,'resolution':[960,540],'rupture_time_s':args.event_time_s,'rupture_frame':EVENT,
 'rest_material_length_author_units':4.0,'rest_width_author_units':.18,'rest_thickness_author_units':.035,
 'axial_intervals':160,'fracture_material_fraction':args.fracture_material_fraction,'fracture_edge_slope_degrees':3,
 'author_reference_gauge_material_fraction':[.15,.85],'formal_source_gauge':'unknown',
 'maximum_free_span_elastic_stretch':1.012,'clamped_material_fraction_each_end':.05,'strain_ramp_material_fraction':.025,
 'loading_curve':f'smoothstep(time/{args.event_time_s})','transverse_scale':'local stretch^-0.5, small-strain geometric volume approximation',
 'fracture_motion':f'single event at{args.event_time_s}s releases the prescribed small free-span axial strain; anchored ends remain fixed; graded material-point displacement, no rigid piece translation or deleted material',
 'after_event':f'all material vertices, jaws, caps and load rods constant from{args.event_time_s}s onward; no delayed rebound/sway',
 'camera_position':[2,-25,2],'camera_target':[0,0,.02],'orthographic_scale':9.3,'camera_fixed':True,
 'presentation':'connected grips, caps and load rods close view; rods intentionally exit image, no full machine frame represented',
 'jaw_size':[1.12,.4,.24],'grip_embed_author_units':.20,'grip_cap_size':[1.12,.95,.14],'load_rod_radius':.12,
 'polymer_color':[.64,.77,.50],'renderer':'BLENDER_WORKBENCH','antialias_samples':8,
 'source_phase_retiming':'source excerpt4.544s to authored20s sequence; phase extension, not compression of a measured full experiment',
 'parameter_range_acceptance':False,'stage1':{'baseline_implementation_version':'polymer-brittle/1.0','position_engineering_guard':[.45,.55],'full_fracture_fraction_bounds':[args.fracture_material_fraction-.18/2*math.tan(math.radians(3))/4,args.fracture_material_fraction+.18/2*math.tan(math.radians(3))/4],'first_crack_pre_frame':EVENT-1,'final_connected_pre_frame':EVENT-1,'event_candidates_s':[12,15,17],'default_regression_event_s':16,'stretch_parameter_open':False,'scope':'small deformation brittle only; ring-grid guard is not continuous approval'}}
N=CONFIG['axial_intervals']; K=round(args.fracture_material_fraction*N); FPS=30; REST=4.; WIDTH=.18; THICKNESS=.035
def smooth(x): x=max(0.,min(1.,x)); return x*x*(3-2*x)
def strain_mask(u): return smooth((u-.05)/.025)*smooth((.95-u)/.025)
def coordinates(t):
 broken=t>=args.event_time_s; p=smooth(min(t,args.event_time_s)/args.event_time_s)
 loaded=[1+.012*p*strain_mask(i/N) for i in range(N+1)]
 steps=[REST/N*(loaded[i]+loaded[i+1])/2 for i in range(N)]
 bottom=-2.; top=bottom+sum(steps)
 z=[bottom]
 for step in steps:z.append(z[-1]+step)
 local=loaded[:]
 if broken:
  # Both anchors and the stopped jaws remain fixed. Each half releases its
  # small prescribed elastic strain inside this rupture event only.
  z=[bottom+REST*i/N if i<=K else top-REST*(N-i)/N for i in range(N+1)]
  upper_cut=top-REST*(N-K)/N; local=[1.]*len(local)
 else: upper_cut=z[K]
 vertices=[]
 slope=math.tan(math.radians(CONFIG['fracture_edge_slope_degrees']))
 for i,zi in enumerate(z):
  w=WIDTH/math.sqrt(local[i]); h=THICKNESS/math.sqrt(local[i])
  for x,y in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]:
   vertices.append((x,y,zi+(x*slope if i==K else 0)))
 if broken:
  for x,y in [(-WIDTH/2,-THICKNESS/2),(WIDTH/2,-THICKNESS/2),(WIDTH/2,THICKNESS/2),(-WIDTH/2,THICKNESS/2)]:vertices.append((x,y,upper_cut+x*slope))
 faces=[]
 for i in range(N):
  a=4*(N+1) if broken and i==K else 4*i; b=4*(i+1)
  for j in range(4):faces.append((a+j,a+(j+1)%4,b+(j+1)%4,b+j))
 faces += [(3,2,1,0),tuple(4*N+j for j in range(4))]
 if broken:faces += [tuple(4*K+j for j in range(4)),tuple(4*(N+1)+j for j in [3,2,1,0])]
 return vertices,faces,bottom,top

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene; scene.render.engine='BLENDER_WORKBENCH'; scene.render.resolution_x=960; scene.render.resolution_y=540
scene.render.resolution_percentage=100; scene.render.fps=FPS; scene.frame_start=1; scene.frame_end=600
scene.render.image_settings.file_format='PNG'; scene.display.render_aa='8'
scene.display.shading.light='STUDIO'; scene.display.shading.studiolight_rotate_z=.45; scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=False; scene.display.shading.show_cavity=True; scene.display.shading.cavity_type='BOTH'
scene.display.shading.show_specular_highlight=True; scene.display.shading.background_type='WORLD'; scene.world.color=(.16,.19,.22)
def material(name,color,metal=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.metallic=metal; m.roughness=.3; return m
poly=material('source_pale_green_polymer',CONFIG['polymer_color']); steel=material('steel',(.39,.43,.48),1); dark=material('caps',(.10,.12,.15),1)
mesh=bpy.data.meshes.new('brittle_material_mesh'); specimen=bpy.data.objects.new('specimen',mesh); scene.collection.objects.link(specimen); mesh.materials.append(poly)
def box(name,size,mat,pos=(0,0,0)):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos); o=bpy.context.object; o.name=name; o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(mat)
 mod=o.modifiers.new('machined edges','BEVEL'); mod.width=.025; mod.segments=2; o.modifiers.new('normals','WEIGHTED_NORMAL'); return o
jaws=[]; caps={}; rods={}
for end in ['lower','upper']:
 for y in [-.20-THICKNESS/2,.20+THICKNESS/2]:
  o=box(end+'_contact_jaw',CONFIG['jaw_size'],steel,(0,y,0)); jaws.append((o,end))
 for x in [-.36,.36]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.075,depth=.055,location=(x,-.47,0),rotation=(math.pi/2,0,0))
  o=bpy.context.object; o.name=end+'_jaw_bolt'; o.data.materials.append(dark); jaws.append((o,end))
 caps[end]=box(end+'_connected_cap',CONFIG['grip_cap_size'],dark)
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.12,depth=1,location=(0,0,0))
 rods[end]=bpy.context.object; rods[end].name=end+'_load_rod_to_offscreen_machine'; rods[end].data.materials.append(steel)
box('plain_lab_background',(14,.1,10),material('background',(.42,.46,.50)),(0,1.4,0))
bpy.ops.object.camera_add(location=CONFIG['camera_position']); camera=bpy.context.object
camera.rotation_euler=(Vector(CONFIG['camera_target'])-camera.location).to_track_quat('-Z','Y').to_euler(); camera.data.type='ORTHO'; camera.data.ortho_scale=9.3; scene.camera=camera
def update(frame):
 t=(frame-1)/FPS; vertices,faces,bottom,top=coordinates(t); mesh.clear_geometry(); mesh.from_pydata(vertices,[],faces); mesh.update()
 for ob,end in jaws:ob.location.z=bottom+.10 if end=='lower' else top-.10
 caps['lower'].location.z=bottom-.09; caps['upper'].location.z=top+.09
 for end,lo,hi in [('lower',-3.5,bottom-.16),('upper',top+.16,3.6)]:rods[end].location.z=(lo+hi)/2; rods[end].scale.z=hi-lo
 return t
def evaluated_points(ob,dg):
 e=ob.evaluated_get(dg); m=e.to_mesh(); points=[ob.matrix_world@v.co for v in m.vertices]; e.to_mesh_clear(); return points
def bounds(points):return [[min(p[a] for p in points),max(p[a] for p in points)] for a in range(3)]
def connected_groups(m):
 adjacency=[[] for _ in m.vertices]
 for edge in m.edges:
  a,b=edge.vertices; adjacency[a].append(b); adjacency[b].append(a)
 seen=set(); groups=[]
 for start in range(len(adjacency)):
  if start in seen:continue
  pending=[start]; seen.add(start); group=[]
  while pending:
   a=pending.pop(); group.append(a)
   for b in adjacency[a]:
    if b not in seen:seen.add(b);pending.append(b)
  groups.append(group)
 return groups
def measure(frame):
 t=update(frame); dg=bpy.context.evaluated_depsgraph_get(); dg.update(); e=specimen.evaluated_get(dg); m=e.to_mesh(); m.calc_loop_triangles()
 pts=[v.co.copy() for v in m.vertices]; groups=connected_groups(m)
 volume=abs(sum(pts[a].dot(pts[b].cross(pts[c]))/6 for a,b,c in [tri.vertices for tri in m.loop_triangles]))
 rings=[sum((pts[4*i+j] for j in range(4)),Vector())/4 for i in range(N+1)]
 segments=[]
 for i in range(N):
  a=sum((pts[4*(N+1)+j] for j in range(4)),Vector())/4 if frame>=EVENT and i==K else rings[i]
  segments.append((rings[i+1]-a).length)
 areas=[(pts[4*i+1]-pts[4*i]).length*(pts[4*i+3]-pts[4*i]).length for i in range(N+1)]
 component_bounds=[bounds([pts[i] for i in g]) for g in groups]
 cut_gap=component_bounds[1][2][0]-component_bounds[0][2][1] if len(groups)==2 else 0
 grip_checks=[]; projected=[world_to_camera_view(scene,camera,p) for p in pts]
 for end,ring in [('lower',0),('upper',N)]:
  ringpts=pts[4*ring:4*ring+4]; front=next(o for o,ee in jaws if ee==end and o.name.startswith(end+'_contact_jaw') and o.location.y<0)
  jb=bounds(evaluated_points(front,dg)); cb=bounds(evaluated_points(caps[end],dg)); rb=bounds(evaluated_points(rods[end],dg))
  jaw_to_cap_gap=cb[2][0]-jb[2][1] if end=='upper' else jb[2][0]-cb[2][1]
  cap_to_rod_gap=rb[2][0]-cb[2][1] if end=='upper' else cb[2][0]-rb[2][1]
  grip_checks.append({'end':end,'actual_contact_face_gap':abs(jb[1][1]-min(p.y for p in ringpts)),
   'actual_endpoint_inside_jaw_z_interval':all(jb[2][0]-1e-6<=p.z<=jb[2][1]+1e-6 for p in ringpts),
   'jaw_to_cap_surface_gap':jaw_to_cap_gap,'cap_to_rod_surface_gap':cap_to_rod_gap,
   'cap_to_material_end_clearance':cb[2][0]-rings[-1].z if end=='upper' else rings[0].z-cb[2][1]})
 for ob in [o for o,ee in jaws]+list(caps.values()):projected += [world_to_camera_view(scene,camera,p) for p in evaluated_points(ob,dg)]
 framebounds=[min(p.x for p in projected),max(p.x for p in projected),min(p.y for p in projected),max(p.y for p in projected)]
 # Coordinates hash is from actual evaluated specimen vertices, not intended inputs.
 h=hashlib.sha256()
 for p in pts:h.update(struct.pack('<ddd',*p))
 g0,g1=24,136; gauge=sum(segments[g0:g1]); sections=[{'material_ring':i,'material_fraction':i/N,'area':areas[i],'area_ratio_to_same_initial_section':areas[i]/(WIDTH*THICKNESS)} for i in range(g0,g1+1) if abs(i-K)>1]
 result={'same_material_gauge_arc_length':gauge,'gauge_length_ratio':gauge/(REST*(g1-g0)/N),'complete_material_sections_excluding_fracture_rings':sections,'minimum_complete_section_ratio':min(q['area_ratio_to_same_initial_section'] for q in sections),'fracture_section_area_available':t<args.event_time_s,'actual_initial_full_fracture_material_fraction_bounds':[(min(p.z for p in pts[4*K:4*K+4])-rings[0].z)/REST,(max(p.z for p in pts[4*K:4*K+4])-rings[0].z)/REST] if frame==1 else None,'material_graph_grip_path_exists':any(0 in gg and 4*N in gg for gg in groups),'evaluated_topology_sha256':hashlib.sha256(str([tuple(pp.vertices) for pp in m.polygons]).encode()).hexdigest(),'frame':frame,'time_s':t,'measured_components':len(groups),'actual_volume':volume,
  'same_material_path_length':sum(segments),'lower_half_material_path_length':sum(segments[:K]),'upper_half_material_path_length':sum(segments[K:]),
  'central_section_area':areas[K],'min_section_area':min(areas),'max_section_area':max(areas),
  'component_bounds':component_bounds,'minimum_axial_component_gap':cut_gap,'grip_checks':grip_checks,
  'projected_specimen_jaw_cap_bounds':framebounds,'all_specimen_and_grips_inside_frame':all(0<=x<=1 for x in framebounds),
  'evaluated_specimen_coordinate_sha256':h.hexdigest(),'vertices':[tuple(p) for p in pts],
  'actual_jaw_cap_rod_positions':[tuple(o.location) for o in [o for o,ee in jaws]+list(caps.values())+list(rods.values())]}
 e.to_mesh_clear();return result
frames=list(range(1,601))
checks=[measure(frame) for frame in frames]; initial=checks[0]['actual_volume']
initial_sections={q['material_ring']:q['area'] for q in checks[0]['complete_material_sections_excluding_fracture_rings']}
initial_gauge_length=checks[0]['same_material_gauge_arc_length']
for check in checks:
 check['actual_volume_ratio_to_initial']=check['actual_volume']/initial
 check['gauge_length_ratio']=check['same_material_gauge_arc_length']/initial_gauge_length
 for q in check['complete_material_sections_excluding_fracture_rings']:q['area_ratio_to_same_initial_section']=q['area']/initial_sections[q['material_ring']]
 check['minimum_complete_section_ratio']=min(q['area_ratio_to_same_initial_section'] for q in check['complete_material_sections_excluding_fracture_rings'])
post=[r for r in checks if r['frame']>=EVENT]
post_motion=max((Vector(a)-Vector(b)).length for r,q in zip(post,post[1:]) for a,b in zip(r['vertices'],q['vertices']))
post_machine=max((Vector(a)-Vector(b)).length for r,q in zip(post,post[1:]) for a,b in zip(r['actual_jaw_cap_rod_positions'],q['actual_jaw_cap_rod_positions']))
before=next(r for r in checks if r['frame']==EVENT-1)['vertices']; after=next(r for r in checks if r['frame']==EVENT)['vertices']
lower_release=[after[i][2]-before[i][2] for i in range(4*(K+1))]
upper_release=[after[4*(N+1)+j][2]-before[4*K+j][2] for j in range(4)]+[after[i][2]-before[i][2] for i in range(4*(K+1),4*(N+1))]
summary={'frames_measured':len(checks),'component_transition_frame':next(r['frame'] for r in checks if r['measured_components']==2),
 'all_grip_material_endpoints_inside_actual_jaws':all(g['actual_endpoint_inside_jaw_z_interval'] for r in checks for g in r['grip_checks']),
 'max_actual_jaw_contact_gap':max(g['actual_contact_face_gap'] for r in checks for g in r['grip_checks']),
 'max_actual_machine_joint_gap':max(abs(g[k]) for r in checks for g in r['grip_checks'] for k in ['jaw_to_cap_surface_gap','cap_to_rod_surface_gap']),
 'min_actual_cap_to_material_clearance':min(g['cap_to_material_end_clearance'] for r in checks for g in r['grip_checks']),
 'all_specimen_jaws_caps_inside_frame':all(r['all_specimen_and_grips_inside_frame'] for r in checks),
 'actual_volume_ratio_range':[min(r['actual_volume_ratio_to_initial'] for r in checks),max(r['actual_volume_ratio_to_initial'] for r in checks)],
 'minimum_actual_component_gap_after_rupture':min(r['minimum_axial_component_gap'] for r in post),
 'max_actual_vertex_step_after_rupture':post_motion,'max_actual_machine_position_step_after_rupture':post_machine,
 'all_actual_post_event_mesh_coordinate_hashes_identical':len({r['evaluated_specimen_coordinate_sha256'] for r in post})==1,
 'actual_event_material_point_axial_displacement_ranges':{'lower_half':[min(lower_release),max(lower_release)],'upper_half':[min(upper_release),max(upper_release)],
 'interpretation':'nonconstant axial displacement within each half independently measured; endpoints constrained, not uniform rigid translation'},
 'no_material_removed':'same160 axial material intervals on both sides of shared fracture slice; only slice vertex connectivity is split',
 'event_release_scope':'nonzero displacement gradient along material path and fixed anchors; not rigid-piece translation'}
for check in checks:del check['vertices']
summary['first_crack_pre_measurement']=next(r for r in checks if r['frame']==EVENT-1)
summary['final_connected_pre_measurement']=next(r for r in checks if r['frame']==EVENT-1)
(out/'mesh_checks.json').write_text(json.dumps({'configuration':CONFIG,'summary':summary,'actual_evaluated_frames':checks},indent=2))
(out/'configuration.json').write_text(json.dumps(CONFIG,indent=2))
for frame in ([] if args.checks_only else sorted(set([1,301,EVENT-4,EVENT-2,EVENT-1,EVENT,EVENT+1,600]))):
 scene.frame_set(frame);update(frame);scene.render.filepath=str(out/f'key_{frame:04d}.png');bpy.ops.render.render(write_still=True)
update(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/'polymer_brittle_initial_scene.blend'))
if not args.keys_only and not args.checks_only:
 directory=out/'frames';directory.mkdir(exist_ok=True)
 for frame in range(1,601):scene.frame_set(frame);update(frame);scene.render.filepath=str(directory/f'{frame:06d}.png');bpy.ops.render.render(write_still=True)
print('BRITTLE_DONE',IMPLEMENTATION,str(out),flush=True)
