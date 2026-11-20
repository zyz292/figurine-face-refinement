"""Blend one eye patch into a quadratic fitted to labelled healthy skin."""
import argparse
import heapq
import math
from pathlib import Path
import sys

import bpy
import numpy as np


def members(mesh, group):
    return {v.index: g.weight for v in mesh.vertices for g in v.groups
            if g.group == group.index and g.weight > 0}


def distances_to_border(mesh, editable, xyz):
    # Dijkstra in local length units also works on nonuniform triangulations.
    edges = np.empty(len(mesh.edges) * 2, dtype=np.int32)
    mesh.edges.foreach_get("vertices", edges)
    edges = edges.reshape(-1, 2)
    mask = np.zeros(len(xyz), dtype=bool)
    mask[list(editable)] = True
    local = edges[mask[edges].any(axis=1)]
    graph = {i: [] for i in editable}
    dist = {i: math.inf for i in editable}
    for a, b in local:
        if mask[a] and mask[b]:
            length = np.linalg.norm(xyz[a] - xyz[b])
            graph[a].append((b, length))
            graph[b].append((a, length))
        else:
            dist[a if mask[a] else b] = 0.0
    # A second island may be an overlapping hair strand or an independent eye.
    stack = [editable[0]]
    visited = set(stack)
    while stack:
        i = stack.pop()
        for j, _ in graph[i]:
            if j not in visited:
                visited.add(j)
                stack.append(j)
    if len(visited) != len(editable):
        raise ValueError("Editable skin must be one connected patch; inspect the mask and separate layers.")
    queue = [(0., i) for i, d in dist.items() if d == 0.]
    heapq.heapify(queue)
    while queue:
        d, i = heapq.heappop(queue)
        if d != dist[i]:
            continue
        for j, length in graph[i]:
            if d + length < dist[j]:
                dist[j] = d + length
                heapq.heappush(queue, (dist[j], j))
    values = np.array(list(dist.values()))
    if not len(values) or not np.isfinite(values).all() or max(values) <= 0:
        raise ValueError("Patch needs a boundary with fixed surrounding skin and interior vertices.")
    return values


def basis(uv):
    u, v = uv.T
    return np.column_stack((np.ones(len(u)), u, v, u*u, u*v, v*v))


def preview(path, edit, ring, keep):
    uv = np.vstack((edit, ring))
    center = (uv.max(axis=0) + uv.min(axis=0)) / 2
    factor = 680 / max(np.ptp(uv, axis=0))
    items = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800">',
             '<rect width="800" height="800" fill="#17202c"/>']
    for group, color in [(ring, "#66bfff"), (edit, "#79e09c"), (keep, "#ffae6c")]:
        # Keep dense selections manageable. Protected points outside the ROI are irrelevant.
        pts = (group - center) * factor
        pts = pts[(np.abs(pts) <= 372).all(axis=1)]
        pts = np.unique(np.round(pts / 2).astype(int), axis=0)*2
        for x, y in pts:
            items.append(f'<circle cx="{400+x}" cy="{395-y}" r="2" fill="{color}"/>')
    items.append('<text x="25" y="785" fill="white" font-size="17">Local projection: green edit / blue reference / orange protected</text></svg>')
    with path.open("x", encoding="utf-8") as f:
        f.write("\n".join(items))


def main():
    p = argparse.ArgumentParser()
    for flag in ("object", "edit", "reference", "protect"):
        p.add_argument("--"+flag, required=True)
    out = p.add_mutually_exclusive_group(required=True)
    out.add_argument("--output", type=Path)
    out.add_argument("--preview", type=Path)
    p.add_argument("--strength", type=float, default=1.)
    p.add_argument("--feather", type=float, default=.45,
                   help="Transition width as a fraction of maximum inward boundary distance.")
    a = p.parse_args(sys.argv[sys.argv.index("--")+1:])
    dest = (a.output or a.preview).resolve()
    if dest.exists() or not dest.parent.is_dir():
        raise ValueError("Choose a new output path in an existing directory.")
    if a.output and dest.suffix.lower() != ".blend":
        raise ValueError("Output must end in .blend")
    if not 0 < a.strength <= 1 or not 0 < a.feather <= 1:
        raise ValueError("strength and feather must be in (0, 1].")
    obj = bpy.data.objects.get(a.object)
    if obj is None or obj.type != "MESH" or obj.mode != "OBJECT":
        raise ValueError("Select a mesh in Object mode.")
    mesh = obj.data
    edit, ring, keep = [members(mesh, obj.vertex_groups[name])
                        for name in (a.edit, a.reference, a.protect)]
    if set(edit) & set(ring):
        raise ValueError("Edit and reference groups must be disjoint.")
    ids = [i for i in edit if i not in keep]
    refs = list(ring)
    if not ids or len(refs) < 6:
        raise ValueError("Provide editable skin and a surrounding ring of healthy samples.")
    xyz = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", xyz)
    xyz = xyz.reshape(-1, 3)
    points = xyz[refs].astype(float)
    center = points.mean(axis=0)
    _, singular, axes = np.linalg.svd(points-center, full_matrices=False)
    if singular[1] <= 1e-5*singular[0] or not singular[0]:
        raise ValueError("Reference skin should surround the patch on two axes.")
    def project(indices):
        return (xyz[indices]-center) @ axes.T
    ref = project(refs)
    patch = project(ids)
    if a.preview:
        preview(dest, patch[:, :2], ref[:, :2], project(list(keep))[:, :2])
        return
    if mesh.shape_keys or obj.library or mesh.library:
        raise ValueError("Use a local mesh without shape keys for this tool.")
    radius = np.linalg.norm(ref[:, :2], axis=1).max()
    matrix = basis(ref[:, :2] / radius)
    coeff, _, rank, values = np.linalg.lstsq(matrix, ref[:, 2], rcond=None)
    if rank != 6 or values[-1] < values[0]*1e-5:
        raise ValueError("Reference group needs a band with width and varied radial distances.")
    # Check the sampled support in multiple directions before allowing extrapolation.
    for angle in np.linspace(0, np.pi, 24, endpoint=False):
        direction = np.array([np.cos(angle), np.sin(angle)])
        r = ref[:,:2] @ direction
        e = patch[:,:2] @ direction
        if e.min() < r.min() - .02*radius or e.max() > r.max() + .02*radius:
            raise ValueError("Reference skin must wrap around the editable patch.")
    dist = distances_to_border(mesh, ids, xyz)
    t = np.clip(dist / (max(dist)*a.feather), 0., 1.)
    weight = t*t*(3-2*t) * a.strength * np.array([edit[i] for i in ids])
    depth = (basis(patch[:,:2]/radius) @ coeff - patch[:,2])*weight
    if mesh.users > 1:
        obj.data = mesh.copy()
        mesh = obj.data
    xyz[ids] += (depth[:, None]*axes[2]).astype(np.float32)
    mesh.vertices.foreach_set("co", xyz.ravel())
    mesh.update()
    result = bpy.ops.wm.save_as_mainfile(filepath=str(dest), copy=True)
    if "FINISHED" not in result:
        raise RuntimeError("Blender could not save the repaired copy.")
    print(f"Edited {np.count_nonzero(depth)} vertices; peak local displacement {max(abs(depth)):.6g}")


if __name__ == "__main__":
    main()
