import os
import sys
import glob
import numpy as np
import networkx as nx
import cv2

# Project root = one level above this file (main/vein_graph.py)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main.process import clean_image
from main.skeleton import get_skeleton
from main.graph_utils import (
    build_graph,
    largest_component,
    simplify_graph,
    visualize_graph,
    compute_equation,
)

# ---- Centralised folder layout ----
# Change these if you rearrange the project again.
DIRS = {
    "images":      os.path.join(PROJECT_ROOT, "images"),
    "skeleton":    os.path.join(PROJECT_ROOT, "leaf-skeleton"),
    "overlay":     os.path.join(PROJECT_ROOT, "leaf-graph-overlay"),
    "clean":       os.path.join(PROJECT_ROOT, "leaf-graph-clean"),
    "nodes":       os.path.join(PROJECT_ROOT, "leaf-node"),
    "edges":       os.path.join(PROJECT_ROOT, "leaf-edges"),
}
IMAGE_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG")

MIN_AREA = 3        # min vein-component area in the cleaning step
MIN_BRANCH = 3      # skeleton spur-pruning length
MIN_LEAF_LEN = 25   # graph simplification: remove leaf branches shorter than this
DEFAULT_MAX_DIM = 1500
DEFAULT_THRESHOLDS = (3, 8, 12)


def _ensure_dirs():
    for key, path in DIRS.items():
        if key != "images":
            os.makedirs(path, exist_ok=True)


def _prepare_gray(image, max_dim):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    scale = max_dim / max(h, w)
    if scale < 1.0:
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)),
                          interpolation=cv2.INTER_AREA)
    return gray


def _candidate(gray, method, kernel_size, thr, min_area, min_branch):
    """Return (graph, skeleton, response) for one (method, threshold)."""
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                       (kernel_size, kernel_size))
    if method == "blackhat":
        resp = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    else:
        resp = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)

    _, thresholded = cv2.threshold(resp, thr, 255, cv2.THRESH_BINARY)
    cleaned = clean_image(thresholded, min_area=min_area)
    skeleton = get_skeleton(cleaned, min_branch=min_branch)
    if int(skeleton.sum()) < 30:
        return None, skeleton, resp
    graph = build_graph(skeleton)
    return graph, skeleton, resp


def _score(graph):
    comps = sorted(nx.connected_components(graph), key=len, reverse=True)
    if not comps:
        return 0.0, 0, 0
    big = len(comps[0])
    sub = graph.subgraph(comps[0])
    return big / max(graph.number_of_nodes(), 1), big, sub.number_of_edges()


def process_leaf(
    image_path,
    max_dim=DEFAULT_MAX_DIM,
    kernel=13,
    thresholds=DEFAULT_THRESHOLDS,
    min_area=MIN_AREA,
    min_branch=MIN_BRANCH,
    min_leaf_len=MIN_LEAF_LEN,
    save=True,
    verbose=True,
):
    """Build one connected vein graph from any leaf image.

    The pipeline tries both black-hat (dark veins) and white-hat (bright
    veins) responses over a few low thresholds, keeps the configuration
    whose graph is best connected, then returns the largest connected
    component as a single network.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    gray = _prepare_gray(image, max_dim)

    best = None
    for method in ("blackhat", "whitehat"):
        for thr in thresholds:
            graph, skeleton, _ = _candidate(gray, method, kernel, thr,
                                            min_area, min_branch)
            if graph is None or graph.number_of_nodes() == 0:
                continue
            score = _score(graph)
            if best is None or score > best["score"]:
                best = {
                    "method": method,
                    "thr": thr,
                    "graph": graph,
                    "skeleton": skeleton,
                    "score": score,
                }

    if best is None:
        raise RuntimeError("No vein structure detected in the image.")

    raw_graph = best["graph"]
    score_ratio, big_n, big_e = best["score"]

    # One connected network: largest connected component, then simplify it.
    graph = largest_component(raw_graph)
    graph = simplify_graph(graph, min_leaf_len=min_leaf_len)

    R, N, E, C, mu, L = compute_equation(graph)

    results = {
        "graph": graph,
        "skeleton": best["skeleton"],
        "image": gray,
        "method": best["method"],
        "threshold": best["thr"],
        "connectivity_ratio": score_ratio,
        "raw_nodes": raw_graph.number_of_nodes(),
        "raw_components": nx.number_connected_components(raw_graph),
        "N": N, "E": E, "C": C, "mu": mu, "L": L, "R": R,
    }

    if verbose:
        print(f"[{os.path.basename(image_path)}] method={best['method']} "
              f"thr={best['thr']} connectivity={score_ratio:.2f}")
        print(f"  raw: N={raw_graph.number_of_nodes()} "
              f"E={raw_graph.number_of_edges()}")
        print(f"  network: N={N} E={E} C={C} mu={mu} L={L} R={R}")

    if save:
        _save_outputs(image_path, gray, best, graph, results)

    return results


def _save_outputs(image_path, gray, best, graph, results):
    _ensure_dirs()
    stem = os.path.splitext(os.path.basename(image_path))[0]

    skel_path = os.path.join(DIRS["skeleton"], f"{stem}_skeleton.png")
    cv2.imwrite(skel_path, (best["skeleton"].astype(np.uint8)) * 255)

    overlay_path = os.path.join(DIRS["overlay"], f"{stem}_graph_overlay.jpg")
    visualize_graph(graph, overlay_path, background=gray)

    clean_path = os.path.join(DIRS["clean"], f"{stem}_graph_clean.png")
    visualize_graph(graph, clean_path, background=None)

    _export_csvs(graph, stem)

    results["skeleton_path"] = skel_path
    results["overlay_path"] = overlay_path
    results["clean_path"] = clean_path


def _export_csvs(graph, stem):
    import csv

    nodes_path = os.path.join(DIRS["nodes"], f"{stem}_nodes.csv")
    with open(nodes_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["index", "x", "y", "degree"])
        for n in graph.nodes():
            y, x = graph.nodes[n]["o"]
            writer.writerow([n, int(round(float(x))), int(round(float(y))),
                             int(graph.degree(n))])

    edges_path = os.path.join(DIRS["edges"], f"{stem}_edges.csv")
    with open(edges_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["source", "target", "length"])
        for s, e, d in graph.edges(data=True):
            writer.writerow([s, e, round(float(d["weight"]), 2)])


def process_all(suffix_filter=None, **kwargs):
    """Process every image currently in the images/ folder."""
    _ensure_dirs()
    paths = []
    for ext in IMAGE_EXTENSIONS:
        paths.extend(glob.glob(os.path.join(DIRS["images"], ext)))
    paths = sorted(set(paths))
    if not paths:
        print("No images found in", DIRS["images"])
        return []
    results = []
    for path in paths:
        results.append(process_leaf(path, **kwargs))
    return results