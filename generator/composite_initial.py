import bpy, math, json, sys, os, argparse
from pathlib import Path
from mathutils import Vector
V='composite-initial/0.3.1'
p=argparse.ArgumentParser();p.add_argument('--kind',choices=['debond','brittle'],required=True);p.add_argument('--out',required=True);p.add_argument('--render',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
C={'version':V,'kind':a.kind,'fps':30,'frames':600,'resolution':[960,540],'loading_axis':'z','fixed_end':'lower','moving_end':'upper','free_span':5.0,'width':1.0,'thickness':0.18,'grip_overlap':0.48,'gauge_authored':[-1.5,1.5],'units':'dimensionless relative coordinates','event_frame':511,'maximum_grip_displacement':0.14 if a.kind=='debond' else 0.10,'fracture_z':-1.83 if a.kind=='brittle' else 0.0,'rear_panel':False,'machine_columns':False,'debond_final_result':'complete_rupture_after_interface_damage','debond_fracture_slope':0.22,'debond_local_shear':0.12,'debond_damage_full_frame':481,'brittle_local_shear':0.12,'brittle_fracture_slope':0.22,'no_constitutive_solver':True}
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
  strength=smooth((min(f,481)-361)/120);length=1.6*strength
  for ply in range(2):
   sg=-1 if ply==0 else 1
   for part in range(2):
    def point(x,y,z):
     z1=z+d*max(0,min(1,(z+2.5)/5))
     env=0 if length==0 or abs(z)>=length/2 else math.sin(math.pi*(z+length/2)/length)**2
     opening=.10*strength*env
     x1=x
     if part==1 and f>=511:
      cut=1.2+d*3.7/5
      x1-=.12*max(0,(cut-z1)/(cut-d/2))
     result=(x1,y+sg*opening/2,z1)
     source_map[tuple(round(t,9) for t in result)]=(x,y,z,ply,part)
     return result
    for xa,xb in zip(xs,xs[1:]):
     def levels(x):
      br=.22*x
      return [-2.98,-2.5]+[-.8+i*.1 for i in range(7)]+[br] if part==0 else [br]+[.2+i*.1 for i in range(7)]+[1.2,2.5,2.98]
     lz=levels(xa);rz=levels(xb)
     ya,yb=(-.09,0) if ply==0 else (0,.09)
     for j in range(len(lz)-1):
      corners=[point(xa,ya,lz[j]),point(xb,ya,rz[j]),point(xb,yb,rz[j]),point(xa,yb,lz[j]),point(xa,ya,lz[j+1]),point(xb,ya,rz[j+1]),point(xb,yb,rz[j+1]),point(xa,yb,lz[j+1])]
      addcell(corners,ply)
 else:
  xs=[-.5+i/20 for i in range(21)]
  progress=1.0 if f>=511 else 0.0;gap=0.0
  crackfront=-.5+progress
  def seam(x):return -1.83+.22*x
  def point(x,y,t,part):
   br=seam(x);fract=progress>0 and x<crackfront+1e-8
   opening=gap if fract else 0
   bz=br+d*(br+2.5)/5
   if part==0:
    zb=-2.98+(br+2.98)*t
    zz=zb+d*max(0,min(1,(zb+2.5)/5))
   else:
    zb=br+(-.63-br)*t if t<=1 else (-.63+(2.5+.63)*(t-1) if t<=2 else 2.98)
    zz=zb+d*max(0,min(1,(zb+2.5)/5))
    cut=-.63+d*1.87/5
    x-=.12*progress*max(0,(cut-zz)/(cut+1.83))
   return (x,y,zz)
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
 if a.kind=='debond':
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
    if f<511 and abs(src.z-.22*src.x)<1e-6:
     paths[ply][0].append((src.z,vv));paths[ply][1].append((src.z,vv))
    else:paths[ply][part].append((src.z,vv))
  r['same_material_outer_ply_segment_lengths']=[[sum((bb[1]-aa[1]).length for aa,bb in zip(pp,pp[1:])) for pp in [sorted(path,key=lambda q:q[0]) for path in ply]] for ply in paths]
  r['section_actual_ply_thickness']=None
 else:
  si=set()
  for pp in me.polygons:
   if pp.normal.x<-.9 and abs(pp.normal.y)<.1:si.update(pp.vertices)
  boundary=[v[i] for i in si if abs(v[i].y+.09)<1e-6]
  zcut=-1.94+d*.56/5;lower=[];upper=[]
  for vv in boundary:
   if vv.z<zcut-1e-5:lower.append(vv)
   elif vv.z>zcut+1e-5:upper.append(vv)
   elif f<511:lower.append(vv);upper.append(vv)
   elif abs(vv.x+.5)<1e-5:lower.append(vv)
   else:upper.append(vv)
  r['same_material_lower_upper_left_edge_lengths']=[sum((bb-aa).length for aa,bb in zip(pp,pp[1:])) for pp in [sorted(lower,key=lambda vv:vv.z),sorted(upper,key=lambda vv:vv.z)]]
  r['section_actual_thickness']=max(vv.y for vv in v)-min(vv.y for vv in v)
 # Actual interface opening and fracture-face clearance from evaluated vertices and polygon planes.
 if a.kind=='debond':
  owned=[set(),set()]
  for pp in me.polygons:owned[pp.material_index].update(pp.vertices)
  rings={}
  for ply,ids in enumerate(owned):
   for i in ids:
    src=me.attributes['source_coordinate'].data[i].vector;part=me.attributes['source_part'].data[i].value
    key=(round(src.x,6),round(src.z,6),part if f>=511 else 0)
    rings.setdefault(key,[[],[]])[ply].append(v[i].y)
  gaps=[];th=[]
  for lower,upper in rings.values():
   if lower and upper:gaps.append(min(upper)-max(lower));th.extend([max(lower)-min(lower),max(upper)-min(upper)])
  r['interface_opening_measured']=max(gaps,default=0);r['interface_clearance_measured_min']=min(gaps,default=0);r['ply_thickness_measured_min']=min(th,default=.09);r['inter_ply_penetration']=min(gaps,default=0)<-1e-6;r['section_actual_ply_thickness']=r['ply_thickness_measured_min']
 if f>=511 and len(comps)==2:
  seam=[]
  for pol in me.polygons:
   if abs(pol.normal.z)>.9 and ((-.2<pol.center.z<.3) if a.kind=='debond' else (-2.0<pol.center.z<-1.6)):
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
 ev.to_mesh_clear();return r
keyframes=[1,241,362,421,481,510,511,540,600] if a.kind=='debond' else [1,241,481,507,510,511,540,600]
checks=[check(f) for f in keyframes]
# Post-event equality uses actual evaluated material coordinates, plus actual fixture locations.
post=[check(f) for f in [C['event_frame'],C['event_frame']+1,540,600]]
stop=max(max(abs(x-y) for x,y in zip(sum(post[0]['coordinates'],[]),sum(q['coordinates'],[]))) for q in post)
for q in checks:q.pop('coordinates')
for f in keyframes:
 update(f);s.render.filepath=str(out/'previews'/('frame_%04d.png'%f));bpy.ops.render.render(write_still=True)
(out/'mesh_checks.json').write_text(json.dumps({'implementation_version':V,'config':C,'samples':checks,'post_event_max_vertex_displacement':stop,'scope':'evaluated mesh graph connectivity, signed closed material volume, face-to-jaw contact, fixed postevent geometry; no independent physics solver','contact_semantics':'intentional material overlap in jaws; face contact y=+/-0.09, grip embed 0.48','inter_ply_gap_max':0.10 if a.kind=='debond' else None,'fracture_opening_max':None,'fracture_gap_method':'measured local lateral shear across slanted complementary surfaces, no axial shortening' if a.kind in ['brittle','debond'] else None},indent=2))
update(600);bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'))
(out/'config.json').write_text(json.dumps(C,indent=2))
if a.render:
 allchecks=[]
 for f in range(1,601):
  rr=check(f);rr.pop('coordinates');allchecks.append(rr)
  s.render.filepath=str(out/'frames'/('frame_%04d.png'%f))
  if not(a.resume and Path(s.render.filepath).exists()):bpy.ops.render.render(write_still=True)

if a.render:(out/'all_frame_mesh_checks.json').write_text(json.dumps(allchecks,indent=2))
