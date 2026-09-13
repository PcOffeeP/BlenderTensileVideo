"""Render the single deterministic metal-brittle prototype from its config.

Run from the repository root:
  /Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python \
    scripts/build_metal_brittle_video.py -- --stage keyframes
  /Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python \
    scripts/build_metal_brittle_video.py -- --stage video

`keyframes` renders the four visual gate states. `video` renders an ignored
candidate MP4, never a formal output or JSON sidecar.
"""
from pathlib import Path
import math
import json
import sys
import hashlib
import os
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "prototypes" / "metal_brittle"
CONFIG = ROOT / "configs" / "synthetic_0002.json"
with CONFIG.open(encoding="utf-8") as _config_file:
    CFG = json.load(_config_file)
EXPECTED_PROFILE = {
    "video_id": "synthetic_0002",
    "material_type": "金属",
    "fracture_mechanism": "脆性断裂",
    "fracture_site": "inside_gauge",
    "scene_profile_id": "metal_flat_dogbone_l1_front_v1",
    "specimen_template": "flat_dogbone_v1",
    "material_profile": "neutral_brushed_metal_v1",
    "machine_template": "dual_grip_machine_l1_v1",
    "camera_profile": "front_fixed_v1",
    "lighting_profile": "soft_neutral_v1",
    "background_profile": "neutral_gray_v1",
    "tensile_axis": "Z",
    "moving_component": "Grip_Upper",
    "fixed_component": "Grip_Lower",
}
if any(CFG.get(key) != value for key, value in EXPECTED_PROFILE.items()):
    raise ValueError("synthetic_0002 metal-brittle scene/material configuration required")
FPS = CFG["fps"]
TOTAL_FRAMES = int(round(CFG["duration_s"] * FPS))
THICKNESS_W = CFG["implementation"]["thickness_w"]
POST_FRACTURE_FIXTURE_SHIFT = CFG["implementation"]["post_fracture_fixture_shift_w"]
RELEASE_DURATION_FRAMES = CFG["implementation"]["local_release_duration_frames"]
RELEASE_EXTRA_GAP = CFG["implementation"]["local_release_extra_gap_w"]
EXPECTED_DIMENSIONS = {
    "gauge_width_w": 1.0,
    "gauge_length_w": 4.0,
    "thickness_w": 0.15,
    "grip_width_w": 1.8,
    "grip_length_w": 1.5,
    "shoulder_radius_w": 0.8,
    "post_fracture_fixture_motion": "freeze_at_fracture",
    "post_fracture_fixture_shift_w": 0.42,
    "initial_separation_gap_w": 0.62,
    "local_release_duration_frames": 3,
    "local_release_extra_gap_w": 0.10,
}
if any(CFG["implementation"].get(key) != value for key, value in EXPECTED_DIMENSIONS.items()):
    raise ValueError("synthetic_0002 dimensions must match the frozen L1 metal scene")
FRAME_INITIAL = 1
FRAME_PRE = CFG["implementation"]["last_continuous_frame"]
FRAME_FIRST_SEPARATED = CFG["implementation"]["fracture_frame"]
FRAME_POST = 210
GAP_AT_FIRST = CFG["implementation"]["initial_separation_gap_w"]
SHOULDER_RADIUS = 0.80
SHOULDER_ANGLE = math.acos(0.75)
SHOULDER_TOP_Z = 2.0 + 2.0 * SHOULDER_RADIUS * math.sin(SHOULDER_ANGLE)
GRIP_OUTER_Z = SHOULDER_TOP_Z + 1.50


def t_for_frame(frame):
    return (frame - 1) / FPS


def stage():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        return "keyframes"
    if args == ["--stage", "keyframes"] or args == ["--stage", "video"]:
        return args[1]
    raise ValueError("use -- --stage keyframes or -- --stage video")


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in collection:
            collection.remove(item)


def mat(name, color, metallic=0.0, roughness=0.5):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def cube(name, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("Edge_Round", "BEVEL")
    bevel.width = 0.08
    bevel.segments = 2
    return obj


def extruded_profile(name, points_xz, material):
    """One watertight mesh, extruded along Y; point order follows perimeter."""
    depth = THICKNESS_W
    vertices = [(x, -depth / 2, z) for x, z in points_xz] + [(x, depth / 2, z) for x, z in points_xz]
    count = len(points_xz)
    faces = [tuple(range(count)), tuple(range(count, 2 * count))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, j + count, i + count))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bevel = obj.modifiers.new("Micro_Edge", "BEVEL")
    bevel.width = 0.035
    bevel.segments = 2
    return obj


def upper_shift(frame):
    """Finite, uniform-gauge elongation: no ductile necking."""
    return POST_FRACTURE_FIXTURE_SHIFT * min(1.0, (frame - 1) / (FRAME_PRE - 1))


def separation_gap(frame):
    """Initial brittle gap plus only a short local free-end release."""
    release = min(1.0, max(0.0, frame - FRAME_FIRST_SEPARATED) / RELEASE_DURATION_FRAMES)
    return GAP_AT_FIRST + RELEASE_EXTRA_GAP * release


def golden_outline(frame, half=None, gap=0.0):
    """Reuse v0.2's G1 shoulder construction, changing only deformation mode."""
    shoulder = []
    for i in range(17):
        path = 2.0 * SHOULDER_ANGLE * i / 16.0
        if path <= SHOULDER_ANGLE:
            z = 2.0 + SHOULDER_RADIUS * math.sin(path)
            width = 0.50 + SHOULDER_RADIUS * (1.0 - math.cos(path))
        else:
            u = path - SHOULDER_ANGLE
            z = 2.0 + SHOULDER_RADIUS * math.sin(SHOULDER_ANGLE) + SHOULDER_RADIUS * (math.sin(SHOULDER_ANGLE) - math.sin(SHOULDER_ANGLE-u))
            width = 0.50 + SHOULDER_RADIUS * (1.0-math.cos(SHOULDER_ANGLE)) + SHOULDER_RADIUS * (math.cos(SHOULDER_ANGLE-u)-math.cos(SHOULDER_ANGLE))
        shoulder.append((z, width))
    lower = [(-GRIP_OUTER_Z, 0.90), (-SHOULDER_TOP_Z, 0.90)]
    lower += [(-z, w) for z, w in list(reversed(shoulder))[1:]]
    lower += [(z, 0.50) for z in (-1.60, -1.20, -0.80, -0.40, 0.0, 0.40, 0.80, 1.20, 1.60, 2.00)]
    full = lower + shoulder[1:] + [(GRIP_OUTER_Z, 0.90)]
    stretch = upper_shift(frame)
    def mapped(z):
        return z if z <= -2.0 else z + stretch if z >= 2.0 else z + stretch * (z + 2.0) / 4.0
    if half == "lower":
        refs = [(z,w) for z,w in full if z <= 0.0]
        # Local release has its full value at the cut and falls linearly to
        # zero at the gauge/shoulder boundary (z=-2).  Every neighbouring
        # gauge vertex moves with it, so no hooked or self-crossing outline
        # appears as the post-break gap increases through frame 300.
        def lower_z(z):
            release = gap / 2 * max(0.0, min(1.0, (z + 2.0) / 2.0))
            return mapped(z) - release
        left = [(-w, lower_z(z)) for z,w in refs]
        right = [(w, lower_z(z)) for z,w in reversed(refs)]
        return left + right
    if half == "upper":
        refs = [(z,w) for z,w in full if z >= 0.0]
        def upper_z(z):
            release = gap / 2 * max(0.0, min(1.0, (2.0 - z) / 2.0))
            return mapped(z) + release
        left = [(-w, upper_z(z)) for z,w in refs]
        right = [(w, upper_z(z)) for z,w in reversed(refs)]
        return left + right
    return [(-w, mapped(z)) for z,w in full] + [(w, mapped(z)) for z,w in reversed(full)]


def continuous_specimen(material, frame):
    return extruded_profile("Specimen_Continuous", golden_outline(frame), material)


def separated_specimen(material, frame, gap):
    return (extruded_profile("Specimen_Lower_Component", golden_outline(frame, "lower", gap), material),
            extruded_profile("Specimen_Upper_Component", golden_outline(frame, "upper", gap), material))


def build_machine(machine, jaw, frame):
    shift = upper_shift(frame)
    # Paired jaws leave shoulder and gauge boundaries unoccluded.
    jaw_z = SHOULDER_TOP_Z + 0.78
    crosshead_z = GRIP_OUTER_Z + 0.18
    cube("Crosshead_Lower_Partial", (0, 0, -crosshead_z), (2.8, 0.52, 0.26), machine)
    cube("Crosshead_Upper_Partial", (0, 0, crosshead_z + shift), (2.8, 0.52, 0.26), machine)
    for sign in (-1, 1):
        cube("Lower_Jaw_" + str(sign), (1.18 * sign, 0, -jaw_z), (0.35, 0.42, 0.62), jaw)
        cube("Upper_Jaw_" + str(sign), (1.18 * sign, 0, jaw_z + shift), (0.35, 0.42, 0.62), jaw)


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 854
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.fps = FPS
    scene.world.color = (0.14, 0.14, 0.14)
    camera_data = bpy.data.cameras.new("Camera_Front_Fixed")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 23.25
    camera = bpy.data.objects.new("Camera_Front_Fixed", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (0, -20, 0.70)
    camera.rotation_euler = ((Vector((0, 0, 0.70)) - camera.location).to_track_quat("-Z", "Y")).to_euler()
    scene.camera = camera
    backdrop = mat("Neutral_Background", (0.26, 0.26, 0.26), 0.0, 0.8)
    nodes = backdrop.node_tree.nodes; links = backdrop.node_tree.links
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (0.19, 0.19, 0.19, 1.0)
    emission.inputs["Strength"].default_value = 0.32
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    cube("Neutral_Background", (0, 1.0, 0.7), (20.0, 0.08, 10.0), backdrop)
    for name, location, energy, size in [
        ("Key_Softbox", (-4.2, -5.0, 5.5), 200, 5.0),
        ("Fill_Softbox", (4.0, -3.0, 1.0), 150, 5.0),
        ("Front_Softbox", (0.0, -6.0, 0.7), 120, 8.0),
        ("Rim_Softbox", (0.0, 1.5, 4.5), 55, 3.0),
    ]:
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy; data.shape = "DISK"; data.size = size
        lamp = bpy.data.objects.new(name, data); bpy.context.collection.objects.link(lamp); lamp.location = location
        lamp.rotation_euler = ((Vector((0, 0, 0)) - lamp.location).to_track_quat("-Z", "Y")).to_euler()


def setup_animated_scene():
    clear_scene()
    machine = mat("Machine_Dark_Metal", (0.12, 0.14, 0.16), 0.75, 0.42)
    jaw = mat("Jaw_Steel", (0.27, 0.29, 0.31), 0.75, 0.36)
    specimen = mat("Neutral_Brushed_Metal", (0.45, 0.45, 0.45), 0.8, 0.5)
    setup_render()
    # Build the frozen apparatus once. The per-frame specimen meshes carry the
    # complete deterministic deformation; no simulation state is involved.
    build_machine(machine, jaw, FRAME_INITIAL)
    # The upper fixture is the only moving machine component. Anchored specimen
    # ends are already encoded at the matching profile coordinates each frame.
    for obj in list(bpy.data.objects):
        if obj.name.startswith("Upper_") or obj.name == "Crosshead_Upper_Partial":
            base_z = obj.location.z
            for frame in range(1, TOTAL_FRAMES + 1):
                obj.location.z = base_z + upper_shift(frame)
                obj.keyframe_insert("location", frame=frame)
    objects = []
    for frame in range(1, TOTAL_FRAMES + 1):
        if frame <= FRAME_PRE:
            objects.append(continuous_specimen(specimen, frame))
        else:
            gap = separation_gap(frame)
            objects.extend(separated_specimen(specimen, frame, gap))
        for obj in objects[-1:] if frame <= FRAME_PRE else objects[-2:]:
            obj.hide_render = True
            obj.keyframe_insert("hide_render", frame=1)
            obj.hide_render = False
            obj.keyframe_insert("hide_render", frame=frame)
            if frame < TOTAL_FRAMES:
                obj.hide_render = True
                obj.keyframe_insert("hide_render", frame=frame + 1)
    scene = bpy.context.scene
    scene.frame_start = 1; scene.frame_end = TOTAL_FRAMES
    scene.render.resolution_x = CFG["resolution_x"]; scene.render.resolution_y = CFG["resolution_y"]
    return scene


def render_gate_states(scene):
    for frame, name in [(FRAME_INITIAL, "synthetic_0002_state_initial_f001.png"),
                        (FRAME_PRE, "synthetic_0002_state_prefracture_f180.png"),
                        (FRAME_FIRST_SEPARATED, "synthetic_0002_state_first_separation_f181.png"),
                        (184, "synthetic_0002_state_release_complete_f184.png"),
                        (FRAME_POST, "synthetic_0002_state_postfracture_f210.png"),
                        (TOTAL_FRAMES, "synthetic_0002_state_postfracture_f300.png")]:
        scene.frame_set(frame)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(OUT / name)
        bpy.ops.render.render(write_still=True)


def render_video(scene):
    # Blender 5 routes video selection through media_type; image codec remains
    # an image-only enum.
    scene.render.image_settings.media_type = "VIDEO"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "REALTIME"
    video = OUT / (CFG["video_id"] + ".mp4")
    temporary_video = OUT / (CFG["video_id"] + ".rendering.mp4")
    if temporary_video.exists():
        temporary_video.unlink()
    scene.render.filepath = str(temporary_video)
    scene.frame_set(1)
    bpy.ops.render.render(animation=True)
    # Blender has closed the MP4 only after animation render returns. Promote
    # the finished temporary file atomically, keeping an existing candidate
    # intact if an interrupted render never returns.
    os.replace(temporary_video, video)
    evidence = {
        "schema_version": "synthetic-render-evidence/v0.1",
        "video_id": CFG["video_id"],
        "config_sha256": hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        "generator_script": "scripts/build_metal_brittle_video.py",
        "generator_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "video_sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
        "blender_version": bpy.app.version_string,
        "first_separated_frame": FRAME_FIRST_SEPARATED,
    }
    (OUT / "render-evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


OUT.mkdir(parents=True, exist_ok=True)
scene = setup_animated_scene()
if stage() == "keyframes":
    render_gate_states(scene)
else:
    render_video(scene)
