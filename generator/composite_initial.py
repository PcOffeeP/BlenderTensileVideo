import bpy, math, json, sys, os, argparse
import hashlib
from pathlib import Path
from mathutils import Vector
V='composite-initial/0.5.0'
p=argparse.ArgumentParser()
p.add_argument('--kind',choices=['debond','brittle'],required=True)
p.add_argument('--out',required=True)
p.add_argument('--render',action='store_true')
p.add_argument('--resume',action='store_true')
p.add_argument('--skip-previews',action='store_true',help='checks and scene only')
p.add_argument('--fracture-center',type=float,default=None,help='initial material z; entire damage field follows')
p.add_argument('--event-time-s',type=float,choices=[12.,15.,17.],default=17.)
p.add_argument('--debond-length-factor',type=float,choices=[.8,1.,1.2],default=1.)
p.add_argument('--debond-opening-factor',type=float,choices=[.8,1.,1.2],default=1.)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
center=(-1.83 if a.kind=='brittle' else 0.) if a.fracture_center is None else a.fracture_center
if not math.isfinite(center):p.error('fracture center must be finite')
if a.kind=='brittle' and (a.debond_length_factor!=1 or a.debond_opening_factor!=1):p.error('debond controls apply only to debond')
# Bound the whole slanted fracture and support of the opening field, not just its centre.
seam_bounds=[center-.11,center+.11]
damage_bounds=[center-.8*a.debond_length_factor,center+.8*a.debond_length_factor] if a.kind=='debond' else seam_bounds
if a.kind=='debond':
 if not(-1.5<min(damage_bounds+seam_bounds) and max(damage_bounds+seam_bounds)<1.5):p.error('complete debond/fracture region must remain strictly within authored gauge [-1.5,1.5]')
 if not(center-.2*a.debond_length_factor<seam_bounds[0] and seam_bounds[1]<center+.2*a.debond_length_factor):p.error('grid must surround slanted seam')
 if center+1.2>=2.5:p.error('shear support must end below upper jaw')
else:
 if not(-2.5<seam_bounds[0] and seam_bounds[1]<-1.5):p.error('entire brittle seam must stay below gauge and above lower clamp root')
 if center+1.2>=2.5:p.error('shear support must end below upper jaw')
out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
C={'version':V,'baseline_implementation_version':'composite-initial/0.4.0' if a.kind=='debond' else 'composite-initial/0.3.1','kind':a.kind,'fps':30,'frames':600,'resolution':[960,540],'loading_axis':'z','fixed_end':'lower','moving_end':'upper','free_span':5.0,'width':1.0,'thickness':0.18,'grip_overlap':0.48,'gauge_authored':[-1.5,1.5],'units':'dimensionless relative coordinates','event_frame':1+round(a.event_time_s*30),'event_time_s':a.event_time_s,'maximum_grip_displacement':0.14 if a.kind=='debond' else 0.10,'fracture_z':center,'rear_panel':False,'machine_columns':False,'debond_final_result':'complete_rupture_simultaneous_with_interface_opening','debond_fracture_slope':0.22,'debond_local_shear':0.12,'brittle_local_shear':0.12,'brittle_fracture_slope':0.22,'no_constitutive_solver':True,'debond_length_factor':a.debond_length_factor,'debond_opening_factor':a.debond_opening_factor,'debond_length':1.6*a.debond_length_factor,'debond_opening':.10*a.debond_opening_factor,'fracture_material_bounds':seam_bounds,'damage_material_bounds':damage_bounds,'shear_support_material_upper':center+1.2,'parameter_scope':'stage1 discrete candidates; no accepted continuous range','camera':{'location':[14,-9,3.] if a.kind=='debond' else [7.5,-17,3.],'look_at':[0,0,0],'orthographic_scale':16.4,'fixed_all_frames':True},'renderer':'BLENDER_WORKBENCH','render_aa':'8','world_color':[.13,.16,.19],'specimen_color':[.15,.18,.21],'other_assumed_ply_color':[.23,.27,.3],'loading_function':'dmax*smoothstep((frame-1)/(event_frame-1)), held at event','damage_function':'abrupt whole seam lateral shear; simultaneous sinusoidal local interface opening for debond','clamp':{'front_back_y':[-.29,.29],'jaw_size':[1.48,.40,.72],'centre_z':[-2.86,2.86]},'encoding':{'codec':'libx264','crf':16,'preset':'slow','pixel_format':'yuv420p','audio':False}}
if a.kind=='debond':C.update({'debond_damage_onset_frame':C['event_frame'],'debond_damage_full_frame':C['event_frame'],'interface_and_complete_rupture_same_onset':True,'debond_event_timing':'simultaneous abrupt opening and complete rupture'})
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100;s.render.fps=30;s.frame_start=1;s.frame_end=600
s.render.image_settings.file_format='PNG';s.render.film_transparent=False
s.display.shading.light='STUDIO';s.display.shading.studiolight_rotate_z=0.5;s.display.shading.studio_light='paint.sl';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.display.shading.curvature_ridge_factor=1.1;s.display.shading.curvature_valley_factor=1.1;s.display.shading.show_specular_highlight=True;s.display.shading.background_type='WORLD';s.world.color=(0.13,0.16,0.19);s.display.render_aa='8'
s.view_settings.view_transform='Standard'
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
steel=mat('fixture satin steel',(0.44,.49,.53));jawmat=mat('gripping jaw',(.15,.18,.2));specmat=mat('composite neutral surface',(.15,.18,.21));edge=mat('second assumed layer',(.23,.27,.3));dark=mat('fastener',(.08,.10,.12));blue=mat('machine frame',(.27,.35,.43));white=mat('gauge marks',(.83,.85,.83))
def box(n,loc,size,m,bev=.035):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bev:
  q=o.modifiers.new('rounded machined edges','BEVEL');q.width=bev;q.segments=3;o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 return o
# Actual front/back jaw faces contact specimen at y=+/-0.09, clamp overlap 0.48.
fixtures=[]
for sign in [-1,1]:
 root=sign*2.5;cy=sign*2.86
 for y in [-.29,.29]: fixtures.append((box(('lower' if sign<0 else 'upper')+' jaw '+str(y),(0,y,cy),(1.48,.40,.72),jawmat),sign))
 fixtures.append((box('fixture body '+str(sign),(0,.30,sign*3.33),(2.40,1.1,.70),steel),sign))
 fixtures.append((box('loading shaft '+str(sign),(0,.33,sign*3.94),(.75,.80,.57),steel),sign))
 for x in [-.96,.96]: fixtures.append((box('bolt '+str(sign)+str(x),(x,-.32,sign*3.31),(.19,.12,.19),dark,.06),sign))
# Fixture-and-specimen view: no detached frame columns or rear panel.
bpy.ops.object.camera_add(location=((14,-9,3.0) if a.kind=='debond' else (7.5,-17,3.0)));cam=bpy.context.object;cam.name='fixed_camera';cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=16.4;s.camera=cam
# Mesh builder welds coincident material vertices; connectivity is subsequently measured on evaluated mesh.
def smooth(v):v=max(0,min(1,v));return v*v*(3-2*v)
def displacement(f): return C['maximum_grip_displacement']*smooth((f-1)/(C['event_frame']-1))
def build(f):
 d=displacement(min(f,C['event_frame']));verts=[];faces=[];mids=[];cache={};sources=[];source_map={}
 def vid(v):
  k=tuple(round(t,9) for t in v)
  if k not in cache:cache[k]=len(verts);verts.append(v);sources.append(source_map.get(k,(0,0,0,-1,-1)))
  return cache[k]
 def addcell(corners,mi):
  ids=[vid(v) for v in corners]
  for inds in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:faces.append(tuple(ids[i] for i in inds));mids.append(mi)
 if a.kind=='debond':
  xs=[-.5+i/20 for i in range(21)]
  strength=1.0 if f>=C['event_frame'] else 0.0;length=C['debond_length']*strength
  for ply in range(2):
   sg=-1 if ply==0 else 1
   for part in range(2):
    def point(x,y,z):
     z1=z+d*max(0,min(1,(z+2.5)/5))
     env=0 if length==0 or abs(z-center)>=length/2 else math.sin(math.pi*(z-center+length/2)/length)**2
     opening=C['debond_opening']*strength*env
     x1=x
     if part==1 and f>=C['event_frame']:
      cut=center+1.2+d*(center+3.7)/5
      x1-=.12*max(0,(cut-z1)/(cut-(center+d*(center+2.5)/5)))
     result=(x1,y+sg*opening/2,z1)
     source_map[tuple(round(t,9) for t in result)]=(x,y,z,ply,part)
     return result
    for xa,xb in zip(xs,xs[1:]):
     def levels(x):
      br=center+.22*x
      return [-2.98,-2.5]+[center+(-.8+i*.1)*a.debond_length_factor for i in range(7)]+[br] if part==0 else [br]+[center+(.2+i*.1)*a.debond_length_factor for i in range(7)]+[center+1.2,2.5,2.98]
     lz=levels(xa);rz=levels(xb)
     ya,yb=(-.09,0) if ply==0 else (0,.09)
     for j in range(len(lz)-1):
      corners=[point(xa,ya,lz[j]),point(xb,ya,rz[j]),point(xb,yb,rz[j]),point(xa,yb,lz[j]),point(xa,ya,lz[j+1]),point(xb,ya,rz[j+1]),point(xb,yb,rz[j+1]),point(xa,yb,lz[j+1])]
      addcell(corners,ply)
 else:
  xs=[-.5+i/20 for i in range(21)]
  progress=1.0 if f>=C['event_frame'] else 0.0;gap=0.0
  crackfront=-.5+progress
  def seam(x):return center+.22*x
  def point(x,y,t,part):
   sx=x;br=seam(x);fract=progress>0 and x<crackfront+1e-8
   opening=gap if fract else 0
   bz=br+d*(br+2.5)/5
   if part==0:
    zb=-2.98+(br+2.98)*t
    zz=zb+d*max(0,min(1,(zb+2.5)/5))
   else:
    zb=br+(center+1.2-br)*t if t<=1 else (center+1.2+(2.5-center-1.2)*(t-1) if t<=2 else 2.98)
    zz=zb+d*max(0,min(1,(zb+2.5)/5))
    cut=center+1.2+d*(center+3.7)/5
    x-=.12*progress*max(0,(cut-zz)/(cut-center))
   result=(x,y,zz)
   source_map[tuple(round(q,9) for q in result)]=(sx,y,zb,0,part)
   return result
  for part in [0,1]:
   ts=([i/12 for i in range(13)]+[1+i/20 for i in range(1,21)]+[3]) if part==1 else [i/24 for i in range(25)]
   for xa,xb in zip(xs,xs[1:]):
    for ta,tb in zip(ts,ts[1:]):
     addcell([point(x,y,t,part) for t in [ta,tb] for y,x in [(-.09,xa),(-.09,xb),(.09,xb),(.09,xa)]],0)
 mesh=bpy.data.meshes.new('material_mesh');mesh.from_pydata(verts,[],faces);mesh.materials.append(specmat);mesh.materials.append(edge)
 # remove duplicated internal cell faces; keep interface surfaces where opened.
 seen={};discard=set()
 for i,p in enumerate(mesh.polygons):
  k=tuple(sorted(p.vertices))
  if k in seen:discard.add(i);discard.add(seen[k])
  else:seen[k]=i
 ff=[face for i,face in enumerate(faces) if i not in discard];mm=[mi for i,mi in enumerate(mids) if i not in discard]
 # Drop unreferenced construction-grid vertices, not material or boundary faces.
 used=sorted({i for face in ff for i in face});remap={old:new for new,old in enumerate(used)}
 verts=[verts[i] for i in used];sources=[sources[i] for i in used];ff=[tuple(remap[i] for i in face) for face in ff]
 mesh.clear_geometry();mesh.from_pydata(verts,[],ff);mesh.update()
 for p,mi in zip(mesh.polygons,mm):
  p.material_index=mi;p.use_smooth=True
 mesh.set_sharp_from_angle(angle=math.radians(40))
 source_attr=mesh.attributes.new('source_coordinate','FLOAT_VECTOR','POINT')
 part_attr=mesh.attributes.new('source_part','INT','POINT')
 for i,src in enumerate(sources):source_attr.data[i].vector=src[:3];part_attr.data[i].value=src[4]
 return mesh
mesh=build(1);obj=bpy.data.objects.new('specimen_actual_material',mesh);s.collection.objects.link(obj)
base_fixture={o.name:o.location.z for o,sign in fixtures}
def update(f):
 old=obj.data;obj.data=build(f);bpy.data.meshes.remove(old)
 d=displacement(min(f,C['event_frame']))
 for o,sign in fixtures:o.location.z=base_fixture[o.name]+(d if sign>0 else 0)
 s.frame_set(f)
def check(f):
 update(f);dg=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dg);me=ev.to_mesh();v=[obj.matrix_world@x.co for x in me.vertices];adj=[set() for x in v]
 for e in me.edges:u,w=e.vertices;adj[u].add(w);adj[w].add(u)
 seen=set();comps=[];component_ids=[]
 for k in range(len(v)):
  if k in seen:continue
  q=[k];seen.add(k);n=0;ids=[]
  while q:
   u=q.pop();n+=1;ids.append(u)
   for w in adj[u]:
    if w not in seen:seen.add(w);q.append(w)
  comps.append(n);component_ids.append(ids)
 me.calc_loop_triangles();vol=sum(v[t.vertices[0]].dot(v[t.vertices[1]].cross(v[t.vertices[2]]))/6 for t in me.loop_triangles)
 d=displacement(min(f,C['event_frame']));bottom=[vv for vv in v if vv.z< -2.51];top=[vv for vv in v if vv.z>2.51+d]
 contact=lambda vs: min(abs(abs(vv.y)-.09) for vv in vs)
 r={'frame':f,'time_s':(f-1)/30,'components_measured':len(comps),'component_vertices':comps,'vertices':len(v),'faces':len(me.polygons),'signed_volume':vol,'specimen_z_bounds':[min(vv.z for vv in v),max(vv.z for vv in v)],'grip_surface_contact_error':[contact(bottom),contact(top)],'upper_jaw_displacement':d,'coordinates':[[round(t,9) for t in vv] for vv in v]}
 r['component_clamp_connections']=[{'vertex_count':len(ids),'z_bounds':[min(v[i].z for i in ids),max(v[i].z for i in ids)],'touches_lower_material_clamp':any(-2.98001<=v[i].z<=-2.49999 for i in ids),'touches_upper_material_clamp':any(2.49999+d<=v[i].z<=2.98001+d for i in ids)} for ids in component_ids]
 for c,ids in zip(r['component_clamp_connections'],component_ids):
  members=set(ids);cv=sum(v[t.vertices[0]].dot(v[t.vertices[1]].cross(v[t.vertices[2]]))/6 for t in me.loop_triangles if t.vertices[0] in members)
  c['signed_surface_volume']=cv;c['boundary_kind']='internal_cavity_boundary' if cv<0 and not(c['touches_lower_material_clamp'] or c['touches_upper_material_clamp']) else 'material_outer_boundary'
 r['has_material_surface_path_between_clamps']=any(c['touches_lower_material_clamp'] and c['touches_upper_material_clamp'] for c in r['component_clamp_connections'])
 # Track actual same-material left-edge paths and measured section dimensions at key states.
 if a.kind=='debond':
  paths=[[[],[]],[[],[]]]
  for i,vv in enumerate(v):
   src=me.attributes['source_coordinate'].data[i].vector;part=me.attributes['source_part'].data[i].value
   if abs(src.x+.5)<1e-6 and -2.50001<=src.z<=2.50001 and abs(abs(src.y)-.09)<1e-6:
    ply=0 if src.y<0 else 1
    if f<C['event_frame'] and abs(src.z-(center+.22*src.x))<1e-6:
     paths[ply][0].append((src.z,vv));paths[ply][1].append((src.z,vv))
    else:paths[ply][part].append((src.z,vv))
  r['same_material_outer_ply_segment_lengths']=[[sum((bb[1]-aa[1]).length for aa,bb in zip(pp,pp[1:])) for pp in [sorted(path,key=lambda q:q[0]) for path in ply]] for ply in paths]
  r['section_actual_ply_thickness']=None
 else:
  si=set()
  for pp in me.polygons:
   if pp.normal.x<-.9 and abs(pp.normal.y)<.1:si.update(pp.vertices)
  boundary=[v[i] for i in si if abs(v[i].y+.09)<1e-6]
  zcut=center-.11+d*(center+2.39)/5;lower=[];upper=[]
  for vv in boundary:
   if vv.z<zcut-1e-5:lower.append(vv)
   elif vv.z>zcut+1e-5:upper.append(vv)
   elif f<C['event_frame']:lower.append(vv);upper.append(vv)
   elif abs(vv.x+.5)<1e-5:lower.append(vv)
   else:upper.append(vv)
  r['same_material_lower_upper_left_edge_lengths']=[sum((bb-aa).length for aa,bb in zip(pp,pp[1:])) for pp in [sorted(lower,key=lambda vv:vv.z),sorted(upper,key=lambda vv:vv.z)]]
  r['section_actual_thickness']=max(vv.y for vv in v)-min(vv.y for vv in v)
 # Actual interface opening and fracture-face clearance from evaluated vertices and polygon planes.
 if a.kind=='debond':
  owned=[set(),set()]
  for pp in me.polygons:owned[pp.material_index].update(pp.vertices)
  rings={};interface_rings={}
  for ply,ids in enumerate(owned):
   for i in ids:
    src=me.attributes['source_coordinate'].data[i].vector;part=me.attributes['source_part'].data[i].value
    key=(round(src.x,6),round(src.z,6),part if f>=C['event_frame'] else 0)
    rings.setdefault(key,[[],[]])[ply].append((src.y,v[i].y))
    # Only original y=0 material interface vertices can measure an interface gap.
    # A bonded interior interface has no surface vertices, not a gap equal to bulk thickness.
    if abs(src.y)<1e-6:interface_rings.setdefault(key,[[],[]])[ply].append(v[i].y)
  gaps=[min(upper)-max(lower) for lower,upper in interface_rings.values() if lower and upper];th=[]
  for layers in rings.values():
   for ply,vs in enumerate(layers):
    inner=[yy for sy,yy in vs if abs(sy)<1e-6];outer=[yy for sy,yy in vs if abs(sy-(-.09 if ply==0 else .09))<1e-6]
    if inner and outer:th.append(abs(sum(inner)/len(inner)-sum(outer)/len(outer)))
  r['interface_opening_measured']=max(gaps,default=0);r['interface_clearance_measured_min']=min(gaps,default=0);r['ply_thickness_measured_min']=min(th,default=.09);r['inter_ply_penetration']=min(gaps,default=0)<-1e-6;r['section_actual_ply_thickness']=r['ply_thickness_measured_min']
 if f>=C['event_frame'] and len(comps)==2:
  seam=[]
  for pol in me.polygons:
   if abs(pol.normal.z)>.9 and (center+d*(center+2.5)/5-.25<pol.center.z<center+d*(center+2.5)/5+.25):
    vs=[v[i] for i in pol.vertices];n=(vs[1]-vs[0]).cross(vs[2]-vs[0]);cc=n.dot(vs[0]);seam.append((n,cc,vs))
  upp=[pp for pp in seam if pp[0].z<0];low=[pp for pp in seam if pp[0].z>0]
  # Derive actual boundary planes from evaluated mesh triangles, inspect their overlapping width.
  assert upp and low,(f,'missing seam faces')
  un,uc,uv=upp[0];ln,lc,lv=low[0]
  ux=[vv.x for pp in upp for vv in pp[2]];lx=[vv.x for pp in low for vv in pp[2]]
  xlo=max(min(ux),min(lx));xhi=min(max(ux),max(lx));clear=[]
  for x in [xlo+(xhi-xlo)*i/100 for i in range(101)]:
   clear.append((uc-un.x*x)/un.z-(lc-ln.x*x)/ln.z)
  r['seam_clearance_measured_min']=min(clear);r['seam_clearance_measured_max']=max(clear);r['seam_penetration']=min(clear)<-1e-6
 # Material-coordinate paths use evaluated corners on the same exterior material line.
 paths=[[],[]]
 for i,vv in enumerate(v):
  src=me.attributes['source_coordinate'].data[i].vector
  part=me.attributes['source_part'].data[i].value
  if abs(src.x+.5)<1e-6 and abs(src.y+.09)<1e-6:
   br=center-.11
   if f<C['event_frame']:
    if src.z<=br+1e-6:paths[0].append((float(src.z),vv))
    if src.z>=br-1e-6:paths[1].append((float(src.z),vv))
   else:paths[part].append((float(src.z),vv))
 def interpolate(path,z):
  path=sorted(path,key=lambda q:q[0])
  for zz,vv in path:
   if abs(zz-z)<1e-6:return vv
  for (za,va),(zb,vb) in zip(path,path[1:]):
   if za<z<zb:return va+(vb-va)*((z-za)/(zb-za))
  raise AssertionError(('missing tracked material point',z,f))
 segment_lengths=[]
 for part,path in enumerate(paths):
  lo,hi=(-2.5,center-.11) if part==0 else (center-.11,2.5)
  pp=[(lo,interpolate(path,lo))]+[(z,vv) for z,vv in sorted(path,key=lambda q:q[0]) if lo+1e-6<z<hi-1e-6]+[(hi,interpolate(path,hi))]
  segment_lengths.append(sum((vb-va).length for (_,va),(_,vb) in zip(pp,pp[1:])))
 r['tracked_material_segment_path_lengths']=segment_lengths
 r['tracked_material_segment_initial_bounds']=[[-2.5,center-.11],[center-.11,2.5]]
 r['tracked_material_gauge_axial_length']=None
 if f<C['event_frame']:
  combined=paths[0]+paths[1]
  r['tracked_material_gauge_axial_length']=float(interpolate(combined,1.5).z-interpolate(combined,-1.5).z)
  r['tracked_material_gauge_lambda']=r['tracked_material_gauge_axial_length']/3.
 # Undamaged same-material section at authored gauge upper boundary.
 corners=[]
 for sx in [-.5,.5]:
  for sy in [-.09,.09]:
   path=[]
   for i,vv in enumerate(v):
    src=me.attributes['source_coordinate'].data[i].vector
    if abs(src.x-sx)<1e-6 and abs(src.y-sy)<1e-6:path.append((float(src.z),vv))
   corners.append(interpolate(path,1.5))
 r['tracked_intact_section_material_z']=1.5
 r['tracked_intact_section_width']=float((corners[2]-corners[0]).length)
 r['tracked_intact_section_thickness']=float((corners[1]-corners[0]).length)
 r['tracked_intact_section_area']=r['tracked_intact_section_width']*r['tracked_intact_section_thickness']
 # Actual evaluated bevelled jaw contact planes and axial overlap.
 jaw_checks=[]
 for sign in [-1,1]:
  jaw=[o for o,sg in fixtures if sg==sign and ' jaw ' in o.name]
  planes=[];jaw_min=[];jaw_max=[]
  for jo in jaw:
   je=jo.evaluated_get(dg);jm=je.to_mesh();jv=[je.matrix_world@vv.co for vv in jm.vertices]
   planes.append(min(jv,key=lambda vv:abs(vv.y)).y);jaw_min.append(min(vv.z for vv in jv));jaw_max.append(max(vv.z for vv in jv));je.to_mesh_clear()
  matz=[vv.z for vv in v if (vv.z< -2.49999 if sign<0 else vv.z>2.49999+d)]
  exterior=[vv for vv in v if (vv.z< -2.51 if sign<0 else vv.z>2.51+d) and abs(abs(vv.y)-.09)<1e-5]
  jaw_checks.append({'sign':sign,'inner_planes_y':planes,'contact_error_max':max(min(abs(vv.y-y) for y in planes) for vv in exterior),'overlap_z':min(max(matz),min(jaw_max))-max(min(matz),max(jaw_min)),'material_max_abs_x':max(abs(vv.x) for vv in exterior)})
 r['actual_evaluated_jaw_checks']=jaw_checks
 edge_uses={}
 for pol in me.polygons:
  for u,w in pol.edge_keys:edge_uses[(min(u,w),max(u,w))]=edge_uses.get((min(u,w),max(u,w)),0)+1
 r['non_two_face_edges']=sum(n!=2 for n in edge_uses.values())
 r['whole_damage_material_bounds']=C['damage_material_bounds']
 r['fracture_material_bounds_measured']=[min(me.attributes['source_coordinate'].data[i].vector.z for i in range(len(v)) if abs(me.attributes['source_coordinate'].data[i].vector.z-center-.22*me.attributes['source_coordinate'].data[i].vector.x)<1e-6),max(me.attributes['source_coordinate'].data[i].vector.z for i in range(len(v)) if abs(me.attributes['source_coordinate'].data[i].vector.z-center-.22*me.attributes['source_coordinate'].data[i].vector.x)<1e-6)]
 r['fixture_coordinates']={o.name:[float(q) for q in o.location] for o,sign in fixtures}
 ev.to_mesh_clear();return r
event=C['event_frame']
keyframes=sorted(set([1,1+(event-1)//2,event-30]+list(range(event-3,event+3))+[600]))
allchecks=[];reference=None;fixture_reference=None;stop=0.;fixture_stop=0.
for f in range(1,601):
 rr=check(f)
 if f==event:reference=rr['coordinates'];fixture_reference=rr['fixture_coordinates']
 if f>=event:
  stop=max(stop,max(abs(x-y) for x,y in zip(sum(reference,[]),sum(rr['coordinates'],[]))))
  fixture_stop=max(fixture_stop,max(abs(x-y) for name,pos in fixture_reference.items() for x,y in zip(pos,rr['fixture_coordinates'][name])))
 rr.pop('coordinates');rr.pop('fixture_coordinates');allchecks.append(rr)
(out/'all_frame_mesh_checks.json').write_text(json.dumps(allchecks,indent=2))
checks=[allchecks[f-1] for f in keyframes]
summary={'implementation_version':V,'config':C,'samples':checks,'evaluated_frame_count':600,'post_event_max_vertex_displacement':stop,'post_event_max_fixture_displacement':fixture_stop,'scope':'600 evaluated mesh frames: graph paths, closed edges, signed volume, tracked material lengths and intact section, actual bevelled jaws, interface and seam-plane clearance; no full triangle self-intersection or constitutive solver','contact_semantics':'intentional jaw embed0.48; evaluated inner planes and outer material measured','full_triangle_selfintersection_checked':False}

volume0=allchecks[0]['signed_volume']
first_loss=next(q['frame'] for q in allchecks if not q['has_material_surface_path_between_clamps'])
first_open=next((q['frame'] for q in allchecks if q.get('interface_opening_measured',0)>1e-6),None)
summary['all_frame_summary']={
 'first_complete_rupture_frame_by_measured_clamp_path':first_loss,
 'first_interface_opening_frame_by_measurement':first_open,
 'simultaneous_onset_checked':first_open==first_loss if a.kind=='debond' else None,
 'pre_event_every_frame_spans_clamps':all(q['has_material_surface_path_between_clamps'] for q in allchecks[:event-1]),
 'post_event_every_frame_two_clamped_fragments':all(q['components_measured']==2 and not q['has_material_surface_path_between_clamps'] and all(c['touches_lower_material_clamp']!=c['touches_upper_material_clamp'] for c in q['component_clamp_connections']) for q in allchecks[event-1:]),
 'signed_volume_initial':volume0,'signed_volume_min':min(q['signed_volume'] for q in allchecks),'signed_volume_max':max(q['signed_volume'] for q in allchecks),
 'volume_at_last_connected':allchecks[event-2]['signed_volume'],'volume_at_first_disconnected':allchecks[event-1]['signed_volume'],
 'volume_max_relative_change':max(abs(q['signed_volume']/volume0-1) for q in allchecks),
 'maximum_actual_jaw_contact_error':max(j['contact_error_max'] for q in allchecks for j in q['actual_evaluated_jaw_checks']),
 'minimum_actual_jaw_embed_z':min(j['overlap_z'] for q in allchecks for j in q['actual_evaluated_jaw_checks']),
 'maximum_non_two_face_edges':max(q['non_two_face_edges'] for q in allchecks),
 'seam_clearance_min':min(q.get('seam_clearance_measured_min',float('inf')) for q in allchecks),
 'interface_opening_max':max(q.get('interface_opening_measured',0) for q in allchecks),
 'detected_seam_or_interface_penetration':any(q.get('seam_penetration',False) or q.get('inter_ply_penetration',False) for q in allchecks),
 'position_guard':'entire fracture endpoints and full sinusoidal debond support constrained in initial material coordinates; actual fracture extrema measured each frame',
 'length_definition':'tracked outer material edge path for each future fragment; gauge length is axial projection between initial z=-1.5,+1.5 prior to rupture',
 'intact_section_definition':'same initial material section at z=1.5, outside fracture/opening region',
 'volume_interpretation':'fixed thickness and prescribed axial stretch, small volume increase is authored geometric approximation; not incompressibility',
 'pre_first_crack':allchecks[event-2],'last_actual_connection':allchecks[event-2],
 'two_prefracture_measurements_equal_reason':'abrupt whole seam failure and simultaneous interface opening; both events measured at same onset frame'}
assert summary['all_frame_summary']['pre_event_every_frame_spans_clamps']
assert summary['all_frame_summary']['post_event_every_frame_two_clamped_fragments']
assert not summary['all_frame_summary']['detected_seam_or_interface_penetration']
assert summary['all_frame_summary']['maximum_non_two_face_edges']==0
assert stop==0 and fixture_stop==0
assert a.kind!='debond' or first_open==first_loss

(out/'mesh_checks.json').write_text(json.dumps(summary,indent=2))
if not a.skip_previews:
 for f in keyframes:
  update(f);s.render.filepath=str(out/'previews'/('frame_%04d.png'%f));bpy.ops.render.render(write_still=True)
update(600);bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'))
(out/'config.json').write_text(json.dumps(C,indent=2))
SOURCE_RECORDS={'brittle': {'source': {'id': 'video_0100', 'path': '/Users/pcoffeep/Documents/BUAA/IDM/Finetune-VLLM/Vedio_data/standard-videos/video_0100.mp4', 'sha256': '79ad9d52ad9148bc12e946de390acc42c1ce0e6419b64e0220eb4bead9f89e09', 'mapping_csv': '/Users/pcoffeep/Documents/BUAA/IDM/Finetune-VLLM/Vedio_data/video_mapping.csv', 'labels_xlsx': '/Users/pcoffeep/Documents/BUAA/IDM/Finetune-VLLM/Vedio_data/all_videos_tag.xlsx', 'original_labels': {'断裂时间点': '100.166 s', '断裂模式': '脆性断裂', '材料类型': '复材', '清晰度': '720P'}, 'original_filename': '749713af810113414347fed17027ebaa.mp4', 'duration_s': 102.9, 'original_result_and_location_labels': 'not supplied in original spreadsheet'}, 'modelling_assumptions': ['所有尺寸均为无量纲作者相对几何，未由来源毫米标尺标定。', '固定相机与理想真实夹口接触；设备柔度和真实控制延迟未求解。', '采用参考约束的定性几何动画，不是有限元、本构预测或标准符合性证明。', '中央60%作为作者模拟标距，不代表来源正式标距。', '完整板条用无纤维纹理的等效连续固体表达，具体破坏组分未知。', '近下端低倾角斜裂面为作者几何近似；上裂面局部x方向剪切0.12表达来源轻微侧偏，未标定幅度。', '破断后停止加载与几何运动是DESIGN选择的试验条件，不声称原实验完全静止。', '后板按用户反馈移除，孤立设备柱按独立复核移除；夹口与固定相机保留，采用夹具与试样视图。', '破断后停止加载与运动是选定生成条件，不声称来源设备和附件完全静止。'], 'unknowns': ['材料牌号、基体、纤维种类、纤维方向、铺层数/织构。', '真实厚度、宽度、正式标距、载荷、伸长率和横梁柔度。', '真实三维裂面/界面路径、控制延迟与可恢复能量。', '来源侧视及遮挡不能证实微观纤维断裂或完整层合结构。'], 'expected_labels_six_groups': {'材料类别': '复材', '断裂结果': '完全断裂', '单一主要破坏类别': '脆性断裂', '断裂位置': '标距外非根部', '夹持异常': '无', '拍摄异常': '无'}, 'source_observations': ['来源身份来自all_videos_tag.xlsx和video_mapping.csv，颜色不作为材料依据。', '深色近侧视平板条被上下真实夹口夹持，未见金属式塑性颈缩。', '下夹口上方暴露段有局部曲折损伤，侧视投影与测量附件遮挡使准确断面结构难确认。', '事件附近上方自由端出现轻微侧偏；测量附件断后摆开，不能视为试样飞动。'], 'accepted_baseline_reference': {'metadata_path': 'outputs/current/composite_brittle_lower/composite_brittle_lower_feedback_v0_3.json', 'candidate_id': 'composite_brittle_lower_feedback_v0_3', 'implementation_version': 'composite-initial/0.3.1', 'video_sha256': 'fed17e58fe19af53240695aec7c464df4574aa55210980dc1e48fb78f0be404a', 'implementation_sha256': '596e5faf4f8fbd9f1dea27a4b7b879d9f02545644c7070707aaa239eb38a33c5', 'reference_only_acceptance_not_inherited': True}}, 'debond': {'source': {'id': 'video_0020', 'path': '/Users/pcoffeep/Documents/BUAA/IDM/Finetune-VLLM/Vedio_data/standard-videos/video_0020.mp4', 'sha256': 'c19501ad365b24bb346c6db65c7ac38a77ca54aa8ea30a09e3138042875aa831', 'mapping_csv': '/Users/pcoffeep/Documents/BUAA/IDM/Finetune-VLLM/Vedio_data/video_mapping.csv', 'labels_xlsx': '/Users/pcoffeep/Documents/BUAA/IDM/Finetune-VLLM/Vedio_data/all_videos_tag.xlsx', 'original_labels': {'断裂时间点': '25.72 s', '断裂模式': '界面脱粘', '材料类型': '复材', '清晰度': '480P'}, 'original_filename': 'http_20251104_0042.mp4', 'duration_s': 30.784, 'original_result_and_location_labels': 'not supplied in original spreadsheet'}, 'modelling_assumptions': ['两层布局仅用于界面可视化，真实铺层数和纤维方向未知。', '所有尺寸为作者相对无量纲几何，未由来源标尺标定。', '作者中央60%标距与来源未知正式标距分开。', '采用有限伸长的等宽等厚定性几何动画，不是不可压缩本构或有限元求解。', '同一瞬时事件中残余连接断开采用中央互补低倾角裂面和上半片局部面内剪切；具体破坏组分与裂面路径属于作者假设。', '事件局部x/y剪切保持源材料z坐标，没有删除材料或轴向短缩来造缝。', '17秒事件后加载端和材料保持静止；不是声称真实机器没有控制延迟、来源没有附件运动。', '固定相机与夹具试样视图，无后板和机架柱。'], 'unknowns': ['真实材料牌号、基体、纤维种类、方向、铺层/织构。', '具体失效组分及微观先后，不能由用户视觉描述证明。', '真实厚度、宽度、正式标距、载荷和标距应变。', '真实三维开口、断面、局部侧偏及设备控制延迟。'], 'expected_labels_six_groups': {'材料类别': '复材', '断裂结果': '完全断裂', '单一主要破坏类别': '界面脱粘', '断裂位置': '标距内', '夹持异常': '无', '拍摄异常': '无'}, 'source_observations': ['源XLSX记录复材、界面脱粘、25.72s；没有结果标签或两个事件相对时序标签。', '来源多数画面为近侧视细条，末景局部损伤线；换景和二维投影不能独立确认所有残余连接及微观破坏。'], 'accepted_baseline_reference': {'metadata_path': 'outputs/current/composite_interface_debond_simultaneous_complete/composite_interface_debond_simultaneous_baseline_v0_4.json', 'candidate_id': 'composite_interface_debond_simultaneous_baseline_v0_4', 'implementation_version': 'composite-initial/0.4.0', 'video_sha256': 'ff4b576ffd2c29a7c9812ce161ea4f8433993fe013183e5d082d9d7e3a963581', 'implementation_sha256': 'd3aab22f15278ad1c0b589d0c47f5e7ed048b71b7093c2b2dc30c47a3b526172', 'reference_only_acceptance_not_inherited': True}}}
record=SOURCE_RECORDS[a.kind]
labels=record['expected_labels_six_groups']
checked={k:{'value':v,'status':'geometry_checked_pending_independent_and_final_video_review'} for k,v in labels.items()}
checked['材料类别']['status']='source_record_material_identity; pending_independent_review'
checked['单一主要破坏类别']={'value':'无法确认','expected':labels['单一主要破坏类别'],'status':'pending_independent_material_behavior_and_final_video_review'}
checked['拍摄异常']={'value':'无法确认','expected':'无','status':'fixed_camera_and_key_previews_only; final_encoded_video_pending'}
event_record=lambda frame:{'frame_1_based':frame,'time_s':(frame-1)/30}
source_event=float(record['source']['original_labels']['断裂时间点'].split()[0])
metadata={'schema':'tensile-video-candidate/v1','candidate_id':out.name,'style_id':'composite_brittle_lower' if a.kind=='brittle' else 'composite_interface_debond_simultaneous_complete','status':'key_states_and600_frame_geometry_checked_pending_independent_review','design_version':'v1.12','parameter_design':'docs/fracture-variation-stage1.md','implementation_version':V,'implementation_file':str(Path(__file__).resolve()),'implementation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'full_generation_config':C,'video':{'path':str(out/(out.name+'.mp4')),'status':'not_rendered','fps':30,'frames':600,'duration_s':20,'width':960,'height':540},'source':record['source'],'accepted_baseline_reference':record['accepted_baseline_reference'],'source_observations':record['source_observations'],'observations':['All600 evaluated frames measured; geometry observations are in technical_checks. Final video visual observations pending.','No material clamp path after measured whole-seam rupture; both fragments remain attached to their respective jaw.','Interface opens at the same measured frame as rupture.' if a.kind=='debond' else 'Entire measured oblique seam stays outside lower authored gauge boundary and above lower clamp root.'],'modelling_assumptions':record['modelling_assumptions']+['Stage1 changes are uncalibrated qualitative author parameters; source does not measure these candidate values.','Discrete candidate changes do not establish continuous accepted ranges.'],'unknowns':record['unknowns'],'time_mapping':{'frame_definition':'PTS=(frame-1)/30;600 displayed frames cover20s, final frame PTS19.9666666667','source_annotation_s':source_event,'source_annotation_is':'provided source label, not physical highspeed timestamp','anchor_pairs_source_to_generated_s':[[0,0],[source_event,a.event_time_s],[record['source']['duration_s'],20]],'events':{'loading_start':event_record(1),'first_crack':event_record(first_loss),'debond_start':event_record(first_open) if first_open else None,'final_loss_of_clamp_path':event_record(first_loss),'geometric_complete_separation':event_record(first_loss),'visually_readable_complete_separation':'pending_final_video_review','postevent_stop':event_record(event)}},'expected_labels_six_groups':labels,'checked_labels_six_groups':checked,'technical_checks':summary,'acceptance':{'user_accepted':False,'style_accepted':False,'parameter_range_accepted':False,'training_released':False,'independent_review':'pending','main_final_video_view':'pending','acceptance_scope':'unaccepted_single_parameter_candidate'},'user_accepted':False,'style_accepted':False,'parameter_range_accepted':False,'training_released':False,'limitations':['No constitutive or microscopic failure validation.','Seam plane and interply clearance measured; full triangle selfintersection not checked.','Final encoded video, human view and independent review pending.']}
(out/(out.name+'.json')).write_text(json.dumps(metadata,indent=2,ensure_ascii=False))

if a.render:
 for f in range(1,601):
  update(f);s.render.filepath=str(out/'frames'/('frame_%04d.png'%f))
  if not(a.resume and Path(s.render.filepath).exists()):bpy.ops.render.render(write_still=True)
