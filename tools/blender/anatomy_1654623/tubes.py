"""Smooth tubes along centrelines (numpy only; no bpy).

`catmull_rom` is a port of `smooth_path` in app/micro/geometry.py of Layered Human / AnatomyExplorer
(https://github.com/ethanprince4/AnatomyExplorer, Copyright (c) 2026 Ethan Prince, MIT licence; the full
notice is in lh_hepatobiliary.py). The ported centrelines are drawn through the same spline the source
uses, and the radius profiles are interpolated linearly along the normalised arc length, as its taper()
does. The sweep, the parallel-transport frames and the end caps are SurgeryCraft code (MIT).
"""
from __future__ import annotations

import numpy as np


def catmull_rom(points, samples: int = 60) -> np.ndarray:
    """Catmull-Rom spline through the control points (same construction as Layered Human smooth_path)."""
    pts = np.asarray(points, dtype=np.float64)
    if len(pts) < 3:
        return np.linspace(pts[0], pts[-1], samples)
    p = np.vstack([pts[0] * 2 - pts[1], pts, pts[-1] * 2 - pts[-2]])
    out = []
    segs = len(pts) - 1
    per = max(2, samples // segs)
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return np.array(out)


def resample(path, spacing: float) -> np.ndarray:
    """Points at (about) equal arc-length spacing along a polyline."""
    path = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(int(arc[-1] / spacing) + 1, 3)
    s = np.linspace(0.0, arc[-1], n)
    return np.stack([np.interp(s, arc, path[:, c]) for c in range(3)], -1)


def spline(ctrl, spacing: float) -> np.ndarray:
    """Dense centreline through the control points: the spline the source uses, resampled."""
    ctrl = np.asarray(ctrl, float)
    return resample(catmull_rom(ctrl, max(len(ctrl) * 30, 60)), spacing)


def arc_length(path) -> np.ndarray:
    seg = np.linalg.norm(np.diff(np.asarray(path, float), axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(seg)])


def frames(path):
    """Tangents and parallel-transport normals/binormals along a path."""
    path = np.asarray(path, float)
    t = np.gradient(path, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
    ref = np.array([0.0, 0.0, 1.0]) if abs(t[0][2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    n = np.cross(t[0], ref)
    n /= np.linalg.norm(n)
    normals = [n]
    for i in range(1, len(path)):
        # project the previous normal onto the plane normal to the new tangent (parallel transport)
        n = normals[-1] - np.dot(normals[-1], t[i]) * t[i]
        ln = np.linalg.norm(n)
        normals.append(n / ln if ln > 1e-12 else normals[-1])
    normals = np.array(normals)
    binormals = np.cross(t, normals)
    return t, normals, binormals


def radius_profile(radius, u) -> np.ndarray:
    """Radius at normalised arc length u: a number, or a list interpolated linearly (taper())."""
    u = np.asarray(u, float)
    if isinstance(radius, (int, float)):
        return np.full(u.shape, float(radius))
    vals = np.asarray(radius, float)
    return np.interp(u, np.linspace(0.0, 1.0, len(vals)), vals)


def tube(ctrl, radius, n_theta: int = 20, spacing: float = 0.0015, cap_rings: int = 4):
    """A closed tube (vertices, faces) along the spline through `ctrl`, rounded caps at both ends.

    Faces are quads (and triangles at the cap poles), outward-oriented.
    """
    path = spline(ctrl, spacing)
    s = arc_length(path)
    rad = radius_profile(radius, s / s[-1])
    t, nrm, bnr = frames(path)
    ang = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    ca, sa = np.cos(ang), np.sin(ang)
    rings = []
    # start cap (hemisphere behind the first point)
    for k in range(cap_rings, 0, -1):
        phi = (np.pi / 2) * k / (cap_rings + 1)
        c = path[0] - t[0] * rad[0] * np.sin(phi)
        rr = rad[0] * np.cos(phi)
        rings.append(c + rr * (np.outer(ca, nrm[0]) + np.outer(sa, bnr[0])))
    for i in range(len(path)):
        rings.append(path[i] + rad[i] * (np.outer(ca, nrm[i]) + np.outer(sa, bnr[i])))
    for k in range(1, cap_rings + 1):
        phi = (np.pi / 2) * k / (cap_rings + 1)
        c = path[-1] + t[-1] * rad[-1] * np.sin(phi)
        rr = rad[-1] * np.cos(phi)
        rings.append(c + rr * (np.outer(ca, nrm[-1]) + np.outer(sa, bnr[-1])))
    verts = np.vstack(rings)
    nr = len(rings)
    faces = []
    for j in range(nr - 1):
        for i in range(n_theta):
            a = j * n_theta + i
            b = j * n_theta + (i + 1) % n_theta
            faces.append((a, a + n_theta, b + n_theta, b))
    pole0 = len(verts)
    pole1 = pole0 + 1
    verts = np.vstack([verts, path[0] - t[0] * rad[0], path[-1] + t[-1] * rad[-1]])
    for i in range(n_theta):
        faces.append((pole0, i, (i + 1) % n_theta))
        base = (nr - 1) * n_theta
        faces.append((pole1, base + (i + 1) % n_theta, base + i))
    # orientation: make the faces point outwards (check one face against the centreline)
    f = faces[len(faces) // 4]
    p = verts[list(f)]
    fn = np.cross(p[1] - p[0], p[2] - p[0])
    centre = path[np.argmin(np.linalg.norm(path - p.mean(0), axis=1))]
    if np.dot(fn, p.mean(0) - centre) < 0:
        faces = [tuple(reversed(f)) for f in faces]
    return verts, faces, path, rad
