"""Create a reusable reference-constrained metal round-bar tensile candidate.

Usage: Blender --background --python render_metal_round.py -- --config CONFIG --out OUTPUT
OUTPUT receives a blend, numbered PNG sequence, five previews, and actual
evaluated-mesh checks.  Video encoding remains an explicit caller operation.
"""
import argparse, json, math, os, sys
import bpy
from mathutils import Vector

def args():
    p=argparse.ArgumentParser(); p.add_argument('--config',required=True); p.add_argument('--out',required=True); p.add_argument('--preview-only',action='store_true')
    return p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])

def mat(name, color, metallic, rough):
    m=bpy.data.materials.new(name); m.use_nodes=True
    b=next(x for x in m.node_tree.nodes if x.type=='BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value=(*color,1); b.inputs['Metallic'].default_value=metallic; b.inputs['Roughness'].default_value=rough
    return m

def profile(name, zs, rs, material):
    n=64; verts=[]; faces=[]
    for z,r in zip(zs,rs):
        for i in range(n):
            a=2*math.pi*i/n; verts.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(len(zs)-1):
        for i in range(n):
            q=(i+1)%n; faces.append((j*n+i,j*n+q,(j+1)*n+q,(j+1)*n+i))
    faces += [tuple(range(n-1,-1,-1)),tuple((len(zs)-1)*n+i for i in range(n))]
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(verts,[],faces); me.materials.append(material)
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob)
    for f in me.polygons: f.use_smooth=True
    return ob

def cylinder(name, radius, depth, z, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=radius,depth=depth,location=(0,0,z))
    ob=bpy.context.object; ob.name=name; ob.data.materials.append(material); return ob

def cone(name, r1, r2, depth, z, material):
    bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=r1,radius2=r2,depth=depth,location=(0,0,z))
    ob=bpy.context.object; ob.name=name; ob.data.materials.append(material); return ob

def linear(owner, path):
    action=owner.animation_data.action
    curves=list(getattr(action,'fcurves',[]))
    for layer in getattr(action,'layers',[]):
        for strip in getattr(layer,'strips',[]):
            for bag in getattr(strip,'channelbags',[]): curves.extend(getattr(bag,'fcurves',[]))
    for fc in curves:
        if fc.data_path==path:
            for k in fc.keyframe_points: k.interpolation='LINEAR'

def visible(ob, first, last):
    ob.hide_render=True; ob.keyframe_insert('hide_render',frame=max(1,first-1))
    ob.hide_render=False; ob.keyframe_insert('hide_render',frame=first)
    ob.hide_render=False; ob.keyframe_insert('hide_render',frame=last)
    ob.hide_render=True; ob.keyframe_insert('hide_render',frame=last+1)

def shape_motion(ob, first, last, fun, name):
    base=ob.shape_key_add(name='basis',from_mix=False); key=ob.shape_key_add(name=name,from_mix=False)
    for i,v in enumerate(key.data): v.co=fun(base.data[i].co)
    key.value=0; key.keyframe_insert('value',frame=first); key.value=1; key.keyframe_insert('value',frame=last)
    linear(ob.data.shape_keys,'key_blocks["%s"].value'%name)

def extent(ob, dg):
    eo=ob.evaluated_get(dg); me=eo.to_mesh(); points=[eo.matrix_world@v.co for v in me.vertices]; eo.to_mesh_clear()
    return min(v.z for v in points),max(v.z for v in points),max(math.hypot(v.x,v.y) for v in points)

def scene_clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def main():
    a=args(); cfg=json.load(open(a.config)); os.makedirs(a.out,exist_ok=True)
    scene_clear()
    r=cfg['render']; t=cfg['timeline']; g=cfg['geometry']; p=cfg['presentation']
    pre,split,stop,neckstart=t['last_continuous_frame'],t['first_split_frame'],t['recoil_end_frame'],t['neck_start_frame']
    half,disp=g['overall_half_length'],g['axial_upper_displacement']; load=lambda z:z+disp*(z+half)/(2*half)
    silver=mat('polished grey-silver',p['silver'],.9,.23); dark=mat('graphite fixture',(.035,.045,.05),.76,.28); backdrop=mat('laboratory grey-green',p['background'],0,.78)
    sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE'; sc.render.resolution_x=r['width']; sc.render.resolution_y=r['height']; sc.render.resolution_percentage=100; sc.render.fps=r['fps']; sc.frame_start=1; sc.frame_end=r['frame_count']; sc.render.image_settings.file_format='PNG'; sc.world.color=(.025,.03,.038)
    # Jaws have a real mesh face at each specimen end; the conical housings stay outside.
    lower_jaw=cylinder('lower fixture jaw',.36,.26,-4.65,dark)
    upper_jaw=cylinder('upper fixture jaw',.36,.26,4.65,dark)
    lower_housing=cone('lower conical clamp',.84,.48,.42,-5.00,dark)
    upper_housing=cone('upper conical clamp',.48,.84,.42,5.00,dark)
    lower_grip=cylinder('lower grip housing',.62,.50,-5.42,dark)
    upper_grip=cylinder('upper grip housing',.62,.50,5.42,dark)
    upper=[upper_jaw,upper_housing,upper_grip]
    for ob in upper:
        ob.keyframe_insert('location',frame=1); ob.location.z+=disp; ob.keyframe_insert('location',frame=pre); linear(ob,'location')
    zs=[-half,-3.95,-3.63,-1.05,-.30,0,.30,1.05,3.63,3.95,half]
    plain=[g['grip_radius'],g['grip_radius'],g['gauge_radius'],g['gauge_radius'],g['gauge_radius'],g['gauge_radius'],g['gauge_radius'],g['gauge_radius'],g['gauge_radius'],g['grip_radius'],g['grip_radius']]
    neck=[g['grip_radius'],g['grip_radius'],g['gauge_radius'],g['gauge_radius'],.14,g['neck_radius'],.14,g['gauge_radius'],g['gauge_radius'],g['grip_radius'],g['grip_radius']]
    intact=profile('intact round bar',zs,plain,silver); visible(intact,1,pre)
    shape_motion(intact,1,pre,lambda v:Vector((v.x,v.y,load(v.z))),'shared axial loading')
    k=intact.shape_key_add(name='local ductile neck',from_mix=False)
    for j,rad in enumerate(neck):
        for i in range(64):
            q=2*math.pi*i/64; k.data[j*64+i].co=(rad*math.cos(q),rad*math.sin(q),zs[j])
    k.value=0; k.keyframe_insert('value',frame=1); k.keyframe_insert('value',frame=neckstart); k.value=1; k.keyframe_insert('value',frame=pre); linear(intact.data.shape_keys,'key_blocks["local ductile neck"].value')
    loz,hiz=zs[:6],zs[5:]; lor,hir=neck[:6],neck[5:]; gap0=g['initial_separation']
    lo_loaded=[load(z) for z in loz]; hi_loaded=[load(z) for z in hiz]; lo_loaded[-1]-=gap0/2; hi_loaded[0]+=gap0/2
    lo=profile('lower post-break component',lo_loaded,lor,silver); hi=profile('upper post-break component',hi_loaded,hir,silver)
    for ob in (lo,hi): visible(ob,split,r['frame_count'])
    lo0,lo1,hi0,hi1=load(-half),load(0)-gap0/2,load(0)+gap0/2,load(half); R=g['postbreak_local_recoil']
    shape_motion(lo,split,stop,lambda v:Vector((v.x,v.y,v.z-R*(v.z-lo0)/(lo1-lo0))),'anchored local recoil')
    shape_motion(hi,split,stop,lambda v:Vector((v.x,v.y,v.z+R*(hi1-v.z)/(hi1-hi0))),'anchored local recoil')
    bpy.ops.mesh.primitive_cube_add(location=(0,2.4,0)); wall=bpy.context.object; wall.name='backdrop'; wall.scale=(8,.3,7); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); wall.data.materials.append(backdrop)
    bpy.ops.object.camera_add(location=(2.8,-20,.15)); cam=bpy.context.object; sc.camera=cam; cam.data.type='ORTHO'; cam.data.ortho_scale=p['camera_ortho_scale']; cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
    def light(loc,energy,size):
        bpy.ops.object.light_add(type='AREA',location=loc); x=bpy.context.object; x.data.energy=energy; x.data.shape='DISK'; x.data.size=size; x.rotation_euler=(Vector((0,0,0))-x.location).to_track_quat('-Z','Y').to_euler()
    light((-4,-5,7),650,5); light((4,-1,-2),260,4); light((0,4,2),300,3)
    keyframes={'initial':1,'necked':120,'last_connected':pre,'first_separated':split,'end_state':r['frame_count']}
    for label,frame in keyframes.items(): sc.frame_set(frame); sc.render.filepath=os.path.join(a.out,'preview_%s.png'%label); bpy.ops.render.render(write_still=True)
    if a.preview_only:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(a.out,cfg['id']+'_preview.blend'))
        return
    frames=os.path.join(a.out,'frames'); os.makedirs(frames,exist_ok=True); sc.frame_set(1); sc.render.filepath=os.path.join(frames,'frame_'); bpy.ops.render.render(animation=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(a.out,cfg['id']+'.blend'))
    samples=[]; tol=1e-5
    for frame in range(1,r['frame_count']+1):
        sc.frame_set(frame); dg=bpy.context.evaluated_depsgraph_get(); lowfix=extent(lower_jaw,dg)[1]; highfix=extent(upper_jaw,dg)[0]
        if frame<=pre:
            z0,z1,rad=extent(intact,dg); rec={'component_count':1,'separation_gap':0.0,'maximum_radius':rad}
        else:
            a0,a1,ar=extent(lo,dg); b0,b1,br=extent(hi,dg); z0,z1=a0,b1; rec={'component_count':2,'separation_gap':b0-a1,'maximum_radius':max(ar,br)}
        rec.update({'frame':frame,'lower_fixture_mesh_end_z':lowfix,'upper_fixture_mesh_end_z':highfix,'lower_mesh_z':z0,'upper_mesh_z':z1,'lower_connection_error':abs(z0-lowfix),'upper_connection_error':abs(z1-highfix)}); samples.append(rec)
    post=[s for s in samples if s['frame']>=split]
    report={'schema':'metal-round-evaluated-mesh-validation/v1','configuration':cfg['id'],'method':'all 204 frames, evaluated render-time meshes; fixture endpoints measured from jaw meshes','checks':{'fixture_connection_tolerance':tol,'event_order_pass':samples[pre-1]['component_count']==1 and samples[split-1]['component_count']==2 and samples[split-1]['separation_gap']>0,'postbreak_nonpenetration_pass':all(s['separation_gap']>0 for s in post),'relative_geometry':{'gauge_radius':g['gauge_radius'],'neck_radius':g['neck_radius'],'units':'authored relative scene units; not millimetres'}},'samples':samples,'passes':all(s['lower_connection_error']<tol and s['upper_connection_error']<tol for s in samples) and samples[pre-1]['component_count']==1 and samples[split-1]['component_count']==2 and all(s['separation_gap']>0 for s in post)}
    with open(os.path.join(a.out,'evaluated_mesh_validation.json'),'w') as f: json.dump(report,f,indent=2)

if __name__=='__main__': main()
