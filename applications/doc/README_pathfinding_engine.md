# Magic Numbers: pathfinding_engine.py

Every numerical constant in this file, its origin, meaning, and sensitivity.

## Spectral Embedding

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| k_embed default | 5 | Embedding dimension (first 5 non-trivial eigenvectors) | Medium — 3 too low, 10 redundant for most graphs |
| eigenvalue floor | 1e-10 | Threshold for "positive" eigenvalue in pseudoinverse | Exact — numerical safety |

## Effective Resistance

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| L^+ construction | Σ (1/λ_k) v_k v_k^T | Moore-Penrose pseudoinverse of Laplacian | Exact — standard formula |
| R_ij formula | L^+_ii + L^+_jj - 2L^+_ij | Effective resistance from pseudoinverse | Exact — electrical network theory |

## BFS Sampling

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| n_sources | min(N, 10) | BFS from first 10 nodes | Medium — more → better diameter estimate, slower |

## Effective Embedding Dimension

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| participation ratio | 1/Σ(p_k²) | Inverse participation ratio of normalized eigenvalues | Exact — standard measure |

## Test Graphs

| Graph | Parameters | N | Properties |
|-------|-----------|---|------------|
| grid | 10×10 | 100 | Regular, lattice, spectral heuristic works well |
| erdos_renyi | N=100, p=0.1 | 100 | Random, well-connected, BFS sufficient |
| bottleneck | SBM([50,50], pw=0.2, pb=0.005) | 100 | Two clusters, bridge structure |
| barabasi_albert | N=100, m=2 | 100 | Scale-free, hub-dominated |
| path | N=50 | 50 | Linear, worst case for BFS, spectral helps |

## Algorithm Recommendation Thresholds

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| BRIDGE_FIRST: bottleneck | > 1.0 | Max eigengap indicates cluster boundary | High — calibrated from SBM |
| BRIDGE_FIRST: gap_norm | < 0.1 | Low algebraic connectivity confirms bridge | Medium |
| BFS: gap_norm | > 0.15 | Well-connected → BFS optimal | Medium |
| BFS: degree_CV | < 0.5 | Regular enough that BFS explores evenly | Medium |
| ROUTE_HUBS: degree_CV | > 0.8 | Scale-free structure, heterogeneous degree | Medium |
| A_STAR_SPECTRAL: reg_index | > 0.8 | Regular but low gap (lattice-like) | Medium |
| A_STAR_SPECTRAL: gap_norm | < 0.05 | Low connectivity → spectral geometry valuable | Medium |

## Heuristic Quality Assessment

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| GOOD: rank_corr | > 0.7 | Spectral distance preserves BFS ranking well | Medium |
| MODERATE: rank_corr | > 0.4 | Partial correlation, useful but imperfect | Medium |
| POOR: rank_corr | ≤ 0.4 | Spectral heuristic unreliable | Medium |

## Graph Engine Dependencies

| Import | Source | Purpose |
|--------|--------|---------|
| Graph | graph_engine.py | Adjacency matrix + Laplacian + spectrum |
| GG | graph_engine.py | Graph generators (ER, BA, WS, SBM, etc.) |
| graph_features | graph_engine.py | Base 29-feature extraction |
| FNAMES | graph_engine.py | Feature name list (for reference) |

## Numerical Safety

| Constant | Value | Purpose |
|----------|-------|---------|
| 1e-15 | various floors | Prevents division by zero in ratios |
| 1e-10 | eigenvalue threshold | Distinguishes zero from positive eigenvalues |

## Known Limitations

- Spectral heuristic quality depends on graph structure; adds nothing for expanders
- Effective resistance computation is O(N²) in the eigendecomposition output
- BFS sampling from first 10 nodes may miss diameter in pathological cases
- Grid classified as A_STAR_SPECTRAL (rank_corr=0.71, the best in the test set)
- Algorithm recommendation is a heuristic, not a proven optimality guarantee
