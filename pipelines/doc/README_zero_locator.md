# zero_locator.py — Magic Numbers

STA-derived zero localization for RiemannZeta. External zeros for other L-functions.

## Scope Limitation

| Limitation | Cause | Consequence |
|-----------|-------|-------------|
| scan() Riemann-only | mpmath.altzeta converges at σ=1/2; no equivalent exists for L(s,χ) or L(s,E) partial sums | Dirichlet/EC zeros must be supplied via from_values() |
| Phase I raw sum | Float64 alternating sum gives |η|≈0.04 at zeros, not 0 | Valley detection works (relative ordering preserved); residual is NOT meaningful at Phase I |
| from_values() residual = NaN | No convergent evaluator for general L-functions | External zeros cannot be independently verified by this code |

## Phase I: Valley Detection

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| `step` | 0.05 | Scanning resolution. Mean zero spacing at t~50 is ~2.3. Step=0.05 gives ~46 samples per zero. | Medium — increase for large t |
| `M` | 80 | Partial sum order for float64. Optimal for float64 precision. | Low |
| `threshold_quantile` | 0.1 | Bottom 10% of |η| values are candidate valleys. Catches all genuine zeros with 1 false positive per ~10 zeros. False positives are rejected by Phase II. | Medium |

## Phase II: Precision Refinement

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| `RESIDUAL_THRESHOLD` | 1e-3 | Reject false valleys. Genuine zeros at dps=50 have residual < 1e-30. False valleys have residual > 0.01. Threshold 1e-3 is conservative (3 orders of magnitude margin). | Low |
| `bracket_width` | 0.1 | Initial bracket half-width. Must be < half the zero spacing (~1.15 at t~50). | Low |
| `max_iter` | 200 | Golden-section iterations. Each gains ~0.618 bits. 200 iterations = ~124 bits = ~37 digits. Sufficient for dps ≤ 100 with guard digits. | Low |
| `dps + 20` | guard digits | Internal computation uses 20 extra digits to prevent rounding. | Low |

## scan_mpmath

| Constant | Value | Origin |
|----------|-------|--------|
| `mpmath.zetazero(n)` | Euler-Maclaurin | mpmath internal. Exact to working precision. Residual is computed (not fabricated) via altzeta. |

## Numerical Safety

| Constant | Value | Purpose |
|----------|-------|---------|
| `t < 1.0` skip | Phase I+II | Avoid trivial region near t=0 |
| `NaN` residual | from_values() | Honestly marks externally supplied zeros as unverified |
