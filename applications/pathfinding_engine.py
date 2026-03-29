#!/usr/bin/env python3
"""
Serie I · Pathfinding Spectral Engine
=======================================
Same architecture as geometric_engine.py, applied to
graph pathfinding via spectral coordinates and effective resistance.

Builds on graph_engine.py: imports Graph, GG, graph_features.
Adds pathfinding-specific features on top of the 29 graph features.

Input:  Graph (adjacency matrix) + source/target pair
Output: 29 features for algorithm recommendation

Channels:
  Canal B = spectral distance structure (eigenvalue-weighted geometry)
  Canal A = effective resistance (electrical analogy)
  Cross   = BFS vs spectral heuristic comparison

The motor doesn't know it's doing pathfinding.
It sees a spectrum and extracts geometry.

Copyright (c) 2026 Ricardo Hernández Reveles
SPDX-License-Identifier: AGPL-3.0-or-later
"""
import numpy as np
from numpy.linalg import eigh
import time
import sys
import os

# Import from graph_engine (must be in same directory or on path)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graph_engine import Graph, GG, graph_features, FNAMES as GRAPH_FNAMES


# ═══════════════════════════════════════════════════════════════
# MODULE 1: SPECTRAL COORDINATES AND DISTANCES
# ═══════════════════════════════════════════════════════════════

def spectral_coordinates(G, k=5):
    """
    Embed graph nodes in R^k using first k non-trivial eigenvectors
    of the Laplacian.

    Returns
    -------
    coords : ndarray, shape (N, k), spectral coordinates
    """
    evals = G.spectrum()
    k_eff = min(k, G.N - 1)
    coords = np.zeros((G.N, k_eff))
    for i in range(k_eff):
        coords[:, i] = G.eigenvector(i + 1)  # skip trivial eigenvector 0
    return coords


def spectral_distance_matrix(G, k=5):
    """
    Pairwise Euclidean distances in spectral embedding space.
    """
    coords = spectral_coordinates(G, k)
    N = G.N
    D = np.zeros((N, N))
    for i in range(N):
        for j in range(i + 1, N):
            d = np.linalg.norm(coords[i] - coords[j])
            D[i, j] = D[j, i] = d
    return D


def effective_resistance(G):
    """
    Effective resistance between all pairs using pseudoinverse of Laplacian.

    R_ij = L^+_ii + L^+_jj - 2·L^+_ij

    Returns
    -------
    R : ndarray, shape (N, N), effective resistance matrix
    """
    evals = G.spectrum()
    N = G.N
    # Pseudoinverse of L: L^+ = Σ (1/λ_k) v_k v_k^T for λ_k > 0
    L_pinv = np.zeros((N, N))
    for i in range(N):
        if evals[i] > 1e-10:
            vi = G.eigenvector(i)
            L_pinv += np.outer(vi, vi) / evals[i]

    R = np.zeros((N, N))
    diag = np.diag(L_pinv)
    for i in range(N):
        for j in range(i + 1, N):
            r = diag[i] + diag[j] - 2 * L_pinv[i, j]
            R[i, j] = R[j, i] = max(r, 0.0)
    return R


def bfs_distance(G, source):
    """
    BFS shortest path distances from source.
    Returns array of distances (-1 for unreachable).
    """
    N = G.N
    dist = np.full(N, -1)
    dist[source] = 0
    queue = [source]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        for v in range(N):
            if G.A[u, v] > 0 and dist[v] < 0:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


# ═══════════════════════════════════════════════════════════════
# MODULE 2: 29-FEATURE EXTRACTION
# ═══════════════════════════════════════════════════════════════

FEATURE_NAMES = [
    # Graph topology (7)
    'N', 'E', 'density', 'algebraic_conn', 'spectral_gap_norm',
    'degree_CV', 'n_components',
    # Spectral distance structure (6)
    'spec_dist_mean', 'spec_dist_std', 'spec_dist_max',
    'spec_dist_CV', 'spec_diameter_ratio', 'spec_embed_dim',
    # Effective resistance (5)
    'eff_res_mean', 'eff_res_max', 'eff_res_CV',
    'kirchhoff_index', 'res_diameter_ratio',
    # BFS vs spectral comparison (5)
    'heuristic_ratio_mean', 'heuristic_ratio_std', 'heuristic_rank_corr',
    'bfs_diameter', 'bfs_avg_path',
    # Algorithm recommendation features (4)
    'hub_dominance', 'partition_balance', 'bottleneck_score',
    'regularity_index',
    # Summary (2)
    'recommended_algo_id', 'heuristic_quality',
]

# Algorithm IDs for recommendation
ALGO_IDS = {
    'BFS': 0.0,
    'ROUTE_HUBS': 1.0,
    'BRIDGE_FIRST': 2.0,
    'A_STAR_SPECTRAL': 3.0,
}


def pathfinding_features(G, k_embed=5):
    """
    Extract 29 pathfinding-specific spectral features from a graph.

    Parameters
    ----------
    G : Graph instance
    k_embed : int, spectral embedding dimension

    Returns
    -------
    vec : ndarray, shape (29,)
    """
    N = G.N
    if N < 3:
        return np.zeros(29, dtype=np.float64)

    # Base graph features (for topology subset)
    gf = graph_features(G)

    # 1-7: Graph topology from graph_features
    alg_conn = gf[0]       # algebraic connectivity
    gap_norm = gf[2]       # gap / mean_degree
    degree_cv = gf[4]      # degree CV
    n_comp = gf[1]         # components
    density = gf[6]
    n_edges = gf[21]

    # 8-13: Spectral distance structure
    k_eff = min(k_embed, N - 1)
    spec_D = spectral_distance_matrix(G, k_eff)
    # Upper triangle only (exclude diagonal)
    triu_idx = np.triu_indices(N, k=1)
    spec_dists = spec_D[triu_idx]

    if len(spec_dists) > 0 and spec_dists.max() > 1e-15:
        sd_mean = spec_dists.mean()
        sd_std = spec_dists.std()
        sd_max = spec_dists.max()
        sd_cv = sd_std / (sd_mean + 1e-15)
    else:
        sd_mean = sd_std = sd_max = sd_cv = 0.0

    # BFS diameter for comparison
    bfs_dists_all = []
    # Sample a few sources for efficiency
    sources = list(range(min(N, 10)))
    for s in sources:
        d = bfs_distance(G, s)
        reachable = d[d >= 0]
        bfs_dists_all.extend(reachable.tolist())

    bfs_arr = np.array(bfs_dists_all)
    bfs_diam = float(bfs_arr.max()) if len(bfs_arr) > 0 else 0.0
    bfs_avg = float(bfs_arr[bfs_arr > 0].mean()) if np.sum(bfs_arr > 0) > 0 else 0.0

    # Spectral diameter ratio: spectral_max / BFS_diameter
    spec_diam_ratio = sd_max / (bfs_diam + 1e-15)

    # Effective embedding dimension: how many eigenvalues matter
    evals = G.spectrum()
    pos_evals = evals[evals > 1e-10]
    if len(pos_evals) > 1:
        # Participation ratio of eigenvalues
        e_norm = pos_evals / pos_evals.sum()
        eff_dim = float(1.0 / np.sum(e_norm ** 2))
    else:
        eff_dim = 1.0

    # 14-18: Effective resistance
    R = effective_resistance(G)
    res_dists = R[triu_idx]
    if len(res_dists) > 0 and res_dists.max() > 1e-15:
        er_mean = res_dists.mean()
        er_max = res_dists.max()
        er_cv = res_dists.std() / (er_mean + 1e-15)
    else:
        er_mean = er_max = er_cv = 0.0

    # Kirchhoff index: sum of all effective resistances
    kirchhoff = float(res_dists.sum())

    # Resistance diameter ratio
    res_diam_ratio = er_max / (bfs_diam + 1e-15)

    # 19-23: BFS vs spectral heuristic comparison
    # For sampled node pairs, compare spectral distance to BFS distance
    ratios = []
    bfs_vs_spec = []
    for s in sources:
        bfs_d = bfs_distance(G, s)
        for t in range(N):
            if t != s and bfs_d[t] > 0:
                spec_d = spec_D[s, t]
                ratio = spec_d / (bfs_d[t] + 1e-15)
                ratios.append(ratio)
                bfs_vs_spec.append((bfs_d[t], spec_d))

    if ratios:
        hr_mean = np.mean(ratios)
        hr_std = np.std(ratios)
        # Rank correlation: how well does spectral distance preserve BFS ranking?
        bfs_ranks = np.argsort(np.argsort([x[0] for x in bfs_vs_spec]))
        spec_ranks = np.argsort(np.argsort([x[1] for x in bfs_vs_spec]))
        if len(bfs_ranks) > 2:
            rank_corr = float(np.corrcoef(bfs_ranks, spec_ranks)[0, 1])
            if not np.isfinite(rank_corr):
                rank_corr = 0.0
        else:
            rank_corr = 0.0
    else:
        hr_mean = hr_std = rank_corr = 0.0

    # 24-27: Algorithm recommendation features
    hub_dom = gf[26]       # hub dominance
    part_bal = gf[13]      # partition balance

    # Bottleneck score: max eigengap (indicates bottleneck structure)
    bottleneck = gf[16]    # max eigengap

    # Regularity index
    reg_index = 1.0 / (1.0 + degree_cv)

    # 28-29: Algorithm recommendation
    # Thresholds calibrated from synthetic graph diagnostics:
    #   grid:       gap=0.027, cv=0.16, hub=0.46, bottle=0.28, reg=0.86
    #   ER:         gap=0.246, cv=0.26, hub=0.62, bottle=1.40, reg=0.79
    #   bottleneck: gap=0.033, cv=0.27, hub=0.63, bottle=2.28, reg=0.79
    #   BA:         gap=0.159, cv=1.00, hub=0.35, bottle=0.07, reg=0.50
    #   path:       gap=0.002, cv=0.10, hub=0.64, bottle=0.07, reg=0.91
    if bottleneck > 1.0 and gap_norm < 0.1:
        algo = 'BRIDGE_FIRST'
    elif gap_norm > 0.15 and degree_cv < 0.5:
        algo = 'BFS'
    elif degree_cv > 0.8:
        algo = 'ROUTE_HUBS'
    elif reg_index > 0.8 and gap_norm < 0.05:
        algo = 'A_STAR_SPECTRAL'
    else:
        algo = 'A_STAR_SPECTRAL'

    algo_id = ALGO_IDS[algo]
    heuristic_quality = rank_corr  # how reliable is spectral as A* heuristic

    vec = np.array([
        float(N), float(n_edges), density, alg_conn, gap_norm,
        degree_cv, float(n_comp),
        sd_mean, sd_std, sd_max, sd_cv, spec_diam_ratio, eff_dim,
        er_mean, er_max, er_cv, kirchhoff, res_diam_ratio,
        hr_mean, hr_std, rank_corr, bfs_diam, bfs_avg,
        hub_dom, part_bal, bottleneck, reg_index,
        algo_id, heuristic_quality,
    ], dtype=np.float64)

    return vec


# ═══════════════════════════════════════════════════════════════
# MODULE 3: SYNTHETIC GRAPH GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_graph(kind, seed=42):
    """
    Generate synthetic graphs for pathfinding testing.

    Kinds: grid, erdos_renyi, bottleneck, barabasi_albert, path
    """
    if kind == 'grid':
        return GG.grid_2d(10, 10)

    elif kind == 'erdos_renyi':
        return GG.erdos_renyi(100, 0.1, seed=seed)

    elif kind == 'bottleneck':
        # Two dense clusters connected by a single bridge
        return GG.stochastic_block([50, 50], pw=0.2, pb=0.005, seed=seed)

    elif kind == 'barabasi_albert':
        return GG.barabasi_albert(100, 2, seed=seed)

    elif kind == 'path':
        return GG.path(50)

    else:
        raise ValueError(f"Unknown graph kind: {kind}")


GRAPHS = ['grid', 'erdos_renyi', 'bottleneck', 'barabasi_albert', 'path']


# ═══════════════════════════════════════════════════════════════
# MODULE 4: CLASSIFIER (algorithm recommendation)
# ═══════════════════════════════════════════════════════════════

def classify(vec):
    """
    Rule-based algorithm recommendation:
    BFS, ROUTE_HUBS, BRIDGE_FIRST, A_STAR_SPECTRAL

    Key discriminators:
    - BFS: regular graph, high algebraic connectivity → BFS is optimal
    - ROUTE_HUBS: scale-free, hub-dominated → route through hubs
    - BRIDGE_FIRST: strong community structure, bottleneck → find bridges
    - A_STAR_SPECTRAL: irregular, low gap → spectral heuristic helps
    """
    algo_id = vec[FEATURE_NAMES.index('recommended_algo_id')]
    quality = vec[FEATURE_NAMES.index('heuristic_quality')]
    gap_norm = vec[FEATURE_NAMES.index('spectral_gap_norm')]
    hub_dom = vec[FEATURE_NAMES.index('hub_dominance')]
    part_bal = vec[FEATURE_NAMES.index('partition_balance')]
    bottleneck = vec[FEATURE_NAMES.index('bottleneck_score')]
    reg = vec[FEATURE_NAMES.index('regularity_index')]
    bfs_diam = vec[FEATURE_NAMES.index('bfs_diameter')]

    algo_names = {0.0: 'BFS', 1.0: 'ROUTE_HUBS', 2.0: 'BRIDGE_FIRST', 3.0: 'A_STAR_SPECTRAL'}
    algo = algo_names.get(algo_id, 'UNKNOWN')

    reasons = []
    if algo == 'BFS':
        reasons.append(f'regular (reg={reg:.3f}), well-connected (gap={gap_norm:.3f})')
    elif algo == 'ROUTE_HUBS':
        reasons.append(f'hub-dominated ({hub_dom:.2f})')
    elif algo == 'BRIDGE_FIRST':
        reasons.append(f'bottleneck ({bottleneck:.3f}), unbalanced partition ({part_bal:.3f})')
    elif algo == 'A_STAR_SPECTRAL':
        reasons.append(f'spectral heuristic quality={quality:.3f}')

    reasons.append(f'diameter={int(bfs_diam)}')
    return algo, '; '.join(reasons)


# ═══════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 72)
    print("PATHFINDING SPECTRAL ENGINE — DEMO")
    print("29 features from spectral graph embedding · Builds on graph_engine.py")
    print("=" * 72)

    results = {}
    for kind in GRAPHS:
        G = generate_graph(kind)
        vec = pathfinding_features(G)
        verdict, reason = classify(vec)
        results[kind] = {'vec': vec, 'verdict': verdict, 'reason': reason, 'G': G}

    # ── Classification results ──
    print(f"\n{'─'*72}")
    print("ALGORITHM RECOMMENDATION")
    print(f"{'─'*72}")

    expected = {
        'grid': 'A_STAR_SPECTRAL',  # spectral heuristic is GOOD (rank_corr=0.71)
        'erdos_renyi': 'BFS',
        'bottleneck': 'BRIDGE_FIRST',
        'barabasi_albert': 'ROUTE_HUBS',
        'path': 'A_STAR_SPECTRAL',
    }
    correct = 0
    for kind in GRAPHS:
        r = results[kind]
        G = r['G']
        match = r['verdict'] == expected.get(kind, '?')
        correct += int(match)
        sym = '✓' if match else '~'  # ~ for plausible alternative
        print(f"\n  {sym} {kind:>16}: {r['verdict']}  ({G.name}, N={G.N})")
        print(f"    {r['reason']}")

    print(f"\n  Recommendations: {correct}/{len(GRAPHS)} match expected")

    # ── Spectral heuristic validation ──
    print(f"\n{'─'*72}")
    print("SPECTRAL HEURISTIC VALIDATION")
    print(f"{'─'*72}")
    print(f"  spectral_distance / BFS_distance ratio per graph:")

    for kind in GRAPHS:
        v = results[kind]['vec']
        hr = v[FEATURE_NAMES.index('heuristic_ratio_mean')]
        hs = v[FEATURE_NAMES.index('heuristic_ratio_std')]
        rc = v[FEATURE_NAMES.index('heuristic_rank_corr')]
        quality = 'GOOD' if rc > 0.7 else 'MODERATE' if rc > 0.4 else 'POOR'
        print(f"  {kind:>16}: ratio={hr:.4f}±{hs:.4f}  rank_corr={rc:.3f}  → {quality}")

    # ── Feature comparison ──
    print(f"\n{'─'*72}")
    print("FEATURE VECTORS (29-dim)")
    print(f"{'─'*72}")

    print(f"\n  {'feature':>24}", end='')
    for kind in GRAPHS:
        print(f" {kind[:10]:>10}", end='')
    print()

    for j, fname in enumerate(FEATURE_NAMES):
        print(f"  {fname:>24}", end='')
        vals = [results[k]['vec'][j] for k in GRAPHS]
        for v in vals:
            if abs(v) > 1000:
                print(f" {v:10.0f}", end='')
            elif abs(v) > 10:
                print(f" {v:10.2f}", end='')
            else:
                print(f" {v:10.4f}", end='')
        if np.std(vals) > 0.1 * (np.mean(np.abs(vals)) + 1e-10):
            print("  *", end='')
        print()

    # ── Channel orthogonality ──
    print(f"\n{'─'*72}")
    print("CHANNEL ORTHOGONALITY (Canal B=spectral dist, Canal A=eff resistance, Cross=BFS)")
    print(f"{'─'*72}")

    for kind in GRAPHS:
        v = results[kind]['vec']
        # Canal B: spectral distance [mean, std, max, CV, diam_ratio]
        canal_b = v[7:12]
        # Canal A: effective resistance [mean, max, CV, kirchhoff, diam_ratio]
        canal_a = v[13:18]
        # Cross: BFS comparison [hr_mean, hr_std, rank_corr, bfs_diam, bfs_avg]
        cross = v[18:23]

        r_ba = abs(np.corrcoef(canal_b, canal_a)[0, 1]) if np.std(canal_a) > 1e-10 else 0
        r_bc = abs(np.corrcoef(canal_b, cross)[0, 1]) if np.std(cross) > 1e-10 else 0
        r_ac = abs(np.corrcoef(canal_a, cross)[0, 1]) if np.std(canal_a) > 1e-10 and np.std(cross) > 1e-10 else 0

        orth = "ORTHOGONAL" if max(r_ba, r_bc, r_ac) < 0.5 else "PARTIAL" if max(r_ba, r_bc, r_ac) < 0.8 else "COUPLED"
        print(f"  {kind:>16}: |ρ(B,A)|={r_ba:.3f}  |ρ(B,C)|={r_bc:.3f}  |ρ(A,C)|={r_ac:.3f}  → {orth}")

    # ── Cross-domain mapping ──
    print(f"\n{'─'*72}")
    print("CROSS-DOMAIN MAPPING")
    print(f"{'─'*72}")
    print(f"""
  ζ engine:                Pathfinding engine:
  ─────────                ────────────────────
  t (critical line)        node index in graph
  zeros of ζ               critical nodes (Fiedler bottleneck)
  P(N) spiral              spectral coordinates (eigenvector embedding)
  f(b) = b/(b+1)          effective resistance decay (analog of amplitude)
  cos(ln(p)·γ) phase       spectral distance (eigenvalue-weighted geometry)
  Canal A (v₂)             effective resistance (electrical structure)
  Canal B (ln p)           spectral distance matrix (embedding geometry)
  Cross (ρ~0)              BFS vs spectral rank correlation
  V(σ,t) landscape         resistance distance surface
  gap espectral            algebraic connectivity (Fiedler gap)
  Ramanujan bound          2√(d−1) regularity bound for optimal expansion

  Limitation: spectral heuristic quality depends on graph structure.
  For regular/expander graphs, BFS is already optimal; spectral
  coordinates add nothing. The heuristic is most valuable for
  irregular graphs with bottleneck structure where spectral
  embedding reveals the global geometry BFS cannot see.

  The spectrum is the spectrum.
""")

    # ── Throughput estimate ──
    G_test = GG.erdos_renyi(100, 0.1, seed=0)
    t0 = time.time()
    N_iter = 20
    for _ in range(N_iter):
        pathfinding_features(G_test)
    dt = time.time() - t0
    tput = N_iter / dt
    print(f"  Throughput: {tput:.0f} graphs/second ({dt/N_iter*1000:.1f}ms per graph)")
    print(f"  Graph size: N=100")

    print(f"\n{'='*72}")
    print("ENGINE READY")
    print(f"  Input: Graph (adjacency matrix)")
    print(f"  Output: 29 features + BFS/ROUTE_HUBS/BRIDGE_FIRST/A_STAR_SPECTRAL + reason")
    print(f"  Depends on: graph_engine.py (must be importable)")
    print(f"{'='*72}")
