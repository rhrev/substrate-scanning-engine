# graph_engine.py — Magic Numbers

General graph spectral engine. 29 features from any graph via Laplacian spectrum.

## Graph generators

| Value | Location | Meaning |
|-------|----------|---------|
| `60` | demo graphs `N=60` | Default graph size for demos. 60 nodes is large enough for spectral structure to emerge (Fiedler vector is meaningful) but small enough for instant computation. |
| `0.08` | ER sparse `p=0.08` | Edge probability for sparse Erdős-Rényi graph. Expected degree = 60 × 0.08 = 4.8. Near the connectivity threshold (ln(N)/N ≈ 0.068 for N=60). |
| `0.3` | ER dense `p=0.3` | Dense ER: expected degree = 18. Well above percolation; expected to classify as EXPANDER. |
| `2` | BA `m=2` | Barabási-Albert: each new node attaches to 2 existing nodes. Produces scale-free networks with power-law degree distribution P(k) ∝ k^{-3}. m=2 is the minimal value that gives a connected graph with high probability. |
| `6` | WS `k=6` | Watts-Strogatz: each node initially connected to 6 nearest neighbors (3 on each side of the ring). k=6 is the standard choice in the original small-world paper. |
| `0.1` | WS `p=0.1` | Rewiring probability. At p=0.1, the graph retains most local clustering while gaining short long-range paths. The small-world regime spans roughly 0.01 < p < 1.0. |
| `[20,20,20]` | SBM sizes | Stochastic block model: 3 communities of 20 nodes each. Equal-sized communities for clean spectral interpretation (3 near-zero Laplacian eigenvalues). |
| `0.3` | SBM `pw=0.3` | Within-community edge probability. Dense internal structure. |
| `0.02` | SBM `pb=0.02` | Between-community edge probability. Sparse inter-community links. Ratio pw/pb = 15 gives strong community structure. |
| `30` | Star(30) | Star graph with 30 leaves. The star has exactly 2 distinct Laplacian eigenvalues: 1 (multiplicity N-1) and N (multiplicity 1). |
| `6,10` | Grid(6,10) | 2D grid: 6 rows × 10 columns = 60 nodes. The grid Laplacian has known eigenvalues: 2 - 2cos(πj/r) - 2cos(πk/c). |

### Bot farm generator

| Value | Location | Meaning |
|-------|----------|---------|
| `15, 5, 40` | `bot_farm(nb=15, nt=5, nl=40)` | 15 bots, 5 targets, 40 legitimate users. Ratio 15:5 = 3:1 bot-to-target models a coordinated amplification campaign. 40 legit users provides realistic organic background. |
| `0.9` | `rng.random() < 0.9` | Bot-to-target connection probability: 90%. Bots aggressively follow/engage targets — the signature of coordinated inauthentic behavior. |
| `0.3` | `rng.random() < 0.3` | Bot-to-bot connection probability: 30%. Some bots follow each other (coordination network) but not all (to avoid obvious detection). |
| `1, 8` | `rng.randint(1, min(8, N))` | Legitimate users connect to 1-7 random others. Models organic social behavior (heterogeneous degree). |

## Feature computation

| Value | Location | Meaning |
|-------|----------|---------|
| `n_modes=20` | `graph_features(G, n_modes=20)` | Number of Laplacian eigenvalues to use. 20 captures community structure (near-zero eigenvalues) and spectral tail. For N=60, this is the bottom third of the spectrum. |
| `1e-8` | `e < 1e-8` for component counting | Eigenvalue threshold for "zero": counts the multiplicity of λ=0, which equals the number of connected components. Float64 precision means eigenvalues of connected components are ~ 10⁻¹⁵, so 10⁻⁸ is safe. |
| `1e-15` | multiple locations | Universal division-by-zero guard. |
| `1e-10` | `eigs > 1e-10` for spectral entropy | Threshold for "positive" eigenvalue. Zero eigenvalues are excluded from entropy computation. |
| `10` | `min(n-1, 10)` for max eigengap | Search the first 10 non-trivial eigenvalues for the maximum gap. Beyond 10, eigenvalues are typically dense and the gap is not structurally informative. |
| `1e6` | `min(N * np.sum(1.0/enz), 1e6)` | Cap on effective resistance. In disconnected graphs, the sum of 1/λ diverges; capping at 10⁶ prevents overflow. |
| `0.01` | `is_regular tolerance` | Two degrees are "equal" if they differ by < 0.01. Since degrees are integers, this catches floating-point rounding. |
| `2*np.sqrt(d-1)` | Ramanujan bound | A d-regular graph is Ramanujan if its second-largest eigenvalue satisfies λ₂ ≤ 2√(d-1). This is the Alon-Boppana bound. The constant 2 is exact, not tuneable. |
| `0.01` | `sr <= d + rb + 0.01` | Tolerance for Ramanujan check. The `0.01` accounts for numerical eigenvalue error. |

## Classifier thresholds

| Value | Location | Meaning |
|-------|----------|---------|
| `1.5` | `v[1] > 1.5` (n_components) | More than 1 connected component → DISCONNECTED. Threshold 1.5 rather than 1 because the feature is float. |
| `0.3` | `v[2] > 0.3` (gap_norm) | Normalized gap > 0.3 → EXPANDER. The spectral gap divided by mean degree measures expansion quality. 0.3 is a moderate threshold; Ramanujan graphs have gap_norm ≈ 1.0. |
| `1.5` | `v[4] > 1.5` (degree CV) | Coefficient of variation of degree distribution > 1.5 → SCALE-FREE. Regular graphs have CV ≈ 0; scale-free graphs have CV > 2. |
| `5` | `v[5] > 5` (degree max ratio) | Maximum degree / mean degree > 5 → confirms SCALE-FREE (hub-dominated). |
| `0.2` | `v[4] < 0.2` | Low degree CV → REGULAR. |
| `3` | `v[26] > 3` (hub dominance) | Spectral radius / mean degree > 3 → HUB-DOMINATED. |
| `0.3, 0.1` | `v[13] < 0.3 and v[14] < 0.1` | Low partition balance AND low cut ratio → STRONGLY-CLUSTERED. |
| `3` | `v[15] > 3` (n_near_zero) | More than 3 near-zero eigenvalues → MULTI-COMMUNITY (each near-zero eigenvalue beyond the trivial one indicates an additional community). |
| `0.5` | `v[10] > 0.5` | Level repulsion > 0.5 → LEVEL-REPULSION (spacing ratio approaching GUE value ~0.536). |
| `0.1` | `v[17] > 0.1` | Normalized effective resistance > 0.1 → FRAGILE (vulnerable to node removal). |

## Bot detection thresholds

| Value | Location | Meaning |
|-------|----------|---------|
| `0.3` | `d > 0.3` | Relative feature difference > 0.3 (30%) between organic and bot farm → flagged as discriminating feature. |
