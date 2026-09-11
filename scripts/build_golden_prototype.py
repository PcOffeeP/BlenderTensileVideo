#!/usr/bin/env python3
"""Build the deterministic v0.2 flat-dogbone tensile Golden Prototype.

Run from the repository root:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python \
    scripts/build_golden_prototype.py -- --stage scene
  /Applications/Blender.app/Contents/MacOS/Blender --background --python \
    scripts/build_golden_prototype.py -- --stage keyframes
  /Applications/Blender.app/Contents/MacOS/Blender --background --python \
    scripts/build_golden_prototype.py -- --stage final

The animated specimen is an explicit mesh sequence, rather than a physics
simulation.  This makes frame 211's first separation deterministic.
"""
import bpy
import hashlib
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "synthetic_0001.json"
PREVIEW_DIR = ROOT / "artifacts" / "previews"
SCENE_DIR = ROOT / "artifacts" / "scenes"
OUTPUT_DIR = ROOT / "outputs"


def arg_value(name, default):
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return args[args.index(name) + 1] if name in args else default


STAGE = arg_value("--stage", "keyframes")
with CONFIG_PATH.open(encoding="utf-8") as f:
    CFG = json.load(f)
FPS = CFG["fps"]
FRACTURE_FRAME = CFG["implementation"]["fracture_frame"]
LAST_CONTINUOUS_FRAME = CFG["implementation"]["last_continuous_frame"]
SHOULDER_RADIUS = 0.80
# Two tangent-continuous R=0.8 W circular arcs move each side from W/2 to
# 1.8W/2. The resulting shoulder span is derived, never fitted visually.
SHOULDER_ANGLE = math.acos(0.75)
SHOULDER_TOP_Z = 2.0 + 2.0 * SHOULDER_RADIUS * math.sin(SHOULDER_ANGLE)
GRIP_OUTER_Z = SHOULDER_TOP_Z + 1.50


def t_for_frame(frame):
    return (frame - 1) / FPS


def deformation_at(t):
    """Return total upper displacement and neck intensity for the pre-break body."""
    if t <= 1.0:
        return 0.0, 0.0
    if t <= 5.0:
        return 0.60 * (t - 1.0) / 4.0, 0.0
    # At 7s, the gauge grew 0.95 W and its centre narrowed to 38% of W.
    q = min(1.0, (t - 5.0) / 2.0)
    return 0.60 + 0.35 * q, 0.62 * q


def upper_displacement_at(t):
    if t < 7.0:
        return deformation_at(t)[0]
    # Continue the pre-break crosshead motion without a jump. The rapid motion
    # after fracture comes from local elastic unloading, not a fixture jump.
    return 0.95 + 0.09 * min(1.0, (t - 7.0) / 3.0)


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


# Frame 211 (7.0 s) is already visibly open. During the next three frames,
# each free end unloads 0.14 W toward its own grip. The local displacement
# decays to zero at the shoulder/grip boundary, keeping every clamped end
# anchored and avoiding a long, polymer-like rebound.
FRACTURE_HALF_GAP_W = 0.10
FREE_END_RECOIL_W = 0.14
RECOIL_DURATION_S = 3.0 / FPS


def recoil_at(t):
    if t <= 7.0:
        return 0.0
    p = min(1.0, (t - 7.0) / RECOIL_DURATION_S)
    # Front-loaded release: 56% after one frame, 89% after two, complete at 3.
    return FREE_END_RECOIL_W * (1.0 - (1.0 - p) ** 2)


def gauge_width(z, centre, neck):
    # Gaussian-localised constriction at the mid-gauge: visibly ductile, while
    # both shoulder transitions remain broad and identifiable.
    return 0.5 * (1.0 - neck * math.exp(-((z - centre) / 0.56) ** 2))


def profile_points(t, half=None):
    """Return a CCW x/z outline. half=None is a continuous dogbone."""
    stretch, neck = deformation_at(min(t, 7.0))
    # A real G1 biarc: two R=0.8 W circular arcs connect the parallel grip
    # and gauge sides without a cusp. Both x and z are monotonic along the
    # shoulder, and the tangent is vertical at both frozen-width endpoints.
    shoulder_gauge_to_grip = []
    for i in range(17):
        angle_path = (2.0 * SHOULDER_ANGLE) * i / 16.0
        if angle_path <= SHOULDER_ANGLE:
            z = 2.0 + SHOULDER_RADIUS * math.sin(angle_path)
            half_width = 0.50 + SHOULDER_RADIUS * (1.0 - math.cos(angle_path))
        else:
            u = angle_path - SHOULDER_ANGLE
            z = 2.0 + SHOULDER_RADIUS * math.sin(SHOULDER_ANGLE) + SHOULDER_RADIUS * (math.sin(SHOULDER_ANGLE) - math.sin(SHOULDER_ANGLE - u))
            half_width = 0.50 + SHOULDER_RADIUS * (1.0 - math.cos(SHOULDER_ANGLE)) + SHOULDER_RADIUS * (math.cos(SHOULDER_ANGLE - u) - math.cos(SHOULDER_ANGLE))
        shoulder_gauge_to_grip.append((z, half_width))
    shoulder_high_to_low = list(reversed(shoulder_gauge_to_grip))
    # Physical profile locations in the undeformed local specimen reference.
    lower = [(-GRIP_OUTER_Z, 0.90), (-SHOULDER_TOP_Z, 0.90)]
    lower += [(-z, x) for z, x in shoulder_high_to_low[1:]]
    gauge_ref = [-2.00, -1.60, -1.20, -0.80, -0.40, 0.0, 0.40, 0.80, 1.20, 1.60, 2.00]
    lower += [(z, 0.50) for z in gauge_ref[1:]]
    upper = shoulder_gauge_to_grip[1:]
    upper += [(GRIP_OUTER_Z, 0.90)]

    def mapped(z):
        if z <= -2.0:
            return z
        if z >= 2.0:
            return z + stretch
        return z + stretch * (z + 2.0) / 4.0

    def deformed_width(z, base_width):
        return gauge_width(mapped(z), 0.5 * stretch, neck) if abs(z) <= 2.0 else base_width

    full = lower + upper

    if half == "lower":
        refs = [item for item in full if item[0] <= 0.0]
        def lower_unload(z):
            return -recoil_at(t) * max(0.0, min(1.0, (z + 2.0) / 2.0))
        left = [(-deformed_width(z, x), mapped(z) + lower_unload(z)) for z, x in refs]
        centre = 0.5 * stretch
        end_width = gauge_width(centre, centre, neck)
        cut_z = centre - FRACTURE_HALF_GAP_W - recoil_at(t)
        left[-1] = (-end_width, cut_z - 0.015)
        right = [(deformed_width(z, x), mapped(z) + lower_unload(z)) for z, x in reversed(refs)]
        right[0] = (end_width, cut_z + 0.015)
        return left + right
    if half == "upper":
        refs = [item for item in full if item[0] >= 0.0]
        delta = upper_displacement_at(t) - stretch
        def upper_unload(z):
            return recoil_at(t) * max(0.0, min(1.0, (2.0 - z) / 2.0))
        left = [(-deformed_width(z, x), mapped(z) + delta + upper_unload(z)) for z, x in refs]
        centre = 0.5 * stretch
        start_width = gauge_width(centre, centre, neck)
        cut_z = centre + delta + FRACTURE_HALF_GAP_W + recoil_at(t)
        left[0] = (-start_width, cut_z + 0.015)
        right = [(deformed_width(z, x), mapped(z) + delta + upper_unload(z)) for z, x in reversed(refs)]
        right[-1] = (start_width, cut_z - 0.015)
        return left + right

    left = [(-deformed_width(z, x), mapped(z)) for z, x in full]
    right = [(deformed_width(z, x), mapped(z)) for z, x in reversed(full)]
    return left + right


def mesh_from_profile(name, outline, material):
    thickness = 0.15
    n = len(outline)
    verts = [(x, -thickness / 2, z) for x, z in outline] + [(x, thickness / 2, z) for x, z in outline]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bevel = obj.modifiers.new("EdgeSoftening", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 2
    return obj


def make_materials():
    def material(name, color, metallic=0.0, roughness=0.5):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = next((n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
        if bsdf is None:  # Blender 5.x may start with an empty material tree.
            bsdf = m.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
            out = next((n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeOutputMaterial"), None)
            if out is None:
                out = m.node_tree.nodes.new("ShaderNodeOutputMaterial")
            m.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        return m
    return {
        "specimen": material("neutral_brushed_metal_v1", (0.45, 0.45, 0.45), 0.8, 0.5),
        "grip": material("machine_dark_metal", (0.12, 0.14, 0.16), 0.75, 0.42),
        "jaw": material("jaw_steel", (0.27, 0.29, 0.31), 0.75, 0.36),
        "backdrop": material("neutral_gray_backdrop", (0.26, 0.26, 0.26), 0.0, 0.8),
    }


def cube(name, loc, scale, material, parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    bevel = obj.modifiers.new("MachinedEdges", "BEVEL")
    bevel.width = 0.06
    bevel.segments = 3
    return obj


def setup_camera_and_lights(mats):
    bpy.context.scene.world.color = (0.14, 0.14, 0.14)
    camera_data = bpy.data.cameras.new("Camera_Front_Fixed")
    camera_data.type = "ORTHO"
    # A 23.25 W width gives a 13.068 W vertical field and keeps the complete
    # post-fracture apparatus within the frozen 75--85% height envelope.
    camera_data.ortho_scale = 23.25
    camera = bpy.data.objects.new("Camera_Front_Fixed", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (0, -20, 0.70)
    camera.rotation_euler = (math.radians(90), 0, 0)
    # Point the optical axis exactly toward the specimen centre.
    camera.rotation_euler = ((Vector((0, 0, 0.70)) - camera.location).to_track_quat('-Z', 'Y')).to_euler()
    bpy.context.scene.camera = camera

    # Vertical matte card is deliberately over-wide, so its untextured edges
    # cannot appear within the fixed camera view.
    cube("Neutral_Background", (0, 1.0, 0.7), (20.0, 0.08, 10.0), mats["backdrop"])
    # Use an emission-only card for an even neutral gray field: this prevents
    # a lighting gradient or cast shadow from becoming a visual shortcut.
    bg_nodes = mats["backdrop"].node_tree.nodes
    bg_links = mats["backdrop"].node_tree.links
    bg_nodes.clear()
    bg_emission = bg_nodes.new("ShaderNodeEmission")
    bg_emission.inputs["Color"].default_value = (0.19, 0.19, 0.19, 1.0)
    bg_emission.inputs["Strength"].default_value = 0.32
    bg_output = bg_nodes.new("ShaderNodeOutputMaterial")
    bg_links.new(bg_emission.outputs["Emission"], bg_output.inputs["Surface"])
    for name, loc, energy, size in [
        ("Key_Softbox", (-4.2, -5.0, 5.5), 200.0, 5.0),
        ("Fill_Softbox", (4.0, -3.0, 1.0), 150.0, 5.0),
        ("Front_Softbox", (0.0, -6.0, 0.7), 120.0, 8.0),
        ("Rim_Softbox", (0.0, 1.5, 4.5), 55.0, 3.0),
    ]:
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(light)
        light.location = loc
        light.rotation_euler = ((Vector((0, 0, 0.6)) - light.location).to_track_quat('-Z', 'Y')).to_euler()


def setup_machine(mats):
    upper = bpy.data.objects.new("Grip_Upper", None)
    lower = bpy.data.objects.new("Grip_Lower", None)
    bpy.context.collection.objects.link(upper)
    bpy.context.collection.objects.link(lower)
    # Local crossheads are intentionally partial, preserving the specimen evidence.
    crosshead_z = GRIP_OUTER_Z + 0.18
    jaw_z = SHOULDER_TOP_Z + 0.78
    cube("Crosshead_Upper_Partial", (0, 0, crosshead_z), (2.8, 0.52, 0.26), mats["grip"], upper)
    cube("Crosshead_Lower_Partial", (0, 0, -crosshead_z), (2.8, 0.52, 0.26), mats["grip"], lower)
    # Pair of jaws at each end: the central opening exposes the whole shoulder.
    for sign in (-1, 1):
        cube("Upper_Jaw_" + str(sign), (1.18 * sign, 0, jaw_z), (0.35, 0.42, 0.62), mats["jaw"], upper)
        cube("Lower_Jaw_" + str(sign), (1.18 * sign, 0, -jaw_z), (0.35, 0.42, 0.62), mats["jaw"], lower)
    # Only the upper group is animated. The lower fixture remains at Z=0.
    for frame in range(1, 301):
        upper.location.z = upper_displacement_at(t_for_frame(frame))
        upper.keyframe_insert("location", frame=frame)
    return upper, lower


def visible_only(obj, frame):
    obj.hide_render = True
    obj.keyframe_insert("hide_render", frame=1)
    obj.hide_render = False
    obj.keyframe_insert("hide_render", frame=frame)
    obj.hide_render = True
    obj.keyframe_insert("hide_render", frame=frame + 1)


def build_specimen_sequence(mats):
    objects = []
    for frame in range(1, LAST_CONTINUOUS_FRAME + 1):
        obj = mesh_from_profile("Specimen_Continuous_%03d" % frame, profile_points(t_for_frame(frame)), mats["specimen"])
        visible_only(obj, frame)
        objects.append(obj)
    for frame in range(FRACTURE_FRAME, 301):
        t = t_for_frame(frame)
        lower = mesh_from_profile("Specimen_Lower_%03d" % frame, profile_points(t, "lower"), mats["specimen"])
        upper = mesh_from_profile("Specimen_Upper_%03d" % frame, profile_points(t, "upper"), mats["specimen"])
        visible_only(lower, frame)
        visible_only(upper, frame)
        objects.extend((lower, upper))
    return objects


def set_render_settings(final=False):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = CFG["resolution_x"]
    scene.render.resolution_y = CFG["resolution_y"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = 300
    scene.render.image_settings.color_mode = "RGB"
    scene.render.resolution_percentage = 100
    if final:
        # Blender 5.2 routes video selection through ImageFormatSettings.media_type;
        # file_format itself now contains image-only codecs.
        scene.render.image_settings.media_type = "VIDEO"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
        scene.render.ffmpeg.ffmpeg_preset = "REALTIME"
        scene.render.filepath = str(OUTPUT_DIR / (CFG["video_id"] + ".mp4"))


def scene_hash(objects):
    data = []
    for obj in sorted(objects, key=lambda o: o.name):
        verts = [(round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6)) for v in obj.data.vertices]
        data.append((obj.name, verts))
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    (SCENE_DIR / "synthetic_0001_geometry.sha256").write_text(digest + "\n", encoding="utf-8")
    return digest


def write_geometry_evidence(objects, digest):
    indexed = {obj.name: obj for obj in objects}
    samples = {}
    for name in ("Specimen_Continuous_001", "Specimen_Continuous_210", "Specimen_Lower_211", "Specimen_Upper_211"):
        obj = indexed[name]
        coords = [tuple(round(v, 6) for v in vert.co) for vert in obj.data.vertices]
        samples[name] = {
            "vertices": len(obj.data.vertices),
            "edges": len(obj.data.edges),
            "polygons": len(obj.data.polygons),
            "local_bbox": {
                "x": [min(v[0] for v in coords), max(v[0] for v in coords)],
                "y": [min(v[1] for v in coords), max(v[1] for v in coords)],
                "z": [min(v[2] for v in coords), max(v[2] for v in coords)],
            },
        }
    camera = bpy.context.scene.camera
    vertical_field = camera.data.ortho_scale / (CFG["resolution_x"] / CFG["resolution_y"])
    crosshead_extent = GRIP_OUTER_Z + 0.18 + 0.26
    upper_final = crosshead_extent + upper_displacement_at(t_for_frame(300))
    total_height = upper_final - (-crosshead_extent)
    def break_state(frame):
        t = t_for_frame(frame)
        stretch, _ = deformation_at(min(t, 7.0))
        fixture_delta = upper_displacement_at(t) - stretch
        recoil = recoil_at(t) if frame >= FRACTURE_FRAME else 0.0
        return {
            "frame": frame,
            "time_s": round(t, 6),
            "connected_components": 1 if frame <= LAST_CONTINUOUS_FRAME else 2,
            "fixture_delta_w": round(fixture_delta, 6),
            "free_end_recoil_w_each": round(recoil, 6),
            "lower_free_end_z_w": round(0.5 * stretch - FRACTURE_HALF_GAP_W - recoil, 6) if frame >= FRACTURE_FRAME else None,
            "upper_free_end_z_w": round(0.5 * stretch + fixture_delta + FRACTURE_HALF_GAP_W + recoil, 6) if frame >= FRACTURE_FRAME else None,
            # Each deliberately irregular cut edge intrudes 0.015 W toward the
            # gap, so this records the closest rendered silhouette distance.
            "minimum_central_gap_w": round(fixture_delta + 2.0 * FRACTURE_HALF_GAP_W + 2.0 * recoil - 0.03, 6) if frame >= FRACTURE_FRAME else 0.0,
            "grip_anchor_recoil_w": 0.0,
            "lower_shoulder_anchor_z_w": -2.0,
            "upper_shoulder_anchor_z_w": round(2.0 + upper_displacement_at(t), 6),
            "anchors_match_grip_motion": True,
        }

    evidence = {
        "config_sha256": hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest(),
        "geometry_sha256": digest,
        "topology": samples,
        "camera": {
            "type": camera.data.type,
            "location": [round(v, 6) for v in camera.location],
            "ortho_scale_width_w": camera.data.ortho_scale,
            "vertical_field_w": round(vertical_field, 6),
        },
        "grip_upper_transforms": {
            "frame_001": [0.0, 0.0, round(upper_displacement_at(t_for_frame(1)), 6)],
            "frame_210": [0.0, 0.0, round(upper_displacement_at(t_for_frame(210)), 6)],
            "frame_211": [0.0, 0.0, round(upper_displacement_at(t_for_frame(211)), 6)],
            "frame_300": [0.0, 0.0, round(upper_displacement_at(t_for_frame(300)), 6)],
        },
        "grip_lower_transforms": {
            "frame_001": [0.0, 0.0, 0.0],
            "frame_210": [0.0, 0.0, 0.0],
            "frame_211": [0.0, 0.0, 0.0],
            "frame_300": [0.0, 0.0, 0.0],
        },
        "projection_checks": {
            "initial_apparatus_height_w": round(2.0 * crosshead_extent, 6),
            "initial_apparatus_height_percent": round(100 * 2.0 * crosshead_extent / vertical_field, 3),
            "gauge_height_w": 4.0,
            "initial_gauge_height_percent": round(100 * 4.0 / vertical_field, 3),
            "final_apparatus_height_w": round(total_height, 6),
            "final_apparatus_height_percent": round(100 * total_height / vertical_field, 3),
            "required_apparatus_percent_range": [75.0, 85.0],
            "required_gauge_percent_range": [30.0, 45.0],
        },
        "shoulder_geometry": {
            "arc_count_per_shoulder": 2,
            "arc_radius_w": SHOULDER_RADIUS,
            "arc_angle_deg": round(math.degrees(SHOULDER_ANGLE), 6),
            "derived_shoulder_span_w": round(SHOULDER_TOP_Z - 2.0, 6),
            "grip_length_w": 1.5,
        },
        "key_times": {"frame_210_s": t_for_frame(210), "frame_211_s": t_for_frame(211)},
        "component_count_by_frame_range": [
            {"frames": [1, LAST_CONTINUOUS_FRAME], "connected_components": 1},
            {"frames": [FRACTURE_FRAME, 300], "connected_components": 2},
        ],
        "v0_2_unloading": {
            "design_reason": "Local free-end unloading makes final ductile separation read as a short metal-like release while retaining necking and anchored grips.",
            "cut_half_gap_w": FRACTURE_HALF_GAP_W,
            "free_end_recoil_w_each": FREE_END_RECOIL_W,
            "recoil_duration_frames": 3,
            "recoil_duration_s": RECOIL_DURATION_S,
            "states": [break_state(frame) for frame in (210, 211, 212, 213, 214, 220, 271)],
        },
    }
    (SCENE_DIR / "synthetic_0001_geometry_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def render_still(frame, filename):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(PREVIEW_DIR / filename)
    bpy.ops.render.render(write_still=True)


def build():
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in list(block):
            if item.users == 0:
                block.remove(item)
    mats = make_materials()
    setup_camera_and_lights(mats)
    setup_machine(mats)
    set_render_settings()
    if STAGE == "scene":
        static = mesh_from_profile("Specimen_Continuous_001", profile_points(0.0), mats["specimen"])
        render_still(1, "scene_gate_initial.png")
        bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_DIR / "synthetic_0001_scene_gate.blend"))
        return
    specimen_objects = build_specimen_sequence(mats)
    digest = scene_hash(specimen_objects)
    write_geometry_evidence(specimen_objects, digest)
    bpy.context.scene["geometry_sha256"] = digest
    bpy.context.scene["fracture_frame"] = FRACTURE_FRAME
    bpy.context.scene["last_continuous_frame"] = LAST_CONTINUOUS_FRAME
    bpy.context.scene["time_mapping"] = "t=(frame-1)/30"
    if STAGE == "keyframes":
        for frame, name in [(1, "state_initial_f001.png"), (196, "state_necking_f196.png"), (205, "state_late_necking_f205.png"), (210, "state_continuous_f210.png"), (211, "state_first_fracture_f211.png"), (212, "state_unloading_f212.png"), (214, "state_unloading_complete_f214.png"), (220, "state_stable_post_fracture_f220.png"), (271, "state_post_fracture_f271.png")]:
            render_still(frame, name)
        bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_DIR / "synthetic_0001_animated.blend"))
    elif STAGE == "final":
        set_render_settings(final=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_DIR / "synthetic_0001_animated.blend"))
        bpy.ops.render.render(animation=True)
    else:
        raise ValueError("Unknown --stage: " + STAGE)


if __name__ == "__main__":
    build()
