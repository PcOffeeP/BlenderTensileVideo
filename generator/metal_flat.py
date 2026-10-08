"""Source-constrained qualitative flat metal limited deformation and rupture.

Blender -b --python generator/metal_flat.py -- --out _work/<task>/metal-flat \
    --reference <source-observations.json> [--render]

The source record is an explicit input, never imported from _work. Its structure
must be verified as flat_strip or flat_dogbone before a scene is generated.
The fixed geometric inputs are qualitative author units, not measured millimetres.
--render produces 600 PNGs; encoding and independent review belong to the caller.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

IMPLEMENTATION = 'metal-flat/1.2.0'
NAME = 'metal_flat_limited_deformation_rupture_baseline_v1'
FPS, END = 30, 600
HALF, WIDTH, THICKNESS = 2.8, .64, .11
NZ = 80  # number of axial intervals across the original whole material
MID = NZ // 2
# Rectangular perimeter with broad-face points and edge points, CCW in XY.
PERIMETER = [(-1,-1),(-.5,-1),(0,-1),(.5,-1),(1,-1),(1,0),
             (1,1),(.5,1),(0,1),(-.5,1),(-1,1),(-1,0)]
NP = len(PERIMETER)
S = np.linspace(-HALF, HALF, NZ + 1)


def smooth(value):
    value = max(0., min(1., value))
    return value * value * (3 - 2 * value)


def read_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--neck-local-stretch-amplitude', type=float, default=.18)
    parsed = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if not math.isfinite(parsed.neck_local_stretch_amplitude) or not 0 < parsed.neck_local_stretch_amplitude <= 2.5:
        parser.error('neck amplitude must be finite and 0 < amplitude <= 2.5; engineering guard, not approved range')
    out = Path(parsed.out).resolve()
    if '_work' not in out.parts:
        parser.error('candidate output must be inside an _work directory')
    reference = json.loads(Path(parsed.reference).read_text())
    required = ['source_id', 'source_path', 'source_sha256', 'structure', 'source_labels',
                'observations', 'unknowns', 'source_time_mapping', 'geometry_assumptions']
    missing = [key for key in required if key not in reference]
    if missing:
        parser.error('source record is missing: ' + ', '.join(missing))
    if reference['structure'] not in ['flat_strip', 'flat_dogbone']:
        parser.error('source structure must be verified flat_strip or flat_dogbone; do not infer it from material label')
    if not reference['observations'] or not reference['source_time_mapping']:
        parser.error('source observations and explicit retiming are required')
    source_path = Path(reference['source_path'])
    if not source_path.is_file():
        parser.error('source_path must point to the inspected source video')
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != reference['source_sha256']:
        parser.error('source SHA256 does not match the current file')
    out.mkdir(parents=True, exist_ok=True)
    return parsed, out, reference


def build(args, out, reference):
    # All quantities here are a discrete authored candidate. Source observations
    # constrain structure and behavior, but no dimensions or mechanics are fitted.
    event = 511
    crack_start = event - 10
    amplitude = args.neck_local_stretch_amplitude
    gap = .075
    width_exponent = .58
    config = {
        'implementation_version': IMPLEMENTATION,
        'scope': 'video_0058 flat dogbone limited deformation and terminal rupture qualitative extension; no verified progressive necking or calibrated constitutive law; one discrete point only',
        'duration_s': 20, 'fps': FPS, 'frames': END, 'resolution': [960,540],
        'geometry': {'units':'dimensionless author units', 'structure':reference['structure'],
            'original_length':2*HALF, 'gauge_width':WIDTH, 'thickness':THICKNESS,
            'embedded_width':WIDTH if reference['structure']=='flat_strip' else .94,
            'authored_gauge_material_s':[-2.15,2.15], 'formal_source_gauge':'unknown',
            'clamped_end_material_length':.30, 'axial_intervals':NZ,
            'rectangular_perimeter_vertices':NP, 'fracture_material_s':0.,
            'fracture_face':'matching slightly inclined flat-section faces; no invented cup-cone morphology'},
        'deformation': {'uniform_axial_stretch_amplitude':.02,
            'neck_local_stretch_amplitude':amplitude,'neck_material_sigma':.31,
            'width_stretch_exponent':width_exponent,'thickness_stretch_exponent':1-width_exponent,
            'formula':'lambda=1+0.02*u*free_mask+A*n*exp(-(s/0.31)^2)*free_mask; width=width0/lambda^0.58; thickness=thickness0/lambda^0.42; axial z integrates lambda ds',
            'volume_constraint':'width*thickness*lambda equals original section in the continuum material map; closed evaluated triangulated mesh volume independently checked at every frame',
            'opening':'last loading step combines progressive seam discontinuity and graded axial stretch within upper original material; no rigid-half translation, deleted slice or post-break recoil',
            'finite_seam_opening_author_units':gap,
            'extra_material_loading_after_crack_start':.008,
            'opening_measurement':'authored finite geometric separation; not a measured physical crack-opening displacement'},
        'timeline': {'loading_start_frame':1,'neck_onset_frame':241,
            'crack_start_frame':crack_start,'fracture_complete_frame':event,
            'fracture_complete_time_s':(event-1)/FPS,'stop_frame':event,
            'postfracture':'loading jaw and both original material halves hold all vertex positions through frame600'},
        'presentation': {'camera_position':[4,-24,2.1],'camera_target':[0,0,.25],
            'orthographic_scale':12.4,'fixed_camera':True,'renderer':'BLENDER_WORKBENCH',
            'antialias_samples':8, 'apparatus':'front/back contact jaws, connected caps and load rods leaving frame; no unsupported full machine architecture'},
        'presentation_simplifications':['source right-side extensometer omitted to expose specimen; original measurement-device obscuration is not simulated'],
        'parameter_range_accepted':False,
        'engineering_input_guard':{'neck_amplitude':{'minimum_exclusive':0,'maximum_inclusive':2.5},
            'interpretation':'input guard only; every changed discrete configuration needs fresh checks and visual review'},
    }
    def mapping(frame):
        u = smooth((min(frame, crack_start)-1)/(crack_start-1))
        n = smooth((min(frame, crack_start)-241)/(crack_start-241))
        q = max(0., min(1., (frame-crack_start)/(event-crack_start)))
        mask = np.clip((HALF-.30-np.abs(S))/.25,0,1)
        lam = 1+.02*u*mask+amplitude*n*np.exp(-(S/.31)**2)*mask
        # Additional final loading creates an actual displacement gradient in
        # upper material; transverse contraction is coupled to that derivative.
        lam += .008*q*np.where(S>=0,mask,0)
        z = np.zeros(NZ+1); z[0] = -HALF
        z[1:] = -HALF+np.cumsum((lam[:-1]+lam[1:])*.5*np.diff(S))
        base_width = np.full(NZ+1,WIDTH)
        if reference['structure']=='flat_dogbone':
            base_width += (.94-WIDTH)*np.array([smooth((abs(s)-2.15)/.35) for s in S])
        return z, base_width/lam**width_exponent, THICKNESS/lam**(1-width_exponent), q

    def coordinates(frame, side):
        z, widths, heights, q = mapping(frame)
        indices = range(MID+1) if side<0 else range(MID,NZ+1)
        points = []
        def point(j,px,py,scale=1.):
            x,y = px*widths[j]*scale/2, py*heights[j]*scale/2
            # Shallow complementary slant remains flat-specimen specific.
            face = .06*x*math.exp(-(float(S[j])/.20)**2)
            zz = float(z[j])+face
            if side>0:
                # Progressive front-to-rear release. At full release this
                # uniform seam jump is the only discontinuity; each upper
                # material interval also stretches, so no rigid-piece motion.
                threshold = .999*((py*scale+1)/2)**.25
                opening = max(0.,(q-threshold)/(1-threshold))
                fade = math.exp(-(float(S[j])/.23)**2)
                zz += gap*((1-fade)*q+fade*opening)
            return x,y,zz
        for j in indices:
            points.extend(point(j,*xy) for xy in PERIMETER)
        for scale in [.66,.33]:
            points.extend(point(MID,*xy,scale) for xy in PERIMETER)
        points.append(point(MID,0.,0.))
        return points

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end, scene.render.fps = 1, END, FPS
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x,scene.render.resolution_y = 960,540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.display.render_aa = '8'
    sh = scene.display.shading
    sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=False
    sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=True
    sh.background_type='WORLD';sh.studiolight_rotate_z=.35
    scene.world = bpy.data.worlds.new('uniform laboratory background')
    scene.world.color=(.27,.30,.33)
    scene.view_settings.view_transform='Standard'

    def material(name,color,metallic=1):
        result=bpy.data.materials.new(name);result.diffuse_color=(*color,1)
        result.metallic=metallic;result.roughness=.32
        return result
    specimen_mat=material('metal_flat_source_identity_not_color_inference',(.53,.56,.59))
    fracture_mat=material('fresh_fracture_face',(.30,.32,.34))
    grip_mat=material('grip_steel',(.13,.15,.18))
    cap_mat=material('connected_cap_steel',(.30,.33,.37))
    keyframes=sorted(set([1,END,event]+list(range(11,crack_start,10))+list(range(crack_start,event+1))))

    def half_faces(side):
        faces=[];fracture_faces=[]
        for j in range(MID):
            for a in range(NP):
                k=j*NP+a;kn=j*NP+(a+1)%NP
                faces.append((k,kn,kn+NP,k+NP))
        seam=MID*NP if side<0 else 0
        caps=[seam,(MID+1)*NP,(MID+2)*NP]
        for old,new in zip(caps[:-1],caps[1:]):
            for a in range(NP):
                face=(old+a,old+(a+1)%NP,new+(a+1)%NP,new+a)
                faces.append(face if side<0 else face[::-1]);fracture_faces.append(len(faces)-1)
        for a in range(NP):
            face=(caps[-1]+a,caps[-1]+(a+1)%NP,(MID+3)*NP)
            faces.append(face if side<0 else face[::-1]);fracture_faces.append(len(faces)-1)
        end=0 if side<0 else MID*NP
        faces.append(tuple(end+a for a in (range(NP-1,-1,-1) if side<0 else range(NP))))
        return faces,set(fracture_faces)

    def connected_cache(frame):
        # Construct an actual shared-index closed boundary mesh. Fully attached
        # cap facets are INTERNAL and removed on both halves; their positive
        # area is the remaining material connection cross-section. Only opened
        # cap facets become exposed external fracture surfaces. The shared
        # vertex indices are native topology, not a measurement-time weld.
        points=[];lookup={};half_ids=[];all_faces=[];face_materials=[]
        for side in [-1,1]:
            ids=[]
            for point in coordinates(frame,side):
                if point not in lookup:lookup[point]=len(points);points.append(point)
                ids.append(lookup[point])
            half_ids.append(ids)
            faces,cut=half_faces(side)
            for index,face in enumerate(faces):
                all_faces.append(tuple(ids[v] for v in face));face_materials.append(int(index in cut))
        by_vertices={};remove=set();ligament_area=0.
        for index,face in enumerate(all_faces):
            key=tuple(sorted(face))
            if key in by_vertices:
                other=by_vertices[key]
                remove.update([index,other])
                p0=Vector(points[face[0]])
                ligament_area+=sum((Vector(points[face[i]])-p0).cross(Vector(points[face[i+1]])-p0).length/2 for i in range(1,len(face)-1))
            else:by_vertices[key]=index
        retained=[face for index,face in enumerate(all_faces) if index not in remove]
        materials=[mat for index,mat in enumerate(face_materials) if index not in remove]
        # Interior interface points no longer lying on the boundary must not
        # remain as isolated evaluated vertices.
        used=sorted({v for face in retained for v in face});remap={v:i for i,v in enumerate(used)}
        boundary=[points[v] for v in used]
        retained=[tuple(remap[v] for v in face) for face in retained]
        ring_ids=[[remap[ids[j*NP+a]] for j in range(MID+1) for a in range(NP)] for ids in half_ids]
        mesh=bpy.data.meshes.new(f'native_material_boundary_{frame:04d}')
        mesh.from_pydata(boundary,[],retained);mesh.update()
        mesh.materials.append(specimen_mat);mesh.materials.append(fracture_mat)
        for polygon,mat in zip(mesh.polygons,materials):polygon.material_index=mat
        ob=bpy.data.objects.new(f'specimen_cache_{frame:04d}',mesh);scene.collection.objects.link(ob)
        ob['cache_frame']=frame;ob['remaining_shared_material_interface_area']=ligament_area
        ob['shared_interface_boundary_indices']=[remap[v] for v in set(half_ids[0]) & set(half_ids[1]) if v in remap]
        ob.hide_render=True;ob.hide_viewport=True
        for property_name in ['hide_render','hide_viewport']:
            ob.keyframe_insert(data_path=property_name,frame=1)
            setattr(ob,property_name,False);ob.keyframe_insert(data_path=property_name,frame=frame)
            if frame<event:
                setattr(ob,property_name,True);ob.keyframe_insert(data_path=property_name,frame=frame+1)
        return ob,ring_ids,ligament_area
    caches={frame:connected_cache(frame) for frame in range(1,event+1)}
    for frame in range(event+1,END+1):caches[frame]=caches[event]
    keyframes=list(range(1,END+1))
    config['saved_scene_animation']='self-contained native connected boundary cache meshes and constant visibility keys; ordinary apparatus keys; no external handler/script/cache required'
    config['native_interface']='internal matching cap facets removed from both sides; shared boundary vertex indices and finite-area remaining material cross-section before511; complete separation at511'

    def box(name,size,loc,mat,parent=None):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        ob=bpy.context.object;ob.name=name;ob.dimensions=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        ob.data.materials.append(mat)
        # Contact surfaces are planar exact faces; bevel only alters external edges.
        bevel=ob.modifiers.new('small external edge bevel','BEVEL');bevel.width=.012;bevel.segments=2
        ob.modifiers.new('weighted normals','WEIGHTED_NORMAL')
        if parent:ob.parent=parent
        return ob
    apparatus={}
    for side,label in [(-1,'lower'),(1,'upper')]:
        root=bpy.data.objects.new(label+'_grip_root',None);scene.collection.objects.link(root)
        end=side*HALF;center=end-side*.13
        jaws=[box(label+'_'+name+'_contact_jaw',(1.42,.36,.38),(0,sign*(THICKNESS/2+.18),center),grip_mat,root)
              for sign,name in [(-1,'front'),(1,'back')]]
        cap=box(label+'_connected_cap',(1.42,.90,.16),(0,0,end+side*.08),cap_mat,root)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.14,depth=2.,location=(0,0,end+side*1.16))
        rod=bpy.context.object;rod.name=label+'_load_rod';rod.data.materials.append(cap_mat);rod.parent=root
        for x in [-.52,.52]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.07,depth=.05,location=(x,-.46,center),rotation=(math.pi/2,0,0))
            bolt=bpy.context.object;bolt.name=label+'_clamp_bolt';bolt.data.materials.append(cap_mat);bolt.parent=root
        apparatus[label]={'root':root,'jaws':jaws,'cap':cap,'rod':rod}
    for frame in keyframes:
        z,w,h,q=mapping(frame)
        apparatus['upper']['root'].location.z=float(z[-1]-HALF)+gap*q
        apparatus['upper']['root'].keyframe_insert(data_path='location',frame=frame)
    bpy.ops.object.camera_add(location=config['presentation']['camera_position'])
    camera=bpy.context.object;camera.name='fixed_camera'
    camera.rotation_euler=(Vector(config['presentation']['camera_target'])-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=config['presentation']['orthographic_scale'];scene.camera=camera

    def fcurves(action):
        if hasattr(action,'fcurves'):return list(action.fcurves)
        return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
    for owner in bpy.data.objects:
        if owner.animation_data and owner.animation_data.action:
            for curve in fcurves(owner.animation_data.action):
                for key in curve.keyframe_points:key.interpolation='CONSTANT' if curve.data_path in ['hide_render','hide_viewport'] else 'LINEAR'
    scene['implementation_version']=IMPLEMENTATION
    scene['fracture_complete_frame']=event

    def evaluated(ob):
        eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=eo.to_mesh();mesh.calc_loop_triangles()
        points=[eo.matrix_world@v.co for v in mesh.vertices]
        triangles=[tuple(tri.vertices) for tri in mesh.loop_triangles]
        edges=[tuple(edge.vertices) for edge in mesh.edges]
        eo.to_mesh_clear();return points,triangles,edges
    def bounds(points):
        return [[min(p[a] for p in points),max(p[a] for p in points)] for a in range(3)]
    def connected_groups(parts):
        parents=[];offset=0
        def find(value):
            while parents[value]!=value:parents[value]=parents[parents[value]];value=parents[value]
            return value
        def union(a,b):
            a,b=find(a),find(b)
            if a!=b:parents[b]=a
        for points,triangles,edges in parts:
            for point in points:
                index=len(parents);parents.append(index)
            for a,b in edges:union(offset+a,offset+b)
            offset+=len(points)
        groups={}
        for index in range(len(parents)):groups.setdefault(find(index),[]).append(index)
        return list(groups.values())
    def volume(points,triangles):
        return abs(sum(points[a].dot(points[b].cross(points[c]))/6 for a,b,c in triangles))
    def section(ring):
        return abs(sum(a.x*b.y-b.x*a.y for a,b in zip(ring,ring[1:]+ring[:1])))/2
    def native_topology(ob,points):
        eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=eo.to_mesh()
        incidence={};face_keys=set();duplicates=0
        for polygon in mesh.polygons:
            ids=list(polygon.vertices);key=tuple(sorted(ids))
            if key in face_keys:duplicates+=1
            face_keys.add(key)
            for a,b in zip(ids,ids[1:]+ids[:1]):
                edge=tuple(sorted((a,b)));incidence[edge]=incidence.get(edge,0)+1
        # Boundary indices common to both ORIGINAL material domains are native
        # shared indices. Projecting their actual evaluated positions measures
        # the finite cross-section, without welding two coincident coordinates.
        pairs=sorted({(float(points[i].x),float(points[i].y)) for i in ob['shared_interface_boundary_indices']})
        def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
        hull=[]
        if len(pairs)>2:
            lo=[];hi=[]
            for pair in pairs:
                while len(lo)>1 and cross(lo[-2],lo[-1],pair)<=0:lo.pop()
                lo.append(pair)
            for pair in reversed(pairs):
                while len(hi)>1 and cross(hi[-2],hi[-1],pair)<=0:hi.pop()
                hi.append(pair)
            hull=lo[:-1]+hi[:-1]
        area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(hull,hull[1:]+hull[:1])))/2 if hull else 0.
        result={'non_two_incident_edges':sum(v!=2 for v in incidence.values()),
            'duplicate_native_faces':duplicates,'measured_shared_boundary_projected_area':area,
            'native_shared_boundary_vertex_count':len(pairs)}
        eo.to_mesh_clear();return result
    records=[];post_reference=None;max_post_vertex=0.;max_post_machine=0.;first_two=None
    last_loading_start=None;last_loading_end=None
    for frame in range(1,END+1):
        scene.frame_set(frame);cache,ring_ids,ligament_area=caches[frame];parts=[evaluated(cache)]
        points=[point for part in parts for point in part[0]]
        topology=native_topology(cache,points)
        groups=connected_groups(parts)
        if len(groups)==2 and first_two is None:first_two=frame
        rings=[[ [points[ids[j*NP+a]] for a in range(NP)] for j in range(MID+1)] for ids in ring_ids]
        centers=[[sum(ring,Vector())/NP for ring in half] for half in rings]
        lengths=[sum((b-a).length for a,b in zip(half,half[1:])) for half in centers]
        axial_steps=[b.z-a.z for half in centers for a,b in zip(half,half[1:])]
        sections=[section(ring) for half in rings for ring in half]
        seam_lo,seam_hi=rings[0][-1],rings[1][0]
        gaps=[b.z-a.z for a,b in zip(seam_lo,seam_hi)]
        joint_checks=[];machine_points=[];projected=[world_to_camera_view(scene,camera,p) for p in points]
        for label,ring in [('lower',rings[0][0]),('upper',rings[1][-1])]:
            app=apparatus[label]
            jaw_bounds=[bounds(evaluated(jaw)[0]) for jaw in app['jaws']]
            cap_points=evaluated(app['cap'])[0];rod_points=evaluated(app['rod'])[0]
            cap_bounds,rod_bounds=bounds(cap_points),bounds(rod_points)
            endpoint=sum(ring,Vector())/NP;front,back=jaw_bounds
            contact=max(abs(front[1][1]-min(p.y for p in ring)),abs(back[1][0]-max(p.y for p in ring)))
            lower_end=label=='lower'
            jaw_cap=(front[2][0]-cap_bounds[2][1]) if lower_end else (cap_bounds[2][0]-front[2][1])
            cap_rod=(cap_bounds[2][0]-rod_bounds[2][1]) if lower_end else (rod_bounds[2][0]-cap_bounds[2][1])
            cap_clear=endpoint.z-cap_bounds[2][1] if lower_end else cap_bounds[2][0]-endpoint.z
            joint_checks.append({'end':label,'measured_front_back_contact_gap':contact,
                'end_vertices_inside_jaw_z':all(front[2][0]<=p.z<=front[2][1] for p in ring),
                'jaw_cap_axial_gap':jaw_cap,'cap_rod_axial_gap':cap_rod,
                'cap_material_end_axial_clearance':cap_clear})
            for ob in app['jaws']+[app['cap']]:
                actual=evaluated(ob)[0];machine_points+=actual
                projected.extend(world_to_camera_view(scene,camera,p) for p in actual)
            machine_points+=rod_points
        measured_volume=sum(volume(v,t) for v,t,e in parts)
        record={'frame':frame,'time_s':(frame-1)/FPS,'measured_components':len(groups),
            'measured_closed_volume':measured_volume,'same_original_material_half_lengths':lengths,
            'same_original_material_total_length_excluding_seam_gap':sum(lengths),
            'minimum_same_material_axial_station_step':min(axial_steps),
            'actual_vertex_counts':[len(part[0]) for part in parts],
            'remaining_shared_material_interface_area':ligament_area,
            'native_topology':topology,
            'minimum_section_area':min(sections),'central_width':max(p.x for p in seam_lo)-min(p.x for p in seam_lo),
            'central_thickness':max(p.y for p in seam_lo)-min(p.y for p in seam_lo),
            'minimum_corresponding_seam_gap':min(gaps),'maximum_corresponding_seam_gap':max(gaps),
            'jaw_joint_checks':joint_checks,
            'all_specimen_jaws_caps_inside_frame':all(0<=p.x<=1 and 0<=p.y<=1 for p in projected)}
        records.append(record)
        if frame==crack_start:last_loading_start=[p.copy() for ring in rings[1] for p in ring]
        if frame==event:last_loading_end=[p.copy() for ring in rings[1] for p in ring]
        if frame>=event:
            if post_reference is None:post_reference=(points,machine_points)
            max_post_vertex=max(max_post_vertex,max((a-b).length for a,b in zip(points,post_reference[0])))
            max_post_machine=max(max_post_machine,max((a-b).length for a,b in zip(machine_points,post_reference[1])))
    initial=records[0]['measured_closed_volume']
    for r in records:r['volume_ratio_to_initial']=r['measured_closed_volume']/initial
    upper_displacements=[b.z-a.z for a,b in zip(last_loading_start,last_loading_end)]
    summary={'actual_evaluated_frames':len(records),'first_measured_separation_frame':first_two,
        'expected_separation_frame':event,'event_agrees':first_two==event,
        'max_postfracture_vertex_displacement':max_post_vertex,'max_postfracture_apparatus_displacement':max_post_machine,
        'volume_ratio_range':[min(r['volume_ratio_to_initial'] for r in records),max(r['volume_ratio_to_initial'] for r in records)],
        'min_measured_seam_gap':min(r['minimum_corresponding_seam_gap'] for r in records),
        'max_measured_grip_contact_gap':max(j['measured_front_back_contact_gap'] for r in records for j in r['jaw_joint_checks']),
        'max_measured_machine_joint_positive_gap':max(max(0,j[k]) for r in records for j in r['jaw_joint_checks'] for k in ['jaw_cap_axial_gap','cap_rod_axial_gap']),
        'min_measured_cap_material_end_clearance':min(j['cap_material_end_axial_clearance'] for r in records for j in r['jaw_joint_checks']),
        'min_measured_same_material_axial_station_step':min(r['minimum_same_material_axial_station_step'] for r in records),
        'same_original_material_axial_intervals':NZ,
        'material_boundary_topology_changes':'original material rings preserved; interior interface vertices/faces removed while attached, only boundary topology changes',
        'finite_ligament_area_at_frame510':records[509]['remaining_shared_material_interface_area'],
        'measured_native_shared_boundary_area_at_frame510':records[509]['native_topology']['measured_shared_boundary_projected_area'],
        'native_edge_incidence_all_two':all(r['native_topology']['non_two_incident_edges']==0 for r in records),
        'no_duplicate_native_internal_cap_faces':all(r['native_topology']['duplicate_native_faces']==0 for r in records),
        'upper_final_loading_actual_axial_displacement_range':[min(upper_displacements),max(upper_displacements)],
        'upper_final_loading_displacement_is_nonuniform':max(upper_displacements)-min(upper_displacements)>1e-4,
        'all_material_endpoints_inside_jaws':all(j['end_vertices_inside_jaw_z'] for r in records for j in r['jaw_joint_checks']),
        'all_specimen_jaws_caps_inside_frame':all(r['all_specimen_jaws_caps_inside_frame'] for r in records),
        'continuity_measurement':'actual native evaluated edge graph and face-edge incidence; no coordinate welding in measurement',
        'penetration_scope':'corresponding matching cut vertices and same-material axial station order; intended jaw contact checked; no general full-triangle self-intersection solver'}
    checks={'configuration':config,'summary':summary,'actual_evaluated_frames':records}
    (out/'mesh_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
    (out/'configuration.json').write_text(json.dumps(config,ensure_ascii=False,indent=2))
    source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    labels={'材料类别':'金属','断裂结果':'完全断裂','单一主要破坏类别':'韧性断裂','断裂位置':'标距内','夹持异常':'无','拍摄异常':'无'}
    metadata={'schema':'tensile-video-candidate/v1','video_id':NAME,'style':'metal_flat_limited_deformation_rupture',
        'implementation_version':IMPLEMENTATION,'generator_path':'generator/metal_flat.py','generator_sha256':source_hash,
        'configuration':config,'source':reference,'source_observations':reference['observations'],
        'assumptions':reference['geometry_assumptions']+[
            'Three-dimensional thickness and split transverse contraction are authored; cannot be fitted from one projected source view.',
            'Lower clamp fixed; upper clamp loading ends at completed rupture. Source postrupture motion is recorded separately, not reinterpreted as stationary.',
            'Time remapping extends or compresses phases to20s; not a calibrated strain-rate experiment.',
            'Flat-section matching slanted faces illustrate separation, not microscopic fracture morphology.'],
        'unknowns':reference['unknowns']+['formal source gauge length','absolute dimensions','constitutive parameters','plastic/elastic strain split','microfracture morphology'],
        'time_mapping':reference['source_time_mapping'],'expected_labels':labels,
        'checked_labels':{'材料类别':'金属','断裂结果':'完全断裂','单一主要破坏类别':'无法确认',
            '断裂位置':'标距内','夹持异常':'无','拍摄异常':'无'},
        'label_check_scope':'material identity from source table; terminal complete rupture, site, grips and camera are authored candidate properties subject to final-video and independent review; source ductile label is not verified progressive necking',
        'technical_checks':summary,'technical_check_limits':summary['penetration_scope'],
        'acceptance':{'user_accepted':False,'style_accepted':False,'parameter_range_accepted':False,
            'training_released':False,'scope':'single discrete qualitative candidate pending review'},
        'video':{'path':NAME+'.mp4','sha256':None,'encoding_verified':False,'frames':END,'fps':FPS,'duration_s':20},
        'independent_review':'pending','main_final_video_view_completed':False}
    (out/(NAME+'.json')).write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/(NAME+'.blend')))
    for frame in [1,241,421,crack_start,event-2,event,END]:
        scene.frame_set(frame);scene.render.filepath=str(out/f'key_{frame:04d}.png');bpy.ops.render.render(write_still=True)
    if args.render:
        directory=out/'frames';directory.mkdir(exist_ok=True)
        for frame in range(1,END+1):
            scene.frame_set(frame);scene.render.filepath=str(directory/f'{frame:06d}.png');bpy.ops.render.render(write_still=True)
    print('METAL_FLAT_BUILD_COMPLETE',json.dumps(summary),str(out),flush=True)


if __name__=='__main__':
    build(*read_arguments())
