"""Small crystallography utilities aligned with Cayron-style questions.

This is not a replacement for MTEX/ARPGE/GenOVa. It provides transparent,
inspectable matrix and misorientation tools for dashboards and teaching.
"""
from __future__ import annotations
import itertools
import math
import numpy as np


def normalize_rotation(R: np.ndarray) -> np.ndarray:
    """Project a noisy 3x3 matrix to the nearest proper rotation matrix."""
    U, _, Vt = np.linalg.svd(np.asarray(R, dtype=float))
    M = U @ Vt
    if np.linalg.det(M) < 0:
        U[:, -1] *= -1
        M = U @ Vt
    return M


def axis_angle_from_rotation(R: np.ndarray) -> tuple[float, np.ndarray]:
    """Return misorientation angle in degrees and unit axis."""
    R = normalize_rotation(R)
    c = (np.trace(R) - 1.0) / 2.0
    c = float(np.clip(c, -1.0, 1.0))
    angle = math.degrees(math.acos(c))
    if abs(angle) < 1e-8:
        return 0.0, np.array([0.0, 0.0, 1.0])
    axis = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    axis = axis / (2 * math.sin(math.radians(angle)))
    n = np.linalg.norm(axis)
    if n > 0:
        axis = axis / n
    return angle, axis


def cubic_symmetry_operators() -> list[np.ndarray]:
    """24 proper rotation matrices of the cubic point group."""
    ops = []
    for perm in itertools.permutations(range(3)):
        P = np.zeros((3, 3))
        for i, j in enumerate(perm):
            P[i, j] = 1
        for signs in itertools.product([-1, 1], repeat=3):
            S = np.diag(signs)
            M = S @ P
            if round(np.linalg.det(M)) == 1:
                ops.append(M.astype(float))
    # unique
    unique = []
    for op in ops:
        if not any(np.allclose(op, u) for u in unique):
            unique.append(op)
    return unique


def misorientation(g1: np.ndarray, g2: np.ndarray, symmetry: str = "cubic") -> dict:
    """Minimum misorientation between two orientation matrices.

    g1 and g2 map crystal to sample frame. Cubic symmetry is applied by default.
    """
    g1 = normalize_rotation(g1)
    g2 = normalize_rotation(g2)
    ops = cubic_symmetry_operators() if symmetry.lower() == "cubic" else [np.eye(3)]
    best = None
    for S1 in ops:
        for S2 in ops:
            delta = S1 @ g1 @ np.linalg.inv(g2) @ np.linalg.inv(S2)
            angle, axis = axis_angle_from_rotation(delta)
            if best is None or angle < best["angle_deg"]:
                best = {"angle_deg": angle, "axis": axis, "delta": delta}
    return best


def generate_variants(parent_symmetry_ops: list[np.ndarray], correspondence: np.ndarray, orientation_relationship: np.ndarray | None = None, tol: float = 1e-6) -> list[np.ndarray]:
    """Generate orientational variants from parent symmetry and a correspondence/orientation operator.

    In Cayron-style notation this is a simplified variant generator: variants are
    parent symmetry operators composed with the transformation operator.
    """
    C = np.asarray(correspondence, dtype=float)
    OR = np.eye(3) if orientation_relationship is None else np.asarray(orientation_relationship, dtype=float)
    variants = []
    for S in parent_symmetry_ops:
        V = normalize_rotation(S @ OR @ C)
        if not any(np.linalg.norm(V - W) < tol for W in variants):
            variants.append(V)
    return variants


def parse_matrix(text: str) -> np.ndarray:
    """Parse a 3x3 matrix from text with rows separated by ';' or new lines."""
    rows = [r.strip() for r in text.replace("[", "").replace("]", "").split(";") if r.strip()]
    if len(rows) == 1:
        rows = [r.strip() for r in text.strip().splitlines() if r.strip()]
    data = []
    for row in rows:
        nums = [float(x) for x in row.replace(",", " ").split()]
        data.append(nums)
    arr = np.array(data, dtype=float)
    if arr.shape != (3, 3):
        raise ValueError(f"Expected 3x3 matrix, got {arr.shape}")
    return arr


def matrix_to_markdown(M: np.ndarray, precision: int = 4) -> str:
    rows = []
    for row in M:
        rows.append("| " + " | ".join(f"{x:.{precision}f}" for x in row) + " |")
    return "\n".join(["| c1 | c2 | c3 |", "|---:|---:|---:|"] + rows)
