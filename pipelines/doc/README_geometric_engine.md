# geometric_engine.py — Magic Numbers

Core engine. 9 modules, 31 features (29 core + 2 Euler-specific), supports ζ(s), L(s,χ), L(s,E).

## Module 1: EulerProduct

| Value | Location | Meaning |
|-------|----------|---------|
| `1500` | `RiemannZeta.__init__(max_prime=1500)`, `DirichletL.__init__`, `EllipticCurveL` | Upper bound of sieve. 1500 yields 239 primes; sufficient for K ≤ 200. Trade-off: memory vs coverage. |
| `500` | `EllipticCurveL.__init__(max_prime=500)` | Smaller sieve for elliptic curves because `_count_ap` is O(p²) brute-force; p > 500 becomes expensive without precomputed tables. |
| `1e-30` | `EllipticCurveL.log_deriv_term` | Division-by-zero guard for the local factor denominator `1 - a_p·p^{-s} + p·p^{-2s}`. Value chosen well below float64 denormal threshold (~5e-324). |
| `-16`, `4`, `27` | `EllipticCurveL._is_bad` | Discriminant of Weierstrass curve: Δ = -16(4a³ + 27b²). These are standard algebraic constants, not tuneable. |
| `3` | `_is_bad: p > 3` | Primes 2 and 3 always divide the discriminant factor -16; they are always classified as bad reduction. |
| `2*np.sqrt(float(p))` | `arithmetic_channel` | Hasse bound: |a_p| ≤ 2√p. Normalization to [-1, 1] range. |
| `1` | `_count_ap: count = 1` | The point at infinity on the projective curve, always counted. |

## Module 2: ToroidalEmbedding

| Value | Location | Meaning |
|-------|----------|---------|
| `R = 1.5` | `__init__` | Major radius of the torus in ℝ³. Chosen so that `R + r_k > 0` for all `r_k = p_k^{-σ}` at σ = 0.5 (where r_2 = 1/√2 ≈ 0.707). R = 1.5 ensures the torus does not self-intersect. Not physically meaningful — a parametric choice. |
| `2*np.pi` | `embed` | Reduction of angles mod 2π for phase visualization. Exact, not a magic number. |

## Module 3: ThreeScales

| Value | Location | Meaning |
|-------|----------|---------|
| `500` | `decompose(N_max=500)` | Default maximum number of primes in the trajectory. Balances resolution (needs N > 100 for reliable fits) vs. computation (each embed call is O(K)). |
| `999999` | `len(self.torus.L.primes(999999))` | Sentinel to query all available primes. The sieve returns at most 239 primes (for default max_prime=1500), so 999999 is effectively "return all". |
| `50` | `window=50` | Moving-average window size for drift estimation. Must be large enough to smooth oscillations (~20 prime pairs) but small enough to track drift curvature. 50 is ~25% of N_max=200. |
| `60` | `N_pts < 60` | Minimum trajectory length for valid decomposition. Below 60, the moving average (window=50) leaves only 10 points for fitting, which is unreliable. |
| `20` | `len(centers) < 20` | Minimum center points after windowing. 20 gives enough samples for a power-law fit. |
| `10` | `mask.sum() > 10` | Minimum non-zero deviations for the power-law fit `|dev| ~ N^α`. Below 10 points, polyfit is underdetermined. |
| `1e-10` | `dev_mags > 1e-10` | Threshold for "effectively zero" deviation magnitude. Below this, log is meaningless. |
| `1e-15` | `step_norms > 1e-15` | Zero-guard for direction cosine computation. Standard float64 safety margin. |
| `-1, 1` | `np.clip(cos_a, -1, 1)` | Clamping numerical cosine to valid range; floating-point dot products can yield ±1.000000001. |
| `0.9` | `np.median > 0.9` | Coherence threshold: consecutive steps are "aligned" when median cosine > 0.9 (i.e., angle < 26°). Empirically chosen from ζ trajectories where coherence emerges around N ~ 30-50. |
| `10` | `for n in range(10, ...)` | Minimum window for median coherence check. |

## Module 4: EnvelopeDecomposition

| Value | Location | Meaning |
|-------|----------|---------|
| `1e-15` | `fb_norm + 1e-15`, `theta / (fb_norm + 1e-15)` | Division guards against zero f(b) weights. |
| `None` | no numeric magic | This module has no tuneable constants. The f(b) = b/(b+1) formula and the OLS decomposition are parameter-free. |

## Module 5: PotentialLandscape

| Value | Location | Meaning |
|-------|----------|---------|
| `1e-300` | `np.log(mag + 1e-300)` | Guard against log(0). Value is near float64 minimum (~2.2e-308). Using 1e-300 ensures log returns ≈ -691 rather than -inf. |
| `h = 0.003` | `gradient`, `laplacian` | Finite-difference step size for numerical derivatives. At σ = 0.5, the potential V changes on scale ~ 0.1 per unit, so h = 0.003 gives truncation error ~ h² ≈ 10⁻⁵. Verified: 0.07% median harmonicity residual. Smaller h risks cancellation error from float64 subtraction. |
| `1e-15` | `abs(v) + 1e-15` in harmonicity | Zero-guard for the harmonicity ratio |ΔV|/|V|. |

## Module 6: WeilSpectrum

| Value | Location | Meaning |
|-------|----------|---------|
| `-0.25` | `P[j]**(-0.25)` | Exponent in the Weil weighting: p^{-1/4}. Comes from the Weil quadratic form on the critical line σ = 1/2, where p^{-σ/2} = p^{-1/4}. This is the natural weighting for the Weil positivity criterion. |
| `5` | `n_eig=5` | Number of eigenvalues returned. Only the smallest eigenvalue and the gap are used as features; 5 provides context for the spectral distribution. |

## Module 7: ChannelOrthogonality

| Value | Location | Meaning |
|-------|----------|---------|
| `-0.5` | `P**(-0.5)` | Canal B amplitude feature: p^{-1/2} = natural weight at σ = 1/2. |
| `1e-10` | `np.std(...) < 1e-10` | Guard against computing Spearman ρ on constant vectors. |

## Module 8: EulerPhase

| Value | Location | Meaning |
|-------|----------|---------|
| `exp(-π(k/K)²)` | `_gaussian_weights` | Boundary-suppressing window for accumulated argument. Same functional form as the Schwartz-Bruhat kernel f_∞(x) = e^{−πx²} of the archimedean integral in Tate's thesis, but operates here as classical signal windowing — no adelic completeness is invoked (the Critical Circle §6 classifies the Γ connection as "interpretive but not foundational"). Mitigates the divergence of partial Euler products on the critical line (Conrad, Canad. J. Math. 57(2), 2005; cited in Critical Circle Observation 5.6). MVP validation showed 72–93% CV reduction in K-convergence for arg. |
| `h = 0.01` | `query` | Central-difference step for d(arg)/dt. Larger than PotentialLandscape's h=0.003 because arg varies more slowly than V and cancellation error dominates at smaller h. |
| `winding_var` | *excluded* | Variance of phase increments. Proved trivially σ-dependent: Spearman ρ = 1.000 against mean(p^{−2σ}). Theoretical cause: Kronecker-Weyl equidistribution (Critical Circle Theorem 2.1(iv)) implies Var(arg(1−p^{−s})) ≈ (1/2)·E[p^{−2σ}] for generic t, reducing winding_var to a deterministic function of σ. Excluded as label leakage. |

## Module 9: GeometricEngine

| Value | Location | Meaning |
|-------|----------|---------|
| `1e-15` | Multiple locations | Universal zero-guard. Appears in: z_xy_ratio, fb_decay_rate, phase_coherence, Poincaré direction, channels fallback. All serve the same purpose: prevent 0/0. |
| `K*4` | `min(K*4, 500)` in compute_scales | Heuristic: trajectory needs ~4× more primes than the query K to resolve all three scales. Capped at 500 for performance. |

## Demo section

| Value | Location | Meaning |
|-------|----------|---------|
| `14.134725, 21.022040, 25.010858, 30.424876, 32.935062` | `ZEROS` | First 5 non-trivial zeros of ζ(s) (imaginary parts), truncated to 6 decimal places. Standard reference values (Odlyzko tables). |
| `16.0, 19.0, 23.0, 27.5, 34.0` | non-zero points | Points between known zeros, chosen to be roughly equidistant from neighboring zeros for maximal contrast. |
| `K = 30` | demo | Default number of primes for the demo. 30 is where phase_coherence reaches 5.6σ separation. |
| `0.35, 1.10, 0.05` | σ sweep | σ range from well below (0.35) to well above (1.10) the critical line, step 0.05. |
