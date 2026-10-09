"""New qualitative metal candidates; no dependency on any earlier generator.
Blender --background --python generator/metal_initial.py -- --style ductile \
    --neck-local-stretch-amplitude 4.0 --out PATH
Saved scenes use baked absolute shape keys and ordinary jaw keyframes.
The neck parameter changes material-coordinate stretch and its coupled section,
length and loading-jaw displacement. Input bounds are implementation guards,
not an accepted physical or visual parameter range.
"""
import argparse, bpy, json, math, os, sys
from pathlib import Path
from mathutils import Vector
import numpy as np

VERSION='metal-initial-v1.3.0'
FRACTURE_TIME_CHOICES=(12,14,15,16,17)
NECK_DEFAULT=4.0
NECK_ENGINEERING_MAX=4.0
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser(); p.add_argument('--style',choices=['ductile','brittle'],required=True); p.add_argument('--out',required=True); p.add_argument('--render',action='store_true')
def neck_amplitude(value):
 try: result=float(value)
 except ValueError: raise argparse.ArgumentTypeError('neck amplitude must be a finite number')
 if not math.isfinite(result) or not 0 < result <= NECK_ENGINEERING_MAX:
  raise argparse.ArgumentTypeError('neck amplitude must be finite and 0 < value <= 4.0; this engineering guard preserves the current fixed-camera envelope and is not an accepted physical range')
 return result
p.add_argument('--neck-local-stretch-amplitude',type=neck_amplitude,default=None,
 help='ductile only: dimensionless peak additional local axial stretch; default 4.0. Finite 0 < value <= 4.0 is an engineering input guard, not a validated physical/visual range')
def finite_value(value):
 try: result=float(value)
 except ValueError: raise argparse.ArgumentTypeError('must be a finite number')
 if not math.isfinite(result): raise argparse.ArgumentTypeError('must be finite')
 return result
p.add_argument('--neck-material-sigma',type=finite_value,default=None,help='ductile only: Gaussian width in initial material units; default .215, engineering guard [.15,.30]')
p.add_argument('--fracture-material-center',type=finite_value,default=0.0,help='initial axial material coordinate; also moves ductile neck center; full affected zone must remain in authored gauge')
p.add_argument('--fracture-complete-time-s',type=int,choices=FRACTURE_TIME_CHOICES,default=None,help='first frame without end-to-end material path; omitted retains style baseline; discrete candidate times require checks; all preceding loading stages retimed')
p.add_argument('--skip-key-previews',action='store_true',help='save and check scene without rendering key previews')
A=p.parse_args(args)
if A.style=='brittle' and (A.neck_local_stretch_amplitude is not None or A.neck_material_sigma is not None):
 p.error('neck amplitude and sigma apply only to --style ductile; omit them for brittle')
NECK_AMPLITUDE=(NECK_DEFAULT if A.neck_local_stretch_amplitude is None else A.neck_local_stretch_amplitude) if A.style=='ductile' else 0.0
NECK_SIGMA=.215 if A.neck_material_sigma is None else A.neck_material_sigma
CENTER=A.fracture_material_center
if A.style=='ductile' and not .15 <= NECK_SIGMA <= .30:
 p.error('neck sigma engineering guard requires .15 <= value <= .30; no continuous range is accepted')
AFFECTED_HALF_WIDTH=max(.6,3*NECK_SIGMA if A.style=='ductile' else .6)
if abs(CENTER)+AFFECTED_HALF_WIDTH > 2.55:
 p.error('full fracture/neck affected zone must remain inside authored gauge [-2.55,2.55]')
OUT=Path(A.out).resolve(); OUT.mkdir(parents=True,exist_ok=True)
STYLE=A.style; DUCT=STYLE=='ductile'; FPS=30; END=600
EVENT=(552 if DUCT else 517) if A.fracture_complete_time_s is None else A.fracture_complete_time_s*FPS+1
CRACK_START=EVENT-8 if DUCT else EVENT-2
HALF=3.25; R=.28; NR=48; NZ=90
GAP=.250 if DUCT else .030
NAME=f'metal_round_{STYLE}_baseline_v1'
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.frame_start=1; sc.frame_end=END; sc.render.fps=FPS
sc.render.engine='BLENDER_WORKBENCH'; sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'; sc.render.film_transparent=False
sh=sc.display.shading; sh.light='STUDIO'; sh.studiolight_rotate_z=.3
sh.studio_light='paint.sl'; sh.color_type='MATERIAL'; sh.show_shadows=False; sh.show_cavity=True; sh.cavity_type='WORLD'; sh.curvature_ridge_factor=1.2; sh.curvature_valley_factor=.8
sh.show_specular_highlight=True; sh.background_type='WORLD'; sc.world=bpy.data.worlds.new('uniform background'); sc.world.color=(.36,.39,.42)
sc.display.render_aa='16'; sc.view_settings.view_transform='Standard'
def mat(name,color,metal=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Metallic'].default_value=metal; bs.inputs['Roughness'].default_value=.30
 return m
steel=mat('machined steel',(.48,.51,.54),.9); cutmat=mat('new fracture surface',(.29,.31,.33),.6)
jawmat=mat('blackened grip steel',(.085,.095,.11),.8); framemat=mat('machine housing',(.28,.31,.34),.65)
boltmat=mat('bolt metal',(.60,.63,.66),.9)
def cube(name,loc,scale,material,bevel=.05,parent=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); ob=bpy.context.object; ob.name=name; ob.dimensions=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 ob.data.materials.append(material)
 if bevel:
  mod=ob.modifiers.new('machined edges','BEVEL'); mod.width=bevel; mod.segments=3
  ob.modifiers.new('weighted corner normals','WEIGHTED_NORMAL')
 if parent: ob.parent=parent
 return ob
def cyl(name,loc,radius,depth,material,parent=None,rotation=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=depth,location=loc); o=bpy.context.object; o.name=name; o.data.materials.append(material)
 if rotation: o.rotation_euler=rotation
 for poly in o.data.polygons: poly.use_smooth=True
 if parent: o.parent=parent
 return o

def progress(f):
 u=min(1,max(0,(f-1)/(CRACK_START-1))); n=max(0,(u-.53)/.47)
 # Entire source span is compressed; loading starts immediately, no filler loop.
 return u,n*n*(3-2*n),min(1,max(0,(f-CRACK_START)/(EVENT-CRACK_START)))
S=np.linspace(-HALF,HALF,NZ*2+1) if CENTER==0 else np.concatenate((np.linspace(-HALF,CENTER,NZ+1),np.linspace(CENTER,HALF,NZ+1)[1:]))
def axial(f):
 u,n,q=progress(f); taper=np.clip((2.75-np.abs(S))/.35,0,1)
 lam=1+(.052*u if DUCT else .012*u)*taper
 if DUCT: lam+=NECK_AMPLITUDE*n*np.exp(-((S-CENTER)/NECK_SIGMA)**2)*taper
 Z=np.zeros(len(S)); Z[0]=-HALF
 Z[1:]=-HALF+np.cumsum((lam[:-1]+lam[1:])*.5*np.diff(S))
 # Shoulder and embedded end retain their thickness.
 base=R+(.43-R)*np.clip((np.abs(S)-2.55)/.45,0,1)**2
 rad=base/np.sqrt(lam)
 return Z,rad,q

def crack_height(x,y,r):
 if DUCT: return .055*(1-(x*x+y*y)/(r*r))+.035*x/r+.007*math.sin(5*math.atan2(y,x))*(math.hypot(x,y)/r)
 return .008*x/r+.003*math.sin(3*math.atan2(y,x))*(math.hypot(x,y)/r)

def coords(f,side):
 Z,rad,q=axial(f); ids=range(0,NZ+1) if side<0 else range(NZ,NZ*2+1)
 verts=[]
 for j in ids:
  s=float(S[j]); rr=float(rad[j])
  for a in range(NR):
   theta=2*math.pi*a/NR; x=rr*math.cos(theta); y=rr*math.sin(theta)
   h=crack_height(x,y,float(rad[NZ]))*math.exp(-((s-CENTER)/.18)**2) if abs(s-CENTER)<.6 else 0
   z=float(Z[j])+h
   if side>0:
    threshold=.92*(y/rr+1)/2
    opened=max(0,(q-threshold)/(1-threshold))
    fade=math.exp(-((s-CENTER)/.22)**2)
    z+=GAP*((1-fade)*q+fade*opened)
   verts.append((x,y,z))
 # Cap: several radial rings provide non-flat complementary fracture faces.
 # Matched cap vertices remain coincident over the unbroken ligament.
 for b in (.66,.33):
  rr=float(rad[NZ])*b
  for a in range(NR):
   theta=2*math.pi*a/NR; x=rr*math.cos(theta); y=rr*math.sin(theta)
   z=float(Z[NZ])+crack_height(x,y,float(rad[NZ]))
   if side>0:
    threshold=.92*(y/float(rad[NZ])+1)/2
    z+=GAP*max(0,(q-threshold)/(1-threshold))
   verts.append((x,y,z))
 z=float(Z[NZ])+crack_height(0,0,float(rad[NZ]))
 if side>0: z+=GAP*max(0,(q-.46)/.54)
 verts.append((0,0,z))
 return verts

def specimen(side):
 verts=coords(1,side); faces=[]; capfaces=[]
 for j in range(NZ):
  for a in range(NR):
   k=j*NR+a; kn=j*NR+(a+1)%NR; faces.append((k,kn,kn+NR,k+NR))
 # Both strips built in increasing z, normals wind outward.
 seam=NZ*NR if side<0 else 0
 caps=[seam,(NZ+1)*NR,(NZ+2)*NR]
 for old,new in zip(caps[:-1],caps[1:]):
  for a in range(NR):
   f=(old+a,old+(a+1)%NR,new+(a+1)%NR,new+a)
   faces.append(f if side<0 else f[::-1]); capfaces.append(len(faces)-1)
 center=len(verts)-1
 for a in range(NR):
  f=(caps[-1]+a,caps[-1]+(a+1)%NR,center)
  faces.append(f if side<0 else f[::-1]); capfaces.append(len(faces)-1)
 end=0 if side<0 else NZ*NR
 faces.append(tuple(end+a for a in (range(NR-1,-1,-1) if side<0 else range(NR))))
 me=bpy.data.meshes.new('material-coordinate round specimen'); me.from_pydata(verts,[],faces); me.update()
 ob=bpy.data.objects.new('specimen_lower' if side<0 else 'specimen_upper',me); sc.collection.objects.link(ob); me.materials.append(steel); me.materials.append(cutmat)
 for poly in me.polygons: poly.use_smooth=poly.index<NZ*NR; poly.material_index=1 if poly.index in capfaces else 0
 # Baked keys work in saved .blend with no external Python or auto-run code.
 ob.shape_key_add(name='Basis'); ob.data.shape_keys.use_relative=False
 frames=sorted(set([1,END,CRACK_START,EVENT]+list(range(21,CRACK_START,20))+list(range(CRACK_START,EVENT+1))))
 for frame in frames:
  key=ob.shape_key_add(name=f'pose_{frame:04d}'); key.interpolation='KEY_LINEAR'
  for v,co in zip(key.data,coords(frame,side)): v.co=co
 # Absolute key time is assigned by Blender in ten-unit increments.
 sk=ob.data.shape_keys
 for frame,key in zip(frames,list(sk.key_blocks)[1:]):
  sk.eval_time=key.frame; sk.keyframe_insert(data_path='eval_time',frame=frame)
 ob['material_region']='original round specimen, lower half' if side<0 else 'original round specimen, upper half'
 return ob
lower=specimen(-1); upper=specimen(1)

grips=[]
for sign,label in [(-1,'fixed_lower'),(1,'loading_upper')]:
 root=bpy.data.objects.new(label,None); sc.collection.objects.link(root); grips.append(root)
 # Bilateral real V faces meet the embedded shaft at x=+-0.43.
 z=sign*3.37
 cube(label+'_left_jaw',(-.85,0,z),(.84,1.30,1.10),jawmat,parent=root)
 cube(label+'_right_jaw',(.85,0,z),(.84,1.30,1.10),jawmat,parent=root)
 cube(label+'_crosshead',(0,.32,z+sign*.62),(3.35,1.35,.42),framemat,parent=root)
 # Front bolts emphasize physical clamping without covering exposed gauge.
 for x in (-1.06,1.06):
  cyl(label+'_bolt',(x,-.72,z),.14,.10,boltmat,parent=root,rotation=(math.pi/2,0,0))
 # Rear backing touches back side of cylindrical embedded segment.
 cube(label+'_back_contact',(0,.60,z),(.90,.35,.95),jawmat,.02,parent=root)
for frame in sorted(set([1,END,CRACK_START,EVENT]+list(range(21,CRACK_START,20))+list(range(CRACK_START,EVENT+1)))):
 Z,rr,q=axial(frame); grips[1].location.z=float(Z[-1]-HALF)+GAP*q; grips[1].keyframe_insert(data_path='location',frame=frame)

bpy.ops.object.camera_add(location=(5.0,-25,3.8 if DUCT else .15)); cam=bpy.context.object; cam.name='fixed_camera'; target=Vector((0,0,1.0 if DUCT else .15)); cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=20.2 if DUCT else 18.5; sc.camera=cam
def curves(action):
 if hasattr(action,'fcurves'): return list(action.fcurves)
 return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
for o in bpy.data.objects:
 if o.animation_data and o.animation_data.action:
  action=o.animation_data.action
  try:
   for fc in curves(action):
    for key in fc.keyframe_points: key.interpolation='LINEAR'
  except AttributeError: pass
for ob in [lower,upper]:
 try:
  for fc in curves(ob.data.shape_keys.animation_data.action):
   for key in fc.keyframe_points: key.interpolation='LINEAR'
 except AttributeError: pass
sc['implementation_version']=VERSION; sc['neck_local_stretch_amplitude']=NECK_AMPLITUDE; sc['fracture_complete_frame']=EVENT; sc['unit_note']='dimensionless authored units; no claimed mm or constitutive calibration'; sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(NAME+'.blend')))

def evaluated(ob):
 eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=eo.to_mesh(); verts=[eo.matrix_world@v.co for v in me.vertices]; tris=[]
 me.calc_loop_triangles()
 for tri in me.loop_triangles: tris.append(tuple(tri.vertices))
 edges=[tuple(e.vertices) for e in me.edges]; eo.to_mesh_clear(); return verts,tris,edges
def volume(v,tri):
 a=np.asarray(v,dtype=float); t=np.asarray(tri,dtype=int)
 return float(abs(np.einsum('ij,ij->i',a[t[:,0]],np.cross(a[t[:,1]],a[t[:,2]])).sum()/6))
def components(parts):
 # Measure actual evaluated edge connectivity, joining coincident interface points.
 # The two authored mesh containers are not counted as fracture components.
 parent=[]; vertexkeys={}; adj=[]
 def find(x):
  while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
  return x
 def union(a,b):
  aa,bb=find(a),find(b)
  if aa!=bb: parent[bb]=aa
 offset=0
 for v,tr,e in parts:
  for co in v:
   idx=len(parent); parent.append(idx); key=tuple(round(float(c),5) for c in co)
   if key in vertexkeys: union(idx,vertexkeys[key])
   else: vertexkeys[key]=idx
  for a,b in e: union(offset+a,offset+b)
  offset+=len(v)
 return len({find(i) for i in range(len(parent))})
records=[]; allcoords=[]; baseline=None
section_baseline=None; gauge_baseline=None
def material_measurement(parts,frame):
 global section_baseline,gauge_baseline
 # Actual evaluated circumferential rings, tracked by their initial material station.
 rings=list(np.asarray(parts[0][0][: (NZ+1)*NR],dtype=float).reshape(NZ+1,NR,3))+list(np.asarray(parts[1][0][NR:(NZ+1)*NR],dtype=float).reshape(NZ,NR,3))
 centers=np.asarray([r.mean(axis=0) for r in rings])
 areas=np.asarray([abs(np.sum(r[:,0]*np.roll(r[:,1],-1)-np.roll(r[:,0],-1)*r[:,1]))*.5 for r in rings])
 raw_span=float(np.interp(2.55,S,centers[:,2])-np.interp(-2.55,S,centers[:,2]))
 seam_gap=float(np.mean([b.z-a.z for a,b in zip(parts[0][0][NZ*NR:(NZ+1)*NR],parts[1][0][:NR])]))
 span=raw_span-seam_gap
 local_lengths=[float(centers[70,2]-centers[19,2]),float(centers[NZ+71,2]-centers[NZ+20,2])]
 local_initial=[float(S[70]-S[19]),float(S[NZ+71]-S[NZ+20])]
 if section_baseline is None: section_baseline=areas.copy(); gauge_baseline=span
 intact=[i for i,s in enumerate(S) if -2.55<=s<=2.55 and (frame<=CRACK_START or abs(s-CENTER)>=.6)]
 minimum=min(intact,key=lambda i:areas[i]/section_baseline[i])
 return {'gauge_markers_initial_material_s':[-2.55,2.55],'gauge_axial_projection_length_excluding_open_gap':span,'gauge_axial_projection_length_including_gap':raw_span,'mean_fracture_seam_gap_subtracted':seam_gap,'same_material_local_segment_lambda_axial_projection':[a/b for a,b in zip(local_lengths,local_initial)],'lambda_g_axial_projection':span/gauge_baseline,'minimum_intact_section_area_ratio':float(areas[minimum]/section_baseline[minimum]),'minimum_intact_section_material_s':float(S[minimum]),'neck_center_complete_section_area_ratio':float(areas[NZ]/section_baseline[NZ]) if frame<=CRACK_START else None,'crack_zone_excluded_from_area_measurement':frame>CRACK_START,'excluded_material_zone':[CENTER-.6,CENTER+.6] if frame>CRACK_START else None}

for frame in range(1,END+1):
 sc.frame_set(frame); parts=[evaluated(lower),evaluated(upper)]; vtot=sum(volume(v,t) for v,t,e in parts)
 if baseline is None: baseline=vtot
 # Real jaws' evaluated surfaces bound the actual embedded shaft at x +/- .43.
 grips_measured=[]
 for sign,root,part in [(-1,grips[0],parts[0]),(1,grips[1],parts[1])]:
  v=part[0]; ring=v[:NR] if sign<0 else v[NZ*NR:(NZ+1)*NR]
  left=evaluated(bpy.data.objects[root.name+'_left_jaw'])[0]; right=evaluated(bpy.data.objects[root.name+'_right_jaw'])[0]
  lx=max(c.x for c in left); rx=min(c.x for c in right)
  shaft_end=sum(c.z for c in ring)/len(ring)
  axial_overlap=(max(c.z for c in left)-shaft_end) if sign<0 else (shaft_end-min(c.z for c in left))
  grips_measured.append({'shaft_contact_x_error':max(abs(min(c.x for c in ring)-lx),abs(max(c.x for c in ring)-rx)), 'embedded_axial_overlap':axial_overlap,'method':'evaluated jaw inner-face x and exposed-edge z versus evaluated shaft ring extrema and end z; intended specimen/jaw clamping contact'})
 centerlo=parts[0][0][NZ*NR:(NZ+1)*NR]; centerhi=parts[1][0][:NR]
 gapvalues=[b.z-a.z for a,b in zip(centerlo,centerhi)]
 zlo=sum(c.z for c in parts[0][0][19*NR:20*NR])/NR
 zhi=sum(c.z for c in parts[1][0][71*NR:72*NR])/NR
 mean_gap=sum(gapvalues)/len(gapvalues)
 section_area=abs(sum(a.x*b.y-b.x*a.y for a,b in zip(centerlo,centerlo[1:]+centerlo[:1])))/2
 records.append({'material_measurement':material_measurement(parts,frame),'frame':frame,'time_s':(frame-1)/FPS,'measured_geometric_components':components(parts),'evaluated_closed_mesh_volume':vtot,'volume_relative_change':vtot/baseline-1,'minimum_corresponding_fracture_gap':min(gapvalues),'maximum_corresponding_fracture_gap':max(gapvalues),'jaw_contacts':grips_measured,'top_jaw_z':float(grips[1].location.z),'minimum_radius':min(math.hypot(c.x,c.y) for c in centerlo),'same_material_station_s':[float(S[19]),float(S[NZ+71])],'same_material_station_axial_span':zhi-zlo,'axial_material_length_projection_excluding_open_gap':zhi-zlo-mean_gap,'minimum_section_polygon_area':section_area})
 if frame>=EVENT: allcoords.append((frame,[tuple(float(x) for x in v) for part in parts for v in part[0]],tuple(grips[1].location)))
post_motion=max((max(abs(x-y) for a,b in zip(allcoords[0][1],entry[1]) for x,y in zip(a,b)) for entry in allcoords),default=0)
post_jaw=max((max(abs(a-b) for a,b in zip(allcoords[0][2],entry[2])) for entry in allcoords),default=0)
(OUT/'mesh_checks.json').write_text(json.dumps({'implementation_version':VERSION,'measurement_note':'Evaluated mesh positions and actual edge graph with coincident interface vertex welding at 1e-5 units; two containers do not predetermine component count. Interior paired fracture caps are hidden while interface is unbroken. Not an FEM model.','samples':records,'postfracture_max_vertex_displacement':post_motion,'postfracture_max_loading_jaw_displacement':post_jaw,'max_volume_relative_change':max(abs(r['volume_relative_change']) for r in records)},indent=2))
config={'implementation_version':VERSION,'style':STYLE,'render':{'engine':'BLENDER_WORKBENCH','resolution':[1280,720],'fps':FPS,'frames':END,'duration_s':20,'aa_samples':16,'fixed_camera':list(cam.location),'orthographic_scale':cam.data.ortho_scale,'shadow_enabled':False,'studio_light':sh.studio_light},'geometry':{'units':'dimensionless','original_half_length':HALF,'original_gauge_radius':R,'embedded_end_radius':.43,'authored_gauge_region':[-2.55,2.55],'formal_source_gauge':'unknown','rings_per_half':NZ+1,'angular_segments':NR,'fracture_surface': 'complementary shallow cup-cone and inclined lip' if DUCT else 'complementary near-planar transverse rough surface','surface_detail_mechanism':'authored qualitative shape, not a proven fracture mechanism'},'motion':{'lower_jaw':'fixed','upper_jaw':'source-informed loading displacement, freezes at completed rupture','uniform_stretch_at_rupture':.052 if DUCT else .012,'ductile_neck_local_stretch_amplitude':NECK_AMPLITUDE,'neck_material_sigma':NECK_SIGMA if DUCT else None,'crack_opening_units':GAP,'crack_start_frame':CRACK_START,'fracture_complete_frame':EVENT,'fracture_complete_time_s':(EVENT-1)/FPS,'postfracture_displacement':0,'opening_note':'Complementary surfaces open progressively from front to rear under last loading displacement; no region is removed and no rigid fragment recoil is added. Gap is authored qualitative finite opening, not measured source displacement. Ductile gap/original diameter=0.446 and gap/terminal neck diameter~1.0 versus visible source postrupture ratios~0.65 and~1.3. Source ratios include source postrupture motion; here finite opening is authored during final loading to make fracture visible before selected load stop.'},'materials':[{'name':m.name,'rgba':list(m.diffuse_color),'metallic':m.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value,'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value} for m in [steel,cutmat,jawmat,framemat,boltmat]],'saved_scene_animation':'baked absolute shape keys and ordinary jaw keys; no external script required'}
config['neck_parameter']={'cli_option':'--neck-local-stretch-amplitude','applicable_style':'ductile','selected_value':NECK_AMPLITUDE if DUCT else None,'default_value':NECK_DEFAULT,'units':'dimensionless additional local axial stretch','formula':'lambda(s,t)=1+0.052*u*taper(s)+amplitude*n*exp(-((s-center)/sigma)^2)*taper(s); n=v^2*(3-2v), v=max(0,(u-0.53)/0.47), u=min(1,(frame-1)/(crack_start_frame-1))','taper_definition':'clamp((2.75-abs(s))/0.35,0,1)','coupling':'Axial positions integrate lambda over original material coordinates; radius=original radius/sqrt(lambda); loading jaw follows integrated end position. Paired fracture surfaces use the resulting same seam radius and match before crack opening.','engineering_input_guard':{'minimum_exclusive':0.0,'maximum_inclusive':NECK_ENGINEERING_MAX,'finite_required':True,'reason':'Larger amplitudes increase specimen and crosshead excursion beyond the baseline; the conservative input upper bound preserves current fixed-camera framing. Larger-value framing has not been verified.'},'accepted_continuous_parameter_range':None,'parameter_range_accepted':False,'scope_note':'Guarded inputs do not establish physical plausibility, label validity, or user acceptance of a new video; each changed value requires its own applicable checks and review.'}
if DUCT:
 final_radius=R/math.sqrt(1.052+NECK_AMPLITUDE)
 config['motion']['terminal_neck_radius_from_material_mapping']=final_radius
 config['motion']['opening_note']=f'Complementary surfaces open progressively from front to rear under last loading displacement; no region is removed and no rigid fragment recoil is added. Gap is authored qualitative finite opening, not measured source displacement. Gap/original diameter={GAP/(2*R):.6f}; gap/terminal neck diameter={GAP/(2*final_radius):.6f} for selected neck amplitude {NECK_AMPLITUDE}. Source postrupture ratios include actual source motion and are not a calibration of this varied geometry.'
config['stage1_parameters']={'fracture_material_center':CENTER,'neck_material_center':CENTER if DUCT else None,'neck_material_sigma':NECK_SIGMA if DUCT else None,'initial_material_coordinate_grid':S.tolist(),'fracture_affected_zone':[CENTER-.6,CENTER+.6],'neck_3sigma_zone':[CENTER-3*NECK_SIGMA,CENTER+3*NECK_SIGMA] if DUCT else None,'engineering_guards':{'sigma_ductile':[.15,.30],'full_affected_zone_inside_gauge':[-2.55,2.55],'timing_discrete_s':list(FRACTURE_TIME_CHOICES)},'timing_default_frame':552 if DUCT else 517,'timing_selected_override_s':A.fracture_complete_time_s,'coupling':'Moved seam is included exactly in initial material grid. Ductile stretch, radial contraction, fracture geometry, opening fade and jaw endpoint all use same material center; no postbreak translation is introduced. Gaussian has infinite tails; 3sigma bounds are a field envelope, not hard support.','scope':'Stage1 and training-batch1 discrete candidate inputs and engineering guards; new values and combinations require applicable mesh, visibility and material/label checks and user acceptance. No physical calibration or continuous range acceptance.'}
first_open=next((r['frame'] for r in records if r['maximum_corresponding_fracture_gap']>1e-5),None)
first_disconnected=next((r['frame'] for r in records if r['measured_geometric_components']>1),None)
config['measured_events']={'first_open_gap_frame':first_open,'first_loss_of_geometric_path_frame':first_disconnected,'loading_begin_frame':1,'postbreak_stopped_frame':EVENT,'method':'All 600 actual evaluated edge graphs with coincident vertex welding at 1e-5 units; this is geometric contact connectivity, not bonded FEM topology. First opening uses measured paired fracture-ring gap >1e-5.'}
config['prefracture_measurements']={'before_first_opening':records[first_open-2]['material_measurement'] if first_open and first_open>1 else None,'before_final_loss_of_connection':records[first_disconnected-2]['material_measurement'] if first_disconnected and first_disconnected>1 else None,'area_definition':'Transverse xy projected polygon area of same evaluated material ring relative to frame1; exclude entire +/-0.6 material crack-affected zone once first opening occurs. Neck-center area at final connected state is unavailable in progressive crack zone; intact area minimum is reported separately. Axial material-marker projection subtracts mean paired fracture-seam gap to exclude crack opening; also report raw span, subtracted gap and two same-material local segments.','local_material_segments':{'lower_track_initial_s':[float(S[19]),float(S[70])],'upper_track_initial_s':[float(S[NZ+20]),float(S[NZ+71])]},'material_origin':'initial undeformed axial coordinates; authored gauge differs from unknown formal source gauge'}
sc['stage1_configuration_json']=json.dumps(config)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(NAME+'.blend')))
(OUT/'config.json').write_text(json.dumps(config,indent=2))
for frame in ([] if A.skip_key_previews else sorted(set([1,270,CRACK_START,CRACK_START+1,EVENT-1,EVENT,600]))):
 sc.frame_set(frame); sc.render.filepath=str(OUT/f'key_{frame:04d}.png'); bpy.ops.render.render(write_still=True)
if A.render:
 (OUT/'frames').mkdir(exist_ok=True)
 for frame in range(1,END+1):
  sc.frame_set(frame); sc.render.filepath=str(OUT/'frames'/f'{frame:04d}.png'); bpy.ops.render.render(write_still=True)
print('METAL_BUILD_COMPLETE',str(OUT))
