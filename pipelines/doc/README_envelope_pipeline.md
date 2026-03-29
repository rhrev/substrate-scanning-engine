# envelope_pipeline.py — Magic Numbers

Envelope optimization v1. L-BFGS on log-derivative loss over known zeros.

## Primes and zeros

| Value | Location | Meaning |
|-------|----------|---------|
| `1500` | `sieve(1500)` | Prime sieve upper bound. Same as geometric_engine. |
| `[:200]` | `P = sieve(1500)[:200]` | First 200 primes (up to p = 1223). Sufficient for K ≤ 50 with margin. |
| `14.134725...` through `49.773832...` | `ZEROS` | First 10 non-trivial zeros of ζ(s), 15-digit precision. Source: LMFDB / Odlyzko. More digits than geometric_engine demo because optimization is sensitive to target precision. |

## Loss function

| Value | Location | Meaning |
|-------|----------|---------|
| `1e-30` | `dd < 1e-30` | Skip guard: if `|1 - p^{-s}|² < 1e-30`, the local factor is near a pole. This avoids division by near-zero in the log-derivative term. |
| `lam = 0.01` | `loss_with_reg` default | L2 regularization strength. Prevents degenerate solutions where one weight dominates. |
| `0.001` | `args=(K, train_zeros, 0.5, 0.001)` | Actual regularization used in optimization (overrides default 0.01). Weaker regularization to allow the optimizer more freedom. |

## Optimization

| Value | Location | Meaning |
|-------|----------|---------|
| `6, 10, 15, 20, 30, 50` | `for K in [...]` | Number of primes to optimize. Covers the range from Connes' K=6 result up to K=50 where the feature space is rich enough for decomposition analysis. |
| `5` | `n_zeros = min(5, ...)` | Training set: first 5 zeros. The remaining zeros (6-10) test generalization. 5 is enough to constrain 6-50 weights without overfitting. |
| `1/K` | `theta0 = np.ones(K) / K` | Uniform initialization (equal weights summing to 1). |
| `P[:K]**(-0.5)` | `theta_amp` | Natural amplitude initialization: p^{-1/2}, the Euler product weight at σ = 1/2. |
| `2000` | `maxiter: 2000` | L-BFGS iteration limit. Convergence typically occurs in 200-500 iterations; 2000 gives safety margin. |
| `1e-20` | `ftol: 1e-20` | Function tolerance. Very tight because the losses at K ≥ 20 reach 10⁻¹² scale. Default ftol (10⁻⁸) would stop too early. |
| `8` | `ZEROS[:min(8, ...)]` | Evaluate residuals on the first 8 zeros (5 trained + 3 test). |

## Analysis stages

| Value | Location | Meaning |
|-------|----------|---------|
| `1e-6` | `theta > 1e-6` | Threshold for "non-negligible" weight in decay fitting. Below 1e-6, the weight contributes nothing and its log is meaningless. |
| `5` | `mask.sum() > 5` | Minimum non-zero weights for fitting the decay profile. |
| `-0.5` | `beta - (-0.5)` | Reference: natural Euler product weight decay is p^{-1/2}, i.e., β = -0.5. Deviation Δβ measures how the optimizer departs from the natural amplitude. |
| `0.01` | `sp < 0.01` | Spearman p-value threshold for "significant" correlation. |
| `0.3` | `abs(sr) > 0.3` | Spearman ρ threshold for "meaningful" correlation. |
| `0.05` | `sp < 0.05` | p-value threshold for "weak" correlation. |
| `0.15, 0.3` | residual norm thresholds | `< 0.15` = mostly explained by A+B; `> 0.3` = third axis exists. The 0.3 threshold means 30% of signal variance is unexplained by arithmetic + amplitude channels. |
| `-55` | `np.log10(...) - (-55)` | Connes' K=6 precision: 10^{-55} for γ₁. Cited from arXiv:2602.04022. |
