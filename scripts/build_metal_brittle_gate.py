"""Reproducible keyframe gate for a metal, brittle, inside-gauge prototype.

Run from the repository root:
  /Applications/Blender.app/Contents/MacOS/Blender --python-exit-code 1 --background --python \
    scripts/build_metal_brittle_gate.py

The design deliberately uses a single flat dog-bone mesh before fracture (no
necked waist).  At FRAME_FIRST_SEPARATED it is replaced by two disjoint meshes
with a central 0.62-unit visual gap.  No video or labels are produced here.
"""
from pathlib import Path
import math
import json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "prototypes" / "metal_brittle"
with (ROOT / "configs" / "synthetic_0002.json").open(encoding="utf-8") as _config_file:
    CFG = json.load(_config_file)
FPS = CFG["fps"]
THICKNESS_W = CFG["implementation"]["thickness_w"]
FRAME_INITIAL = 1
FRAME_PRE = 180
FRAME_FIRST_SEPARATED = 181
FRAME_POST = 210
GAP_AT_FIRST = 0.62
SHOULDER_RADIUS = 0.80
SHOULDER_ANGLE = math.acos(0.75)
SHOULDER_TOP_Z = 2.0 + 2.0 * SHOULDER_RADIUS * math.sin(SHOULDER_ANGLE)
GRIP_OUTER_Z = SHOULDER_TOP_Z + 1.50


def t_for_frame(frame):
    return (frame - 1) / FPS


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
    return 0.42 * min(1.0, (frame - 1) / (FRAME_PRE - 1)) + max(0, frame - FRAME_FIRST_SEPARATED) * 0.0015


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


def render_state(frame, filename, separated=False):
    # Rebuilds only state objects; camera and deterministic lighting stay fixed.
    clear_scene()
    machine = mat("Machine_Dark_Metal", (0.12, 0.14, 0.16), 0.75, 0.42)
    jaw = mat("Jaw_Steel", (0.27, 0.29, 0.31), 0.75, 0.36)
    specimen = mat("Neutral_Brushed_Metal", (0.45, 0.45, 0.45), 0.8, 0.5)
    setup_render()
    build_machine(machine, jaw, frame)
    if separated:
        separated_specimen(specimen, frame, GAP_AT_FIRST + 0.010 * (frame - FRAME_FIRST_SEPARATED))
    else:
        continuous_specimen(specimen, frame)
    bpy.context.scene.frame_set(frame)
    bpy.context.scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


def write_gate_note():
    checks = []
    for frame in (FRAME_FIRST_SEPARATED, FRAME_POST, 240, 270, 300):
        target_gap = GAP_AT_FIRST + 0.010 * (frame - FRAME_FIRST_SEPARATED)
        lower = golden_outline(frame, "lower", target_gap)
        upper = golden_outline(frame, "upper", target_gap)
        lower_count = sum(1 for z, _ in [(-GRIP_OUTER_Z, 0.90), (-SHOULDER_TOP_Z, 0.90)] if z <= 0) + 1
        # The profile halves are constructed from increasing z samples first.
        lower_left = [z for _, z in lower[:len(lower)//2]]
        upper_left = [z for _, z in upper[:len(upper)//2]]
        lower_monotonic = all(b > a for a, b in zip(lower_left, lower_left[1:]))
        upper_monotonic = all(b > a for a, b in zip(upper_left, upper_left[1:]))
        actual_gap = min(z for _, z in upper) - max(z for _, z in lower)
        if not (actual_gap > 0 and lower_monotonic and upper_monotonic):
            raise RuntimeError(f"geometry validation failed f={frame}: gap={actual_gap}, lower_monotonic={lower_monotonic}, upper_monotonic={upper_monotonic}")
        checks.append((frame, target_gap, actual_gap, lower_monotonic and upper_monotonic))
    check_rows = "\n".join(
        f"| {frame} | {target:.3f} | {actual:.3f} | {'yes' if monotonic else 'no'} |"
        for frame, target, actual, monotonic in checks
    )
    note = f"""# Metal brittle inside-gauge keyframe gate

Fixed camera: orthographic frontal view.  FPS: {FPS}; time mapping: `t=(frame-1)/fps`.

| state | frame | time (s) | connected specimen components | geometric condition |
|---|---:|---:|---:|---|
| initial | {FRAME_INITIAL} | {t_for_frame(FRAME_INITIAL):.6f} | 1 | one watertight dog-bone mesh |
| pre-fracture | {FRAME_PRE} | {t_for_frame(FRAME_PRE):.6f} | 1 | one watertight dog-bone mesh; uniform 1.00-unit gauge, no neck |
| first separation | {FRAME_FIRST_SEPARATED} | {t_for_frame(FRAME_FIRST_SEPARATED):.6f} | 2 | `Specimen_Lower_Component` and `Specimen_Upper_Component` have no shared vertices; central gap = {GAP_AT_FIRST:.2f} units |
| post-fracture | {FRAME_POST} | {t_for_frame(FRAME_POST):.6f} | 2 | independent components; central gap grows while grip anchors remain visible |

The relevant geometric proof is direct in this script: `continuous_specimen()` creates one mesh through frame {FRAME_PRE}; `separated_specimen()` is first called at frame {FRAME_FIRST_SEPARATED} and creates two separate meshes. This is a still-frame design gate only, not an MP4, label sidecar, or physical fracture simulation.

## Post-break geometry validation

The release displacement is linear from the cut to the shoulder (`z=±2`), with a zero release at each shoulder/grip anchor. The table uses actual extrema of the two generated outlines; monotonicity means each cut-to-shoulder chain has strictly increasing Z and therefore has no Z-direction fold-back.

| frame | requested central gap | actual component bbox Z gap | no fold-back |
|---:|---:|---:|---|
{check_rows}
"""
    (OUT / "GATE.md").write_text(note, encoding="utf-8")


render_state(FRAME_INITIAL, "state_initial_f001.png")
render_state(FRAME_PRE, "state_prefracture_f180.png")
render_state(FRAME_FIRST_SEPARATED, "state_first_separation_f181.png", separated=True)
render_state(FRAME_POST, "state_postfracture_f210.png", separated=True)
for _frame in (240, 270, 300):
    render_state(_frame, f"validation_f{_frame:03d}.png", separated=True)
write_gate_note()
