"""Build ignored major-fracture review candidates.

/Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python \
  scripts/build_major_fracture_review_batch.py -- --id 0003 --stage keyframes
/Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python \
  scripts/build_major_fracture_review_batch.py -- --id 0003 --stage video
"""
from pathlib import Path
import bpy, json, sys, math, hashlib, os
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if len(args)!=4 or args[0]!='--id' or args[2]!='--stage' or args[1] not in {'0003','0004','0005','0006','0007','0008'} or args[3] not in {'keyframes','video'}: raise ValueError('use -- --id 0003 --stage keyframes|video')
ID,STAGE=args[1],args[3]; CONFIG=ROOT/'configs'/f'synthetic_{ID}.json'; C=json.loads(CONFIG.read_text()); I=C['implementation']; OUT=ROOT/'artifacts'/'review_batches'/'major_fractures_v1'/C['video_id']; OUT.mkdir(parents=True,exist_ok=True)
F=int(I['fracture_frame']); PRE=F-1; N=300; FPS=30; CASE=I['review_case']; CUT={'metal_outside_ductile':2.55,'metal_grip_brittle':3.35}.get(CASE,0.0)

def clear():
 bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
 for b in (bpy.data.meshes,bpy.data.materials,bpy.data.lights,bpy.data.cameras):
  for x in b: b.remove(x)
def material(name,c,metal=0,rough=.5):
 m=bpy.data.materials.new(name); m.diffuse_color=(*c,1); m.use_nodes=True; b=next(x for x in m.node_tree.nodes if x.type=='BSDF_PRINCIPLED'); b.inputs['Base Color'].default_value=(*c,1); b.inputs['Metallic'].default_value=metal; b.inputs['Roughness'].default_value=rough; return m
def cube(n,loc,scale,m):
 bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object;o.name=n;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);be=o.modifiers.new('round','BEVEL');be.width=.06;be.segments=2;return o
def mesh(n,p,m):
 d=.15; v=[(x,-d/2,z) for x,z in p]+[(x,d/2,z) for x,z in p]; q=len(p); faces=[tuple(range(q)),tuple(range(q,2*q))]+[(i,(i+1)%q,(i+1)%q+q,i+q) for i in range(q)]; me=bpy.data.meshes.new(n);me.from_pydata(v,[],faces);me.materials.append(m);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);be=o.modifiers.new('micro','BEVEL');be.width=.018;be.segments=2;return o
def shard(n,x,z,s,m): return mesh(n,[(x-.10*s,z-.05*s),(x+.08*s,z-.08*s),(x+.12*s,z+.04*s),(x-.02*s,z+.11*s),(x-.12*s,z+.03*s)],m)
def shift(f): return .42*min(1,(f-1)/(PRE-1))
def gap(f): return .56+.08*min(1,max(0,f-F)/3)
def neck(f):
 p=min(1,max(0,(f-(F-80))/80)); return {'polymer_ductile':.26,'metal_mixed':.10,'metal_outside_ductile':.30}.get(CASE,0)*p
def width(z,f):
 az=abs(z); u=max(0,min(1,(az-2)/1.2)); smooth=u*u*(3-2*u)
 base=.5+.4*smooth
 center=CUT
 return base-neck(f)*math.exp(-((z-center)/.48)**2) if abs(z)<=3.2 else base
def mz(z,f): return z+shift(f)*max(0,min(1,(z+4)/8))
def irregular(w): return [(-w,-.045),(-.32*w,.02),(.04*w,-.035),(.43*w,.055),(w,.01)]
def continuous(f,m):
 zs=[-4,-3.2,-2.4,-2,-1.5,-1,-.5,0,.5,1,1.5,2,2.4,3.2,4]; return mesh('Continuous',[(-width(z,f),mz(z,f)) for z in zs]+[(width(z,f),mz(z,f)) for z in reversed(zs)],m)
def split(f,m):
 cut=CUT; g=gap(f); zsL=[-4,-3.2,-2.4,-2,-1.5,-1,-.5]; zsU=[.5,1,1.5,2,2.4,3.2,4]
 if cut!=0:
  zsL=[z for z in zsL if z<cut]; zsU=[z for z in zsU if z>cut]
  if not zsL or abs(zsL[-1]-(cut-.15))>1e-8: zsL.append(cut-.15)
  if not zsU or abs(zsU[0]-(cut+.15))>1e-8: zsU.insert(0,cut+.15)
 w=width(cut,f); prof=irregular(w); base=mz(cut,f)
 low=[(-width(z,f),mz(z,f)-g/2*max(0,min(1,(z+2)/2))) for z in zsL]+[(x,base+dz-g/2) for x,dz in prof]+[(width(z,f),mz(z,f)-g/2*max(0,min(1,(z+2)/2))) for z in reversed(zsL)]
 up=[(-width(z,f),mz(z,f)+g/2*max(0,min(1,(2-z)/2))) for z in zsU]+[(width(z,f),mz(z,f)+g/2*max(0,min(1,(2-z)/2))) for z in reversed(zsU)]+[(x,base+dz+g/2) for x,dz in reversed(prof)]
 return [mesh('Lower',low,m),mesh('Upper',up,m)]
def lap_joint(f,m):
 # Two offset laminate tabs make the load-transfer interface visible in front view.
 g=0 if f<=PRE else gap(f); lower_top=.82-g/2; upper_shift=shift(f); upper_bottom=(-.82+upper_shift) if f<=PRE else (.82+upper_shift+g/2)
 lower=mesh('Laminate_Lower_Tab',[(-.55,-4),(-.05,-4),(-.05,lower_top),(-.55,lower_top)],m)
 upper=mesh('Laminate_Upper_Tab',[(.05,upper_bottom),(.55,upper_bottom),(.55,4+upper_shift),(.05,4+upper_shift)],m)
 if f<=PRE:
  bond=material('Bonded_Interface',(.24,.25,.25),.1,.65); mid=(lower_top+upper_bottom)/2; return [lower,upper,cube('Bonded_Overlap',(0,0,mid),(.10,.10,(lower_top-upper_bottom)/2),bond)]
 return [lower,upper]
def machine(f):
 dark=material('machine',(.11,.13,.15),.7,.45); jaw=material('jaws',(.28,.29,.30),.75,.35); s=shift(f)
 cube('cross_lower',(0,0,-4.35),(2.8,.5,.22),dark);cube('cross_upper',(0,0,4.35+s),(2.8,.5,.22),dark)
 for a in(-1,1): cube('jawL',(a*1.18,0,-3.7),(.34,.4,.6),jaw);cube('jawU',(a*1.18,0,3.7+s),(.34,.4,.6),jaw)
def setup():
 sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=854;sc.render.resolution_y=480;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.fps=FPS;sc.world.color=(.14,.14,.14)
 camd=bpy.data.cameras.new('fixed');camd.type='ORTHO';camd.ortho_scale=19.5;cam=bpy.data.objects.new('fixed',camd);bpy.context.collection.objects.link(cam);cam.location=(0,-20,.3);cam.rotation_euler=((Vector((0,0,.3))-cam.location).to_track_quat('-Z','Y')).to_euler();sc.camera=cam
 bg=material('bg',(.19,.19,.19),0,.8);cube('bg',(0,1,.3),(20,.08,10),bg)
 for n,l,e in [('key',(-4,-5,5),180),('fill',(4,-4,1),130),('front',(0,-6,0),100)]:
  d=bpy.data.lights.new(n,'AREA');d.energy=e;d.shape='DISK';d.size=5;o=bpy.data.objects.new(n,d);bpy.context.collection.objects.link(o);o.location=l;o.rotation_euler=((Vector((0,0,0))-o.location).to_track_quat('-Z','Y')).to_euler()
def build_state(f):
 clear();setup();machine(f); colors={'高分子':((.42,.42,.39),0,.72),'复材':((.32,.34,.34),.15,.58),'金属':((.45,.45,.45),.8,.48)}; c,me,r=colors[C['material_type']];sm=material('specimen',c,me,r)
 if CASE=='composite_delamination': lap_joint(f,sm)
 elif f<=PRE: continuous(f,sm)
 else:
  split(f,sm)
  if CASE=='composite_explosive':
   frag=material('fragment',(.30,.32,.32),.2,.58)
   for i,(x,z) in enumerate([(-.7,.1),(.58,.23),(-.32,-.35),(.31,-.2)]):
    q=min(1,(f-F)/5); shard('fragment'+str(i),x*(.6+q),mz(0,f)+z*(.4+q),.7+.25*(i%2),frag)
def render_frame(f,name): build_state(f);sc=bpy.context.scene;sc.frame_set(f);sc.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
def video():
 clear();setup(); colors={'高分子':((.42,.42,.39),0,.72),'复材':((.32,.34,.34),.15,.58),'金属':((.45,.45,.45),.8,.48)};c,me,r=colors[C['material_type']];sm=material('specimen',c,me,r); machine(1); objs=[]
 # animate upper machine only
 for o in bpy.data.objects:
  if 'upper' in o.name.lower() or 'jawU' in o.name:
   base=o.location.z
   for f in range(1,N+1): o.location.z=base+shift(f);o.keyframe_insert('location',frame=f)
 for f in range(1,N+1):
  made=lap_joint(f,sm) if CASE=='composite_delamination' else ([continuous(f,sm)] if f<=PRE else split(f,sm))
  if CASE=='composite_explosive' and f>PRE:
   fm=material('fragment'+str(f),(.3,.32,.32),.2,.58)
   for i,(x,z) in enumerate([(-.7,.1),(.58,.23),(-.32,-.35),(.31,-.2)]):
    q=min(1,(f-F)/5);made.append(shard('frag',x*(.6+q),mz(0,f)+z*(.4+q),.7+.25*(i%2),fm))
  for o in made:
   o.hide_render=True;o.keyframe_insert('hide_render',frame=1);o.hide_render=False;o.keyframe_insert('hide_render',frame=f)
   if f<N:o.hide_render=True;o.keyframe_insert('hide_render',frame=f+1)
 sc=bpy.context.scene;sc.frame_start=1;sc.frame_end=N;sc.render.image_settings.media_type='VIDEO';sc.render.ffmpeg.format='MPEG4';sc.render.ffmpeg.codec='H264';sc.render.ffmpeg.constant_rate_factor='MEDIUM';sc.render.ffmpeg.ffmpeg_preset='REALTIME';tmp=OUT/(C['video_id']+'.rendering.mp4');final=OUT/(C['video_id']+'.mp4');
 if tmp.exists(): raise RuntimeError('stale temporary render exists')
 sc.render.filepath=str(tmp);bpy.ops.render.render(animation=True);os.replace(tmp,final);e={'schema_version':'synthetic-render-evidence/v0.1','video_id':C['video_id'],'config_sha256':hashlib.sha256(CONFIG.read_bytes()).hexdigest(),'generator_script':'scripts/build_major_fracture_review_batch.py','generator_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'video_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'first_separated_frame':F};(OUT/'render-evidence.json').write_text(json.dumps(e,indent=2)+'\n')
if STAGE=='keyframes':
 for f,n in [(1,'initial_f001.png'),(max(2,PRE-45),'precursor.png'),(PRE,'prefracture.png'),(F,'first_separation.png'),(min(N,F+20),'stable_postfracture.png')]:render_frame(f,n)
else: video()
