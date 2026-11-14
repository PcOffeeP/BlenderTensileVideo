#!/usr/bin/env python3
"""Discrete independent tensile scenes with simultaneous full-section failure.

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
from mathutils.bvhtree import BVHTree


VERSION = "independent-fracture-batch/0.1.0"
FPS = 30
NFRAMES = 600
RESOLUTION = (1280, 960)
N_Z = 64
N_X = 32
N_Y = 4
HALF_LENGTH = 1.7
CASE = None
MESH_SPEC = {}
STYLES = {}
INTERSECTION_CACHE = {}


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def window(s):
    return 1.0 - smoothstep((abs(s) - 1.05) / 0.36)


def width_at(s):
    return (MESH_SPEC["width_gauge"]
            + (MESH_SPEC["width_grip"] - MESH_SPEC["width_gauge"])
            * smoothstep((abs(s) - 1.05) / 0.45))


def perimeter():
    # Clockwise in the camera's view, counter-clockwise from +Z.
    return ([(j, 0) for j in range(N_X)]
            + [(N_X, k) for k in range(N_Y)]
            + [(j, N_Y) for j in range(N_X, 0, -1)]
            + [(0, k) for k in range(N_Y, 0, -1)])


PERIMETER = perimeter()


def motion(kind, frame):
    event = CASE["event_frame"]
    separated = frame >= event
    if kind == "brittle":
        load = 0.0
    elif CASE.get("preloaded", False):
        load = 1.0
    else:
        start, finish = CASE["ramp_start_frame"], event - 1
        load = 1.0 if frame >= finish else smoothstep((frame - start) / (finish - start))
    return {"load": load, "tip": N_X if separated else 0, "separated": separated,
            "opening": 0.018 if kind == "brittle" else 0.022}


def axial_state(kind, frame):
    state = motion(kind, frame)
    center = CASE["fracture_s"]
    mid = N_Z // 2
    levels = [(-HALF_LENGTH + (center + HALF_LENGTH) * i / mid if i <= mid
               else center + (HALF_LENGTH - center) * (i - mid) / mid)
              for i in range(N_Z + 1)]
    lam = []
    for s in levels:
        if kind == "ductile":
            local = 0.54 * math.exp(-0.5 * ((s - center) / 0.32) ** 2)
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
        roughness = 0.012 if kind == "brittle" else 0.006
        return roughness * (0.65 * math.sin(3.8*x + 0.3) + 0.35 * math.sin(9.0*x))

    def opening_at(j):
        return opening if separated else 0.0

    def xyz(i, j, k, side=0):
        s = levels[i]
        scale = 1.0 / math.sqrt(lam[i])
        x = (j / N_X - 0.5) * width_at(s) * scale
        y = (k / N_Y - 0.5) * MESH_SPEC["thickness"] * scale
        distance = abs(s - CASE["fracture_s"])
        near_seam = 1.0 - smoothstep(distance / 0.34)
        grip_distance = (CASE["fracture_s"] + 1.43 if s < CASE["fracture_s"]
                         else 1.43 - CASE["fracture_s"])
        near_grip = 1.0 - smoothstep(distance / grip_distance)
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


def jaw_block(name, position, size, mat, shape):
    if shape in ("box", "rounded"):
        return box(name, position, size, mat, 0.105 if shape == "rounded" else 0.018)
    width, depth, height = size
    if shape == "wedge":
        outline = [(-width/2, -height/2), (width/2, -height/2),
                   (width*0.36, height/2), (-width*0.36, height/2)]
    elif shape == "chamfer":
        cut = min(width, height) * 0.18
        outline = [(-width/2+cut,-height/2), (width/2-cut,-height/2),
                   (width/2,-height/2+cut), (width/2,height/2-cut),
                   (width/2-cut,height/2), (-width/2+cut,height/2),
                   (-width/2,height/2-cut), (-width/2,-height/2+cut)]
    else:
        raise ValueError(f"unknown jaw shape: {shape}")
    n = len(outline)
    points = [(x, y, z) for y in (-depth/2, depth/2) for x, z in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, n*2))]
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(points, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("edge highlights", "BEVEL")
    bevel.width, bevel.segments = 0.015, 3
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
    scene.eevee.taa_render_samples = 16
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

    style = STYLES[CASE["style"]]
    color = CASE["specimen_color"]
    specimen_mat = material("author-defined specimen", color, metallic=0.48 if kind == "ductile" else 0.0,
                            roughness=0.32 if kind == "ductile" else 0.4)
    fracture_mat = material("author-defined fracture", tuple(c * 0.65 for c in color),
                            metallic=0.15 if kind == "ductile" else 0.0, roughness=0.84)
    fixture = material("frame", style["fixture_color"], metallic=0.68, roughness=0.34)
    jaws = material("jaw faces", style["jaw_color"], metallic=0.72, roughness=0.3)
    accent = material("machine trim", style["accent_color"], metallic=0.55, roughness=0.42)
    wall = material("matte background", style["background_color"], roughness=0.95)

    box("background", (0, 1.8, 0.0), (16, 0.15, 14), wall, 0)
    for x in (-1.55, 1.55):
        if style["rail_shape"] == "round":
            cylinder("fixed guide", (x, 0.50, 0), 0.095, 6.1, fixture)
        else:
            box("fixed guide", (x, 0.50, 0), (0.19, 0.19, 6.1), fixture, 0.018)
    box("lower beam", (0, 0.25, -2.65), (3.5, 0.80, 0.26), fixture, 0.05)
    cylinder("lower load rod", (0, 0.0, -2.22), 0.20, 0.65, accent)

    upper = []
    upper.append(box("upper beam", (0, 0.25, 2.70), (3.5, 0.80, 0.27), fixture, 0.05))
    upper.append(cylinder("upper load rod", (0, 0, 2.24), 0.20, 0.70, accent))
    for sign in (-1, 1):
        center_z = sign * 1.65
        pair = []
        for ysign in (-1, 1):
            obj = jaw_block(f"{'upper' if sign > 0 else 'lower'} {'front' if ysign < 0 else 'back'} jaw",
                            (0, ysign * (MESH_SPEC['thickness']/2 + 0.15), center_z),
                            (style['jaw_width'], 0.30, style['jaw_height']), jaws, style['jaw_shape'])
            pair.append(obj)
            if sign > 0:
                upper.append(obj)
        for x in (-0.35, 0.35):
            bolt = cylinder(f"{'upper' if sign > 0 else 'lower'} bolt",
                            (x, -MESH_SPEC['thickness']/2 - 0.315, center_z),
                            0.065, 0.08, accent, math.pi/2)
            if sign > 0:
                upper.append(bolt)

    mesh, _ = specimen_mesh(kind, 0)
    obj = bpy.data.objects.new("specimen", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(specimen_mat)
    obj.data.materials.append(fracture_mat)
    for poly in obj.data.polygons:
        poly.use_smooth = False

    bpy.ops.object.camera_add(location=(0, -16, 0.30))
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


def material_segment(mesh, info):
    """Measure the same author-defined material segment, excluding any gap."""
    levels, layers = info["levels"], info["layers"]
    middle = N_Z // 2
    center = CASE["fracture_s"]
    lo_i = max(i for i in range(middle) if levels[i] <= center - 0.40)
    hi_i = min(i for i in range(middle+1, N_Z+1) if levels[i] >= center + 0.40)
    selected = set()
    for low, high in layers[lo_i:hi_i+1]:
        selected.update(low.values())
        selected.update(high.values())
    for low, high, _j, _k in info["seam_pairs"]:
        selected.update((low, high))
    mesh.calc_loop_triangles()
    total = 0.0
    for tri in mesh.loop_triangles:
        if all(i in selected for i in tri.vertices):
            a, b, c = (mesh.vertices[i].co for i in tri.vertices)
            total += a.dot(b.cross(c)) / 6.0
    for layer, reverse in ((layers[lo_i][0], True), (layers[hi_i][1], False)):
        order = list(reversed(PERIMETER)) if reverse else PERIMETER
        coords = [mesh.vertices[layer[key]].co for key in order]
        for i in range(1, len(coords)-1):
            total += coords[0].dot(coords[i].cross(coords[i+1])) / 6.0
    key = (N_X//2, 0)
    material_length = sum((mesh.vertices[layers[i+1][0][key]].co
                           - mesh.vertices[layers[i][1][key]].co).length
                          for i in range(lo_i, hi_i))
    mid_low = mesh.vertices[layers[middle][0][key]].co
    mid_high = mesh.vertices[layers[middle][1][key]].co
    return {"material_s_bounds":[levels[lo_i], levels[hi_i]],
            "front_surface_material_path_length":material_length,
            "segment_volume":abs(total), "front_surface_centerline_gap":mid_high.z-mid_low.z}


def nonadjacent_overlaps(mesh):
    mesh.calc_loop_triangles()
    vertices = [tuple(v.co) for v in mesh.vertices]
    triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
    tree = BVHTree.FromPolygons(vertices, triangles, all_triangles=True, epsilon=0.0)
    return sum(1 for a, b in tree.overlap(tree)
               if a < b and not set(triangles[a]) & set(triangles[b]))


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
    mesh_ymin, mesh_ymax = min(v.co.y for v in verts), max(v.co.y for v in verts)
    jaw_clearance = min(mesh_ymin-upper_front[1][1], upper_back[1][0]-mesh_ymax,
                        mesh_ymin-lower_front[1][1], lower_back[1][0]-mesh_ymax)
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
    if signature not in INTERSECTION_CACHE:
        INTERSECTION_CACHE[signature] = nonadjacent_overlaps(mesh)
    segment = material_segment(mesh, info)
    result = {"frame": frame, "components": component_count(mesh), "volume": mesh_volume(mesh),
              "width_at_fracture": width, "thickness_at_fracture": thickness,
              "grip_end_to_end_length": top-bottom, "minimum_crack_gap": min(gap) if gap else None,
              "maximum_crack_gap": max(gap) if gap else None, "contact_y_error": end_contact,
              "actual_jaw_face_gaps": jaw_gaps, "load_path_bounds_overlap": connections,
              "minimum_specimen_to_jaw_plane_clearance":jaw_clearance,
              "nonadjacent_triangle_overlaps":INTERSECTION_CACHE[signature],
              "upper_jaw_alignment_error": jaw_center_error, "geometry_sha256": signature,
              "upper_jaw_z": upper_jaw.location.z, "tip_columns": info['state']['tip'],
              "material_segment": segment}
    evaluated.to_mesh_clear()
    return result


def load_case(config_path, case_id):
    global CASE, STYLES, MESH_SPEC
    config = json.loads(Path(config_path).read_text())
    if config["generator_version"] != VERSION or config["fps"] != FPS or config["frames"] != NFRAMES:
        raise ValueError("configuration does not match this generator")
    matches = [c for c in config["cases"] if c["id"] == case_id]
    if len(matches) != 1:
        raise ValueError(f"expected one case for {case_id}")
    CASE, STYLES = matches[0], config["styles"]
    if CASE["kind"] not in ("brittle", "ductile") or not 0 <= CASE["event_frame"] < NFRAMES:
        raise ValueError("invalid kind or event frame")
    if not -0.8 <= CASE["fracture_s"] <= 0.8:
        raise ValueError("fracture outside the bounded author-defined gauge")
    if CASE["kind"] == "ductile" and not CASE.get("preloaded", False):
        if not 0 <= CASE["ramp_start_frame"] < CASE["event_frame"] - 1:
            raise ValueError("ductile ramp requires at least two visible frames")
    MESH_SPEC = {"width_gauge":CASE["gauge_width"], "width_grip":CASE["grip_width"],
                 "thickness":CASE["thickness"]}
    return CASE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).with_name('independent_batch_configs.json')))
    parser.add_argument("--case", required=True)
    parser.add_argument("--mode", choices=("preview", "render", "audit"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--frame-start", type=int, default=0)
    parser.add_argument("--frame-end", type=int, default=NFRAMES-1)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    case = load_case(args.config, args.case)
    kind, event = case['kind'], case['event_frame']
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    scene, obj, upper, initial = setup_scene(kind, out)
    if args.mode == "preview":
        frames = {0, event, 599}
        if event > 0:
            frames.add(event-1)
        if kind == 'ductile' and not case.get('preloaded', False):
            frames.add((case['ramp_start_frame'] + event - 1)//2)
        for frame in sorted(frames):
            set_state(kind, frame, obj, upper, initial)
            render_image(scene, out / f"{case['id']}_{frame:04d}.png")
            print("PREVIEW", case['id'], frame, flush=True)
    elif args.mode == "render":
        if list(out.glob(f"{case['id']}_*.png")):
            raise ValueError("render output already contains frames; use a new directory")
        if kind == 'brittle' or case.get('preloaded', False):
            frames = sorted({0,event})
            ramp = event
        else:
            ramp = case['ramp_start_frame']
            frames = [0] + list(range(ramp+1,event+1))
        for frame in sorted(set(frames)):
            set_state(kind, frame, obj, upper, initial)
            render_image(scene, out / f"{case['id']}_{frame:04d}.png")
            if frame % 30 == 0:
                print("RENDER", case['id'], frame, flush=True)
        for frame in range(NFRAMES):
            target = out / f"{case['id']}_{frame:04d}.png"
            if target.exists():
                continue
            source_frame = 0 if frame <= ramp else event
            source = out / f"{case['id']}_{source_frame:04d}.png"
            os.link(source, target)
    else:
        results = []
        info = set_state(kind, -1, obj, upper, initial)
        prehistory = actual_measures(kind, -1, obj, upper, info)
        for frame in range(args.frame_start, args.frame_end+1):
            info = set_state(kind, frame, obj, upper, initial)
            results.append(actual_measures(kind, frame, obj, upper, info))
            if frame % 100 == 0:
                print("AUDIT", case['id'], frame, flush=True)
        with open(out / f"{case['id']}_mesh_audit.json", "w") as handle:
            json.dump({"generator": VERSION, "case": case, "style":STYLES[case['style']],
                       "frame_numbering":"zero-based", "prehistory_frame_minus_one":prehistory,
                       "measurements":results}, handle, indent=2)
    print("FINISHED", case['id'], args.mode, flush=True)


if __name__ == "__main__":
    main()
