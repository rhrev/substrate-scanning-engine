# cf_features.py — Magic Numbers

CF-integer feature extraction pipeline. 10 per-eigenvalue features, 4 cross-eigenvalue features.

## CF Expansion

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| `max_terms` | 50 | Default CF depth. At 100-digit precision, ~50 terms are extractable before the Gauss map error exceeds residual precision. Lyapunov exponent π²/(6 ln 2) ≈ 2.37 implies ~1.03 digits consumed per CF term. | Medium — increase with precision |
| `min_remainder` | `10^{-(dps-10)}` | Guard digits: 10 digits below working precision. Prevents extracting spurious CF terms from rounding noise. | Low — conservative default |

## Gauss-Kuzmin Distribution

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| `P(a > 10)` | 0.1254 | P(a >= 11) = log2(12/11) ≈ 0.1256. Code computes truncated sum at k=10000 → 0.1254. | Exact to 4 digits |
| `P(a odd)` | 0.6514 | sum_{k=1,3,5,...}^{9999} GK_pmf(k). | Exact to 4 digits |
| `P(a prime)` | ~0.366 | sum_{p prime ≤ 10000} GK_pmf(p). Includes tail estimate. | Exact to 3 digits |
| `6/π²` | 0.6079 | Coprime density: P(gcd(a,b)=1) for random integers. Used as null for C3. | Exact (number theory) |

## Feature Thresholds

| Constant | Location | Meaning |
|----------|----------|---------|
| `10` | F3 large_a_freq | Threshold for "large" CF coefficient. P(a>10) = 0.1254 under GK. Matches STA §4.3 "Spectral Resonance Point" definition. A coefficient a_k > 10 injects > log2(100) ≈ 6.6 bits. |
| `3` | F10 digit_mod | Modulus for digit modularity test. Uses GK mod-3 distribution as null (NOT uniform). P(0)=0.179, P(1)=0.547, P(2)=0.274. |
| `3` | C4 mod_mutual_info | Same modulus for cross-eigenvalue MI. Consistent with F10. |
| `1e-15` | C4 MI computation | Zero-guard for log2 in mutual information. Prevents log(0). |

## Excluded Features

| Feature | Reason | Evidence | Theoretical cause | Documented in |
|---------|--------|----------|-------------------|---------------|
| `a_0` | Magnitude leakage | Spearman ρ(a_0, γ) = 1.000 | a_0 = ⌊γ⌋ by definition | Class docstring |
| `winding_var analog` (Var(a_k)) | Potential σ-proxy | Not yet tested | Analogous to SSE winding_var (ρ=1.000 vs mean(p^{-2σ})) | Class docstring |

## Cross-Feature Constants

| Constant | Value | Origin |
|----------|-------|--------|
| `min K = 3` | minimum CF depth for features | Below 3 terms, Spearman correlation is undefined; KS test is meaningless. |
| `n_pairs = N(N-1)/2` | number of cross-eigenvalue pairs | Standard combinatorial formula. For N=100: 4950 pairs. |

## Numerical Safety

| Constant | Value | Purpose |
|----------|-------|---------|
| `1e-15` | MI guard | Prevents log2(0) in mutual information |
| `np.nan` | insufficient data return | If K < 3, return NaN array rather than incorrect values |
