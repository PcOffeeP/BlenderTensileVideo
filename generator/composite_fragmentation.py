"""Qualitative source-constrained rapid splitting of a narrow composite strip.
Run Blender --background --python generator/composite_fragmentation.py -- --out DIR [--render].
Fixed baseline only; no approved parameter range or constitutive inference.
"""
import bpy, math, json, sys, argparse
from pathlib import Path
from mathutils import Vector
VERSION='composite-fragmentation/0.1.0'
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--render',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
C={'implementation_version':VERSION,'fps':30,'frames':600,'resolution':[960,540],'loading_axis':'z','fixed_end':'lower','moving_end':'upper','free_span':5.0,'width':0.60,'strand_boundaries':[-.3,-.22,-.11,-.025,.09,.19,.3],'strand_splay_x':[-.085,-.040,-.022,.009,.034,.073],'strand_shear_factors':[.95,1.1,.9,1.05,.98,1.0],'surface_texture':'subtle axial colour bands, illustrative rather than observed fiber orientation','thickness':0.12,'grip_overlap':0.48,'synthetic_gauge':[-1.5,1.5],'units':'dimensionless relative coordinates','event_frame':481,'settled_frame':526,'maximum_grip_displacement':0.10,'strand_count':6,'strand_seam_centres':[-.25,.12,-.05,.26,-.15,.05],'fracture_plane_slope_y':0.8,'local_shear_y':0.10,'splay_plateau_z':[-.35,.35],'splay_zero_z':[-.85,.85],'decay_amplitude_ratio':0.16,'decay_cycles':2.0,'free_detached_fragments':0,'camera':{'position':[9,-17,3],'look_at':[0,0,0],'projection':'orthographic','ortho_scale':16.4},'renderer':{'engine':'BLENDER_WORKBENCH','studio_light':'paint.sl','aa':'8','world_color':[.13,.16,.19],'cavity':'BOTH','color':'MATERIAL','view_transform':'Standard'},'fixture':{'jaw_inner_y':[-.06,.06],'jaw_centres_y':[-.26,.26],'jaw_size':[1.48,.40,.72],'jaw_centres_z':[-2.86,2.86],'body_size':[2.40,1.1,.70],'body_centres_z':[-3.33,3.33],'shaft_size':[.75,.80,.57],'shaft_centres_z':[-3.94,3.94],'bolt_x':[-.96,.96],'bolt_size':[.19,.12,.19],'bevel_width':.035,'bevel_segments':3},'encoding':{'codec':'libx264','preset':'slow','crf':16,'pixel_format':'yuv420p'},'rear_panel':False,'machine_columns':False,'no_constitutive_solver':True,'scope':'fixed qualitative rapid rupture with longitudinal branched remnants; strand count and geometry authored, reinforcement and layup unknown'}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x,s.render.resolution_y=C['resolution'];s.render.resolution_percentage=100;s.render.fps=30;s.frame_start=1;s.frame_end=600;s.render.image_settings.file_format='PNG';s.render.film_transparent=False
sh=s.display.shading;sh.light='STUDIO';sh.studiolight_rotate_z=.5;sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=1.1;sh.curvature_valley_factor=1.1;sh.show_specular_highlight=True;sh.background_type='WORLD';s.world.color=(.13,.16,.19);s.display.render_aa='8';s.view_settings.view_transform='Standard'
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
steel=mat('fixture satin steel',(.44,.49,.53));jawmat=mat('gripping jaw',(.15,.18,.2));dark=mat('fastener',(.08,.10,.12));specmat=mat('dark composite narrow strip',(.055,.068,.075));surface_mats=[specmat]+[mat('illustrative axial surface band '+str(i),(.055+i*.0018,.068+i*.0018,.075+i*.0018)) for i in range(1,5)]
def box(n,loc,size,m,bev=.035):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bev:q=o.modifiers.new('machined edges','BEVEL');q.width=bev;q.segments=3;o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 return o
fixtures=[]
for sign in [-1,1]:
 for y in [-.26,.26]:fixtures.append((box(('lower' if sign<0 else 'upper')+' jaw '+str(y),(0,y,sign*2.86),(1.48,.40,.72),jawmat),sign))
 fixtures.append((box('fixture body '+str(sign),(0,.30,sign*3.33),(2.40,1.1,.70),steel),sign));fixtures.append((box('loading shaft '+str(sign),(0,.33,sign*3.94),(.75,.80,.57),steel),sign))
 for x in [-.96,.96]:fixtures.append((box('bolt '+str(sign)+str(x),(x,-.32,sign*3.31),(.19,.12,.19),dark,.06),sign))
bpy.ops.object.camera_add(location=(9,-17,3));cam=bpy.context.object;cam.name='fixed_camera';cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=16.4;s.camera=cam
base_fixture={o.name:o.location.z for o,sg in fixtures}
def smooth(v):v=max(0,min(1,v));return v*v*(3-2*v)
def displacement(f):return .10*smooth((min(f,481)-1)/480)
def event_strength(f):
 if f<481:return 0.0
 if f>=526:return 1.0
 u=(f-481)/45
 return 1+.16*(1-u)**2*math.sin(4*math.pi*u)
def envelope(z):return max(0,min(1,(.85-abs(z))/.50))
def build(f):
 d=displacement(f);strength=event_strength(f);vs=[];src=[];faces=[];cache={}
 # Common cell planes allow genuinely welded neighbours before rupture, not merely coincident objects.
 # All event shear is piecewise affine in actual z; unit determinant preserves material volume.
 seams=sorted(C['strand_seam_centres']);levels=[(-2.98,0),(-2.5,0),(-.85,0),(-.35,0)]+[(z,.8) for z in seams]+[(.35,0),(.85,0),(2.5,0),(2.98,0)]
 def vid(v,q):
  k=tuple(round(t,9) for t in v)
  if k not in cache:cache[k]=len(vs);vs.append(v);src.append(q)
  return cache[k]
 for i,cut in enumerate(C['strand_seam_centres']):
  cutindex=next(j for j,(u,sl) in enumerate(levels) if sl and abs(u-cut)<1e-8)
  for sub in range(8):
   left,right=C['strand_boundaries'][i:i+2];xa=left+(right-left)*sub/8;xb=left+(right-left)*(sub+1)/8
   for j in range(len(levels)-1):
    part=0 if j<cutindex else 1;ids=[]
    for k in [j,j+1]:
     u,sl=levels[k]
     for x,y in [(xa,-.06),(xb,-.06),(xb,.06),(xa,.06)]:
      z=u+sl*y;e=envelope(z);sg=1 if part==0 else -1
      xx=x+C['strand_splay_x'][i]*strength*e;yy=y+sg*.10*C['strand_shear_factors'][i]*strength*e;zz=z+d*max(0,min(1,(z+2.5)/5))
      ids.append(vid((xx,yy,zz),(x,y,z,i,part)))
    for inds in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:faces.append(tuple(ids[k] for k in inds))
 seen={};discard=set()
 for k,face in enumerate(faces):
  kk=tuple(sorted(face))
  if kk in seen:discard.update([k,seen[kk]])
  else:seen[kk]=k
 faces=[fa for k,fa in enumerate(faces) if k not in discard];used=sorted({i for fa in faces for i in fa});remap={old:new for new,old in enumerate(used)};vs=[vs[i] for i in used];src=[src[i] for i in used];faces=[tuple(remap[i] for i in fa) for fa in faces]
 me=bpy.data.meshes.new('conserved strip material');me.from_pydata(vs,[],faces);[me.materials.append(m) for m in surface_mats];me.update();attr=me.attributes.new('source_coordinate','FLOAT_VECTOR','POINT')
 for i,q in enumerate(src):attr.data[i].vector=q[:3]
 for pp in me.polygons:
  pp.use_smooth=False;pp.material_index=int(abs(sum(src[i][0] for i in pp.vertices)/len(pp.vertices))*1700)%5
 return me
obj=bpy.data.objects.new('actual_composite_material',build(1));s.collection.objects.link(obj)
def update(f):
 old=obj.data;obj.data=build(f);bpy.data.meshes.remove(old)
 for o,sg in fixtures:o.location.z=base_fixture[o.name]+(displacement(f) if sg>0 else 0)
 s.frame_set(f)
def check(f):
 update(f);dg=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dg);me=ev.to_mesh();vv=[obj.matrix_world@v.co for v in me.vertices];adj=[set() for _ in vv]
 for e in me.edges:u,w=e.vertices;adj[u].add(w);adj[w].add(u)
 seen=set();cs=[]
 for k in range(len(vv)):
  if k in seen:continue
  ids=[];todo=[k];seen.add(k)
  while todo:
   u=todo.pop();ids.append(u)
   for w in adj[u]:
    if w not in seen:seen.add(w);todo.append(w)
  cs.append(ids)
 d=displacement(f);me.calc_loop_triangles();vol=sum(vv[t.vertices[0]].dot(vv[t.vertices[1]].cross(vv[t.vertices[2]]))/6 for t in me.loop_triangles)
 con=[{'vertices':len(ids),'lower':any(vv[i].z< -2.49999 for i in ids),'upper':any(vv[i].z>2.49999+d for i in ids)} for ids in cs]
 # Actual jaw contact: evaluated inner faces and specimen material points in the embedded range.
 jawerrors=[];jawoverlaps=[]
 for sg in [-1,1]:
  pts=[v for v in vv if ((-2.981<v.z< -2.49999) if sg<0 else (2.49999+d<v.z<2.981+d))]
  errors=[]
  for o,qsg in fixtures:
   if qsg!=sg or ' jaw ' not in o.name:continue
   ee=o.evaluated_get(dg);jm=ee.to_mesh();jv=[o.matrix_world@v.co for v in jm.vertices];inner=max(v.y for v in jv) if o.location.y<0 else min(v.y for v in jv);errors.append(min(abs(v.y-inner) for v in pts));jawoverlaps.append(min(max(v.z for v in pts),max(v.z for v in jv))-max(min(v.z for v in pts),min(v.z for v in jv)));ee.to_mesh_clear()
  jawerrors.append(max(errors))
 # Corresponding source sections remain finite rectangular material sections; segment edges measured from actual source attributes.
 sections={};paths={}
 for i,v in enumerate(vv):
  q=me.attributes['source_coordinate'].data[i].vector
  paths.setdefault((round(q.x,6),round(q.y,6)),[]).append((round(q.z,6),v))
 lengths=[]
 # At rupture shared seam points intentionally duplicate; group each material branch by actual edge adjacency rather than connecting gaps.
 for x in [-.3,.3]:
  ids=[i for i in range(len(vv)) if abs(me.attributes['source_coordinate'].data[i].vector.x-x)<1e-6 and abs(me.attributes['source_coordinate'].data[i].vector.y+.06)<1e-6]
  idsset=set(ids);lengths.append(sum((vv[e.vertices[0]]-vv[e.vertices[1]]).length for e in me.edges if e.vertices[0] in idsset and e.vertices[1] in idsset))
 r={'frame':f,'time_s':(f-1)/30,'component_count_measured':len(cs),'components':con,'has_material_path_between_jaws':any(c['lower'] and c['upper'] for c in con),'signed_material_volume':vol,'jaw_contact_max_error':jawerrors,'jaw_embedded_z_overlap_min':min(jawoverlaps),'upper_jaw_displacement':d,'z_bounds':[min(v.z for v in vv),max(v.z for v in vv)],'same_material_outer_edge_lengths':lengths,'authored_strand_widths':[round(b-a,6) for a,b in zip(C['strand_boundaries'],C['strand_boundaries'][1:])],'authored_thickness':.12,'splay_strength':event_strength(f),'coordinates':[[round(t,9) for t in v] for v in vv]}
 # Measure actual complementary cap clearances and neighbouring strip boundary separation.
 caps={}
 for pp in me.polygons:
  qq=[me.attributes['source_coordinate'].data[i].vector for i in pp.vertices]
  for cut in C['strand_seam_centres']:
   if all(abs(q.z-.8*q.y-cut)<1e-6 for q in qq):
    ys=[vv[i].y for i in pp.vertices];dy=sum(vv[i].y-q.y for i,q in zip(pp.vertices,qq))/len(qq)
    caps.setdefault(cut,{'lower':[],'upper':[]})['lower' if dy>0 else 'upper'].extend(ys)
 clear=[min(q['lower'])-max(q['upper']) for q in caps.values() if q['lower'] and q['upper']]
 r['rupture_cap_y_clearance_min_measured']=min(clear) if clear else 0.0
 r['cap_clearance_applicability']='separated complementary faces, y separating-axis clearance' if clear else 'before rupture, caps are welded internal material'
 rings={};thickness=[];widths=[]
 for i,v in enumerate(vv):
  q=me.attributes['source_coordinate'].data[i].vector
  if abs(abs(q.z)-.35)<1e-6:
   rings.setdefault((round(q.x,6),round(q.z,6)),[]).append((q.y,v))
 for edge in me.edges:
  i,j=edge.vertices;qi=me.attributes['source_coordinate'].data[i].vector;qj=me.attributes['source_coordinate'].data[j].vector
  if abs(qi.x-qj.x)<1e-6 and abs(qi.z-qj.z)<1e-6 and abs(abs(qi.z)-.35)<1e-6 and abs(qi.y-qj.y)>.11999:thickness.append((vv[i]-vv[j]).length)
 # Width and area of actual planar section pairs at z=+/-0.4 are measured independently of splay translation.
 for zi in [-.35,.35]:
  for strand in range(6):
   xa,xb=C['strand_boundaries'][strand:strand+2];pa=[];pb=[]
   for i,v in enumerate(vv):
    q=me.attributes['source_coordinate'].data[i].vector
    if abs(q.z-zi)<1e-6 and abs(q.y+.06)<1e-6:
     if abs(q.x-xa)<1e-6:pa.append(v)
     if abs(q.x-xb)<1e-6:pb.append(v)
   distances=[(b-a).length for a in pa for b in pb]
   if distances:widths.append(min(distances))
 r['section_thickness_min_measured']=min(thickness);r['section_width_min_measured']=min(widths);r['section_area_min_measured']=min(thickness)*min(widths)
 boundary={}
 for i,v in enumerate(vv):
  q=me.attributes['source_coordinate'].data[i].vector
  if any(abs(q.x-x)<1e-6 for x in C['strand_boundaries'][1:-1]):boundary.setdefault(tuple(round(t,6) for t in q),[]).append(v.x)
 gaps=[max(vals)-min(vals) for vals in boundary.values()]
 r['adjacent_strip_boundary_x_clearance_min_measured']=min(gaps,default=0);r['adjacent_strip_boundary_x_clearance_max_measured']=max(gaps,default=0)
 r['cap_penetration_detected']=bool(clear and min(clear)<-1e-6)
 r['penetration_check_scope']='actual complementary cap y separating axes and corresponding neighbouring strip x boundary distances; fixed ordered branch maps, no swept collision solver'
 ev.to_mesh_clear();return r
keyframes=[1,241,478,479,480,481,482,483,484,490,500,510,526,600]
checks=[check(f) for f in keyframes];post=[check(f) for f in [526,527,570,600]];stop=max(max(abs(x-y) for x,y in zip(sum(post[0]['coordinates'],[]),sum(q['coordinates'],[]))) for q in post)
for q in checks:q.pop('coordinates')
for f in keyframes:update(f);s.render.filepath=str(out/'previews'/('frame_%04d.png'%f));bpy.ops.render.render(write_still=True)
(out/'mesh_checks.json').write_text(json.dumps({'config':C,'samples':checks,'post_settle_max_vertex_displacement':stop,'measurement_scope':'actual evaluated graph, signed closed surface volume, jaw inner faces and material points; measured sections at source z=+/-0.35, complementary cap and strip-boundary separating axes; no constitutive or swept collision solver'},indent=2))
update(600);bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'));(out/'config.json').write_text(json.dumps(C,indent=2))
if a.render:
 allchecks=[]
 for f in range(1,601):
  r=check(f);r.pop('coordinates');allchecks.append(r);s.render.filepath=str(out/'frames'/('frame_%04d.png'%f))
  if not(a.resume and Path(s.render.filepath).exists()):bpy.ops.render.render(write_still=True)
 (out/'all_frame_mesh_checks.json').write_text(json.dumps(allchecks,indent=2))
