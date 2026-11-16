#!/usr/bin/env python3
"""Measure an author-defined material segment from each evaluated mesh.

Use Blender with --kind and --out after --.  The first and last segment rings
are closed temporarily for the volume integral; the rendered object is not
modified.  The segment is defined in material coordinates, not as a claim of
a standards-compliant experimental gauge length.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import independent_fracture as gen


def signed_triangle(a, b, c):
    return a.dot(b.cross(c)) / 6.0


def segment_measurements(obj, info):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    lo_i, hi_i = 12, 52  # material coordinates -1.0625 to +1.0625
    levels, layers = info["levels"], info["layers"]
    selected = set()
    for low, high in layers[lo_i:hi_i + 1]:
        selected.update(low.values())
        selected.update(high.values())
    for low, high, _j, _k in info["seam_pairs"]:
        selected.update((low, high))
    volume = 0.0
    for tri in mesh.loop_triangles:
        if all(i in selected for i in tri.vertices):
            a, b, c = (mesh.vertices[i].co for i in tri.vertices)
            volume += signed_triangle(a, b, c)
    for layer, reverse in ((layers[lo_i][0], True), (layers[hi_i][1], False)):
        order = list(reversed(gen.PERIMETER)) if reverse else gen.PERIMETER
        coords = [mesh.vertices[layer[key]].co for key in order]
        for i in range(1, len(coords) - 1):
            volume += signed_triangle(coords[0], coords[i], coords[i+1])
    low_points = [mesh.vertices[i].co for i in layers[lo_i][0].values()]
    high_points = [mesh.vertices[i].co for i in layers[hi_i][1].values()]
    length = (sum(v.z for v in high_points) / len(high_points)
              - sum(v.z for v in low_points) / len(low_points))
    # Follow one consistent material path on the front surface. The transition
    # from the lower to the upper crack rim is deliberately excluded, so an
    # open gap is never counted as specimen material length.
    path_length = 0.0
    path_key = (gen.N_X // 2, 0)
    for i in range(lo_i, hi_i):
        start = mesh.vertices[layers[i][1][path_key]].co
        end = mesh.vertices[layers[i+1][0][path_key]].co
        path_length += (end - start).length
    middle_low = mesh.vertices[layers[gen.N_Z//2][0][path_key]].co
    middle_high = mesh.vertices[layers[gen.N_Z//2][1][path_key]].co
    centerline_gap_z = middle_high.z - middle_low.z
    center = layers[gen.N_Z // 2][0]
    width = mesh.vertices[center[(gen.N_X, 0)]].co.x - mesh.vertices[center[(0, 0)]].co.x
    thickness = (mesh.vertices[center[(gen.N_X//2, gen.N_Y)]].co.y
                 - mesh.vertices[center[(gen.N_X//2, 0)]].co.y)
    evaluated.to_mesh_clear()
    return {"material_segment_s": [levels[lo_i], levels[hi_i]],
            "boundary_span_z_including_gap": length, "front_surface_material_path_length": path_length,
            "front_surface_centerline_gap_z": centerline_gap_z, "segment_volume": abs(volume),
            "cross_section_width": width, "cross_section_thickness": thickness,
            "cross_section_area": width * thickness}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--kind", required=True, choices=("brittle", "ductile"))
    p.add_argument("--out", required=True)
    a = p.parse_args(sys.argv[sys.argv.index("--") + 1:])
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    _scene, obj, upper, initial = gen.setup_scene(a.kind, out)
    measurements = []
    for frame in range(gen.NFRAMES):
        info = gen.set_state(a.kind, frame, obj, upper, initial)
        data = segment_measurements(obj, info)
        data["frame"] = frame
        measurements.append(data)
        if frame % 100 == 0:
            print("GAUGE", a.kind, frame, flush=True)
    result = {"generator": gen.VERSION, "scope": "author-defined material segment; evaluated mesh",
              "frame_numbering": "zero-based", "measurements": measurements}
    (out / (a.kind + "_gauge_audit.json")).write_text(json.dumps(result, indent=2))
    print("FINISHED GAUGE", a.kind, flush=True)


if __name__ == "__main__":
    main()
