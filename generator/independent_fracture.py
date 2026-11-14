#!/usr/bin/env python3
"""Author-defined tensile scenes; no recorded video or old scene is imported.

Run in Blender, with arguments after ``--``.  See generator/README.md.
The animation is a controlled geometric illustration, not a material solver.
"""

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


VERSION = "independent-fracture/0.1.0"
FPS = 30
NFRAMES = 600
FIRST_BREAK = {"brittle": 360, "ductile": 390}  # zero-based video frames
CRACK_BEGIN = 315
RESOLUTION = (1280, 960)
N_Z = 64
N_X = 32
N_Y = 4
HALF_LENGTH = 1.7
MESH_SPEC = {"width_gauge": 0.48, "width_grip": 0.78, "thickness": 0.22}


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def window(s):
    return 1.0 - smoothstep((abs(s) - 1.05) / 0.36)


def width_at(s):
    return 0.48 + 0.30 * smoothstep((abs(s) - 1.05) / 0.45)


def perimeter():
    # Clockwise in the camera's view, counter-clockwise from +Z.
    return ([(j, 0) for j in range(N_X)]
            + [(N_X, k) for k in range(N_Y)]
            + [(j, N_Y) for j in range(N_X, 0, -1)]
            + [(0, k) for k in range(N_Y, 0, -1)])


PERIMETER = perimeter()


def motion(kind, frame):
    if kind == "brittle":
        return {"load": 0.0, "tip": N_X if frame >= FIRST_BREAK[kind] else 0,
                "separated": frame >= FIRST_BREAK[kind], "opening": 0.014}
    load = smoothstep((frame - 45) / (FIRST_BREAK[kind] - 45))
    if frame < CRACK_BEGIN:
        tip, progress = 0, 0.0
    elif frame >= FIRST_BREAK[kind]:
        tip, progress = N_X, 1.0
    else:
        progress = (frame - CRACK_BEGIN + 1) / (FIRST_BREAK[kind] - CRACK_BEGIN + 1)
        tip = max(1, min(N_X - 1, int(math.ceil(progress * N_X))))
    return {"load": load, "tip": tip, "separated": frame >= FIRST_BREAK[kind],
            "opening": 0.008 + 0.030 * progress}


def axial_state(kind, frame):
    state = motion(kind, frame)
    levels = [-HALF_LENGTH + 2 * HALF_LENGTH * i / N_Z for i in range(N_Z + 1)]
    lam = []
    for s in levels:
        if kind == "ductile":
            local = 0.54 * math.exp(-0.5 * (s / 0.32) ** 2)
            lam.append(1.0 + state["load"] * (0.035 * window(s) + local * window(s)))
        else:
            lam.append(1.0)
    z = [-HALF_LENGTH]
    for i in range(1, len(levels)):
        z.append(z[-1] + (levels[i] - levels[i-1]) * (lam[i] + lam[i-1]) / 2)
    return state, levels, lam, z


def specimen_mesh(kind, frame):
    state, levels, lam, zvals = axial_state(kind, frame)
    tip, separated, opening = state["tip"], state["separated"], state["opening"]
    mid = N_Z // 2
    verts, faces, face_material = [], [], []
    layers = []
    seam_pairs = []

    def seam_shape(j, k):
        x = j / N_X * 2 - 1
        y = k / N_Y * 2 - 1
        if kind == "brittle":
            # Matching fracture profiles run through the specimen thickness;
            # a normal view can see the background through the small gap.
            return 0.012 * (0.65 * math.sin(3.8*x + 0.3) + 0.35 * math.sin(9.0*x))
        return 0.006 * (0.65 * math.sin(3.8*x + 0.3) * math.cos(2.3*y)
                        + 0.35 * math.sin(9.0*x - 1.4*y))

    def opening_at(j):
        if tip == 0:
            return 0.0
        if kind == "brittle":
            return opening
        if separated:
            return opening * (0.35 + 0.65 * (1.0 - j / N_X))
        if j >= tip:
            return 0.0
        return opening * (1.0 - j / tip)

    def xyz(i, j, k, side=0):
        s = levels[i]
        scale = 1.0 / math.sqrt(lam[i])
        x = (j / N_X - 0.5) * width_at(s) * scale
        y = (k / N_Y - 0.5) * MESH_SPEC["thickness"] * scale
        near_seam = 1.0 - smoothstep(abs(s) / 0.34)
        near_grip = 1.0 - smoothstep(abs(s) / 1.43)
        sign = side if i == mid else (-1 if i < mid else 1)
        zz = zvals[i] + seam_shape(j, k) * near_seam
        zz += sign * opening_at(j) * near_grip / 2.0
        return (x, y, zz)

    def new_vertex(position):
        verts.append(position)
        return len(verts) - 1

    def make_ring(i, side=0, lower=None):
        result = {}
        for j, k in PERIMETER:
            shared = (i == mid and lower is not None and not separated and j >= tip)
            result[j, k] = lower[j, k] if shared else new_vertex(xyz(i, j, k, side))
        return result

    for i in range(N_Z + 1):
        if i == mid and tip:
            low = make_ring(i, -1)
            high = make_ring(i, +1, low)
            layers.append((low, high))
        else:
            ring = make_ring(i, 0)
            layers.append((ring, ring))

    def add_face(vertices, material=0):
        faces.append(tuple(vertices))
        face_material.append(material)

    for i in range(N_Z):
        lower = layers[i][1]
        upper = layers[i + 1][0]
        for p, key in enumerate(PERIMETER):
            nxt = PERIMETER[(p + 1) % len(PERIMETER)]
            add_face((lower[key], lower[nxt], upper[nxt], upper[key]))
    add_face([layers[0][0][key] for key in reversed(PERIMETER)])
    add_face([layers[-1][1][key] for key in PERIMETER])

    if tip:
        low_ring, high_ring = layers[mid]
        lower_grid, upper_grid = {}, {}
        for j in range(tip + 1):
            for k in range(N_Y + 1):
                key = (j, k)
                boundary = key in low_ring
                if boundary:
                    lo, hi = low_ring[key], high_ring[key]
                else:
                    lo = new_vertex(xyz(mid, j, k, -1))
                    hi = lo if (not separated and j == tip) else new_vertex(xyz(mid, j, k, +1))
                lower_grid[key], upper_grid[key] = lo, hi
                seam_pairs.append((lo, hi, j, k))
        for j in range(tip):
            for k in range(N_Y):
                a, b, c, d = ((j, k), (j+1, k), (j+1, k+1), (j, k+1))
                # The two matching surfaces must use the same diagonal. Letting
                # Blender triangulate oppositely wound non-planar quads can
                # otherwise make the faces cross near a nearly closed tip.
                add_face((lower_grid[a], lower_grid[b], lower_grid[c]), 1)
                add_face((lower_grid[a], lower_grid[c], lower_grid[d]), 1)
                add_face((upper_grid[c], upper_grid[b], upper_grid[a]), 1)
                add_face((upper_grid[d], upper_grid[c], upper_grid[a]), 1)

    mesh = bpy.data.meshes.new(f"specimen_{kind}_{frame:04d}")
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)
    for polygon, material in zip(mesh.polygons, face_material):
        polygon.material_index = material
    return mesh, {"state": state, "levels": levels, "lam": lam, "zvals": zvals,
                  "layers": layers, "seam_pairs": seam_pairs}


def material(name, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    shader = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    mat.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def box(name, position, size, mat, bevel=0.035):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("machined_edges", "BEVEL")
        mod.width, mod.segments = bevel, 3
        mod.affect = "EDGES"
        normal = obj.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
        normal.keep_sharp = True
    return obj


def cylinder(name, position, radius, depth, mat, rotate_x=0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth,
                                      location=position, rotation=(rotate_x, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = len(poly.vertices) == 4
    bevel = obj.modifiers.new("rounded_edges", "BEVEL")
    bevel.width, bevel.segments = 0.018, 3
    return obj


def track(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area_light(name, location, energy, size, target, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=location)
    obj = bpy.context.object
    obj.name, obj.data.energy, obj.data.shape, obj.data.size = name, energy, "DISK", size
    obj.data.color = color
    track(obj, target)


def setup_scene(kind, output):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = os.environ.get("FRACTURE_ENGINE", "BLENDER_EEVEE")
    scene.cycles.samples = 20
    scene.cycles.use_denoising = True
    scene.cycles.seed = 19
    scene.eevee.taa_render_samples = 32
    scene.render.resolution_x, scene.render.resolution_y = RESOLUTION
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.world.color = (0.12, 0.12, 0.12)
    scene.view_settings.view_transform = "AgX"
    scene.render.filepath = str(output)
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 8

    ceramic = material("ceramic porcelain ivory", (0.72, 0.68, 0.58), roughness=0.36)
    ceramic_break = material("ceramic fresh fracture", (0.52, 0.47, 0.39), roughness=0.83)
    metal = material("satin alloy", (0.66, 0.70, 0.74), metallic=0.48, roughness=0.3)
    metal_break = material("metal fracture face", (0.28, 0.31, 0.33), metallic=0.25, roughness=0.83)
    fixture = material("slate fixture", (0.10, 0.15, 0.18), metallic=0.68, roughness=0.34)
    jaws = material("jaw faces", (0.24, 0.28, 0.29), metallic=0.72, roughness=0.3)
    accent = material("machine trim", (0.28, 0.38, 0.40), metallic=0.55, roughness=0.42)
    wall = material("matte warm grey background", (0.06, 0.075, 0.073), roughness=0.95)

    box("background", (0, 1.8, 0.0), (16, 0.15, 14), wall, 0)
    for x in (-1.55, 1.55):
        cylinder("fixed guide", (x, 0.50, 0), 0.095, 6.1, fixture)
    box("lower beam", (0, 0.25, -2.65), (3.5, 0.80, 0.26), fixture, 0.05)
    cylinder("lower load rod", (0, 0.0, -2.22), 0.20, 0.65, accent)

    upper = []
    upper.append(box("upper beam", (0, 0.25, 2.70), (3.5, 0.80, 0.27), fixture, 0.05))
    upper.append(cylinder("upper load rod", (0, 0, 2.24), 0.20, 0.70, accent))
    for sign in (-1, 1):
        center_z = sign * 1.65
        pair = []
        for ysign in (-1, 1):
            obj = box(f"{'upper' if sign > 0 else 'lower'} {'front' if ysign < 0 else 'back'} jaw",
                      (0, ysign * (MESH_SPEC['thickness']/2 + 0.15), center_z),
                      (1.05, 0.30, 0.54), jaws, 0.025)
            pair.append(obj)
            if sign > 0:
                upper.append(obj)
        for x in (-0.35, 0.35):
            bolt = cylinder(f"{'upper' if sign > 0 else 'lower'} bolt", (x, -0.425, center_z),
                            0.065, 0.08, accent, math.pi/2)
            if sign > 0:
                upper.append(bolt)

    mesh, _ = specimen_mesh(kind, 0)
    obj = bpy.data.objects.new("specimen", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(ceramic if kind == "brittle" else metal)
    obj.data.materials.append(ceramic_break if kind == "brittle" else metal_break)
    for poly in obj.data.polygons:
        poly.use_smooth = False

    camera_location = (0, -16, 0.30) if kind == "brittle" else (0.8, -16.0, 1.0)
    bpy.ops.object.camera_add(location=camera_location)
    camera = bpy.context.object
    camera.name = "fixed camera"
    camera.data.type, camera.data.ortho_scale = "ORTHO", 6.30
    track(camera, (0, 0, 0.30))
    scene.camera = camera
    area_light("large soft key", (-3.5, -5.0, 5.5), 850, 5.0, (0, 0, 0.1), (1.0, 0.93, 0.82))
    area_light("cool fill", (4.0, -2.5, 1.8), 600, 4.0, (0, 0, 0.1), (0.82, 0.90, 1.0))
    area_light("edge", (0, 0.8, 4.5), 250, 3.0, (0, 0, 0), (1.0, 1.0, 1.0))
    base_upper = {item.name: item.location.z for item in upper}
    return scene, obj, upper, base_upper


def set_state(kind, frame, obj, upper, upper_initial):
    mesh, info = specimen_mesh(kind, frame)
    old = obj.data
    obj.data = mesh
    for mat in old.materials:
        mesh.materials.append(mat)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    lift = info["zvals"][-1] - HALF_LENGTH
    for item in upper:
        item.location.z = upper_initial[item.name] + lift
    bpy.context.view_layer.update()
    return info


def render_image(scene, path):
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def component_count(mesh):
    parents = list(range(len(mesh.vertices)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parents[b] = a
    for edge in mesh.edges:
        union(edge.vertices[0], edge.vertices[1])
    return len({find(i) for i in range(len(parents))})


def mesh_volume(mesh):
    mesh.calc_loop_triangles()
    total = 0.0
    for tri in mesh.loop_triangles:
        a, b, c = (mesh.vertices[i].co for i in tri.vertices)
        total += a.dot(b.cross(c)) / 6
    return abs(total)


def actual_measures(kind, frame, obj, upper, info):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    verts = mesh.vertices
    gap = [verts[hi].co.z - verts[lo].co.z for lo, hi, j, k in info["seam_pairs"]]
    center = info["layers"][N_Z//2][0]
    left, right = center[(0, 0)], center[(N_X, 0)]
    front, back = center[(N_X//2, 0)], center[(N_X//2, N_Y)]
    width = verts[right].co.x - verts[left].co.x
    thickness = verts[back].co.y - verts[front].co.y
    upper_jaw = next(item for item in upper if item.name == "upper front jaw")
    upper_rim = info["layers"][-1][1]
    lower_rim = info["layers"][0][0]
    top = sum(verts[v].co.z for v in upper_rim.values()) / len(upper_rim)
    bottom = sum(verts[v].co.z for v in lower_rim.values()) / len(lower_rim)
    end_contact = max(abs(abs(verts[v].co.y) - MESH_SPEC['thickness']/2)
                      for ring in (upper_rim, lower_rim) for (j,k),v in ring.items() if k in (0,N_Y))
    jaw_center_error = abs((top - upper_jaw.location.z) - (HALF_LENGTH - 1.65))
    def actual_bounds(name):
        item = bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get())
        item_mesh = item.to_mesh()
        points = [item.matrix_world @ v.co for v in item_mesh.vertices]
        box = [(min(p[i] for p in points), max(p[i] for p in points)) for i in range(3)]
        item.to_mesh_clear()
        return box
    upper_front, upper_back = actual_bounds("upper front jaw"), actual_bounds("upper back jaw")
    lower_front, lower_back = actual_bounds("lower front jaw"), actual_bounds("lower back jaw")
    jaw_gaps = []
    for ring, front_box, back_box in ((upper_rim, upper_front, upper_back),
                                     (lower_rim, lower_front, lower_back)):
        ymin = min(verts[v].co.y for v in ring.values())
        ymax = max(verts[v].co.y for v in ring.values())
        jaw_gaps.extend((ymin-front_box[1][1], back_box[1][0]-ymax))
    connections = []
    for rod, beam, jaw in (("upper load rod", "upper beam", upper_front),
                           ("lower load rod", "lower beam", lower_front)):
        rod_box, beam_box = actual_bounds(rod), actual_bounds(beam)
        connections.append(all(min(rod_box[i][1], beam_box[i][1]) >= max(rod_box[i][0], beam_box[i][0])
                               for i in range(3)))
        # The front jaw and the central rod intersect at the jaw's rear edge in Y.
        connections.append(all(min(rod_box[i][1], jaw[i][1]) >= max(rod_box[i][0], jaw[i][0])
                               for i in range(3)))
    signature = hashlib.sha256(b''.join((f"{v.co.x:.9f},{v.co.y:.9f},{v.co.z:.9f};".encode() for v in verts))).hexdigest()
    result = {"frame": frame, "components": component_count(mesh), "volume": mesh_volume(mesh),
              "width_at_fracture": width, "thickness_at_fracture": thickness,
              "grip_end_to_end_length": top-bottom, "minimum_crack_gap": min(gap) if gap else None,
              "maximum_crack_gap": max(gap) if gap else None, "contact_y_error": end_contact,
              "actual_jaw_face_gaps": jaw_gaps, "load_path_bounds_overlap": connections,
              "upper_jaw_alignment_error": jaw_center_error, "geometry_sha256": signature,
              "upper_jaw_z": upper_jaw.location.z, "tip_columns": info['state']['tip']}
    evaluated.to_mesh_clear()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("brittle", "ductile"), required=True)
    parser.add_argument("--mode", choices=("preview", "render", "audit"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--frame-start", type=int, default=0)
    parser.add_argument("--frame-end", type=int, default=NFRAMES-1)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    scene, obj, upper, initial = setup_scene(args.kind, out)
    if args.mode == "preview":
        frames = [0, FIRST_BREAK[args.kind]-1, FIRST_BREAK[args.kind]] if args.kind == "brittle" else [0, 210, 330, 375, 390, 599]
        for frame in frames:
            set_state(args.kind, frame, obj, upper, initial)
            render_image(scene, out / f"{args.kind}_{frame:04d}.png")
            print("PREVIEW", args.kind, frame, flush=True)
    elif args.mode == "render":
        frames = [0, FIRST_BREAK[args.kind]] if args.kind == "brittle" else range(args.frame_start, args.frame_end+1)
        for frame in frames:
            set_state(args.kind, frame, obj, upper, initial)
            render_image(scene, out / f"{args.kind}_{frame:04d}.png")
            if frame % 30 == 0:
                print("RENDER", args.kind, frame, flush=True)
    else:
        results = []
        for frame in range(args.frame_start, args.frame_end+1):
            info = set_state(args.kind, frame, obj, upper, initial)
            results.append(actual_measures(args.kind, frame, obj, upper, info))
            if frame % 100 == 0:
                print("AUDIT", args.kind, frame, flush=True)
        with open(out / f"{args.kind}_mesh_audit.json", "w") as handle:
            json.dump({"generator": VERSION, "frame_numbering": "zero-based", "measurements": results}, handle, indent=2)
    print("FINISHED", args.kind, args.mode, flush=True)


if __name__ == "__main__":
    main()
