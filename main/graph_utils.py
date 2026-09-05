import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import networkx as nx
import sknw


def build_graph(skeleton):
    # White/True pixels are the leaf veins
    return sknw.build_sknw(skeleton.astype(np.uint16))


def largest_component(graph):
    import networkx as nx
    comps = max(nx.connected_components(graph), key=len)
    return graph.subgraph(comps).copy()


def simplify_graph(graph, min_leaf_len=25):
    # 1. Remove short leaf (degree-1) branches that are spurs.
    # 2. Merge degree-2 pass-through nodes into single edges.
    g = graph.copy()

    changed = True
    while changed:
        changed = False
        for node in list(g.nodes()):
            if node not in g or g.degree(node) != 1:
                continue
            nbr = next(iter(g.neighbors(node)))
            if g[node][nbr]["weight"] < min_leaf_len:
                g.remove_node(node)
                changed = True

    changed = True
    while changed:
        changed = False
        for node in list(g.nodes()):
            if node not in g or g.degree(node) != 2:
                continue
            a, b = list(g.neighbors(node))
            p1 = g[a][node]["pts"]
            p2 = g[b][node]["pts"]
            # orient p1 so it ends at the shared node 'node' (= p2's start)
            if np.linalg.norm(p1[0] - p2[0]) < np.linalg.norm(p1[-1] - p2[0]):
                p1 = p1[::-1]
            joined = np.vstack([p1, p2[1:]])
            w = g[a][node]["weight"] + g[b][node]["weight"]
            g.remove_node(node)
            if not g.has_edge(a, b):
                g.add_edge(a, b, pts=joined, weight=w)
            changed = True
            break
    return g


def node_type(n, graph):
    # 1 = endpoint/leaf, 2 = pass-through, 3+ = junction
    return int(graph.degree(n))


def visualize_graph(graph, output_path="leaf_node_edge_graph.jpg",
                    background=None, dpi=150):

    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(111)

    pts_by_edge = [graph[s][e]["pts"][:, ::-1] for s, e in graph.edges()]

    if background is not None:
        ax.imshow(background, cmap="gray", zorder=0)
    else:
        ax.set_facecolor("white")

    if pts_by_edge:
        lc = LineCollection(pts_by_edge, linewidths=1.2, colors="red", zorder=2)
        ax.add_collection(lc)

    xs = np.array([graph.nodes[n]["o"][1] for n in graph.nodes()])
    ys = np.array([graph.nodes[n]["o"][0] for n in graph.nodes()])
    ax.scatter(xs, ys, s=8, c="blue", zorder=3, edgecolors="none")

    ax.invert_yaxis()
    ax.autoscale()
    ax.axis("off")

    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def compute_equation(graph):

    N = graph.number_of_nodes()
    E = graph.number_of_edges()
    C = nx.number_connected_components(graph)

    mu = max(E - N + C, 1)

    L = 0

    for _, _, data in graph.edges(data=True):

        pts = data["pts"].astype(float)

        d = np.diff(pts, axis=0)
        L += float(np.linalg.norm(d, axis=1).sum())

    L = int(L)

    R = (N + E) * mu + L

    return R, N, E, C, mu, L