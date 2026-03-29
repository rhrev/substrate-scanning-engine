# envelope_v2.py — Magic Numbers

Envelope optimization v2. MLP + Weil quadratic form loss.

## Shared with v1

All primes, zeros, and sieve constants are identical to envelope_pipeline.py. See that README for documentation.

## Weil matrix

| Value | Location | Meaning |
|-------|----------|---------|
| `-0.25` | `P[j]**(-0.25)` | Weil weighting p^{-1/4}. See geometric_engine README, Module 6. Comes from σ/2 = 1/4 on the critical line. |

## MLP architecture

| Value | Location | Meaning |
|-------|----------|---------|
| `n_hidden = 8` | Stage 2 | Hidden layer width. 8 neurons for 6 input features is a 6→8→1 architecture. Chosen to be slightly wider than input to allow nonlinear mixing without excessive parameters. Total params: 6×8 + 8 + 8×1 + 1 = 65. |
| `np.sqrt(2.0/n_in)` | `MLP.__init__` | Xavier/He initialization: `W ~ N(0, √(2/fan_in))`. Standard practice for tanh activation to maintain variance across layers. The `2.0` is the He correction factor. |
| `5` | `for restart in range(5)` | Number of random restarts. MLP loss landscape is non-convex; 5 restarts gives reasonable coverage of local minima. |
| `3000` | `maxiter: 3000` | L-BFGS iteration limit for MLP. Higher than v1's 2000 because the MLP has more parameters and a more complex loss landscape. |
| `1e-18` | `ftol: 1e-18` | Tighter tolerance than v1 because the Weil loss has a different scale. |
| `0.001` | `reg = 0.001 * np.sum(params**2)` | L2 regularization on MLP parameters. Same as v1 effective regularization. |

## Feature normalization

| Value | Location | Meaning |
|-------|----------|---------|
| `1e-15` | `rng > 1e-15` | Guard against dividing by zero when normalizing constant features to [0,1]. |

## Analysis thresholds

| Value | Location | Meaning |
|-------|----------|---------|
| `0.7` | `np.mean(np.abs(cors)) > 0.7` | Threshold for "UNIVERSAL weights": if mean pairwise correlation > 0.7, the same weights work for all zeros. |
| `0.3` | `np.mean(np.abs(cors)) < 0.3` | Threshold for "ZERO-SPECIFIC weights": if mean correlation < 0.3, each zero requires its own operator. |
| `0.15` | `res_norm > 0.15` | Minimum residual to trigger third-axis analysis. Below 0.15, Canal A+B explain most of the variance. |
| `0.3` | `abs(sr) > 0.3 and sp < 0.05` | Significance threshold for residual correlations. |
| `3` | `for _ in range(3)` in ablation | Restarts per ablation experiment. Fewer than full optimization (5) to keep compute tractable with 6 ablation runs × 3 restarts = 18 optimizations. |
| `0.40, 1.06, 0.05` | σ sweep range | Same logic as geometric_engine σ sweep: below, above, and through the critical line. |
| `17.5` | `sigma, 17.5, K_sweep` | Point between γ₁ = 14.13 and γ₂ = 21.02, chosen as midpoint for "between zeros" baseline. |

## Per-zero analysis

| Value | Location | Meaning |
|-------|----------|---------|
| `K_pz = 20` | Stage 7 | 20 primes for per-zero optimization. Moderate K gives enough structure for pairwise comparison without making each optimization expensive. |
| `6` | `ZEROS[:6]` | Optimize separately for the first 6 zeros to build a 6×6 correlation matrix. |
