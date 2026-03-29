# Magic Numbers: turbulence_engine.py

Every numerical constant in this file, its origin, meaning, and sensitivity.

## Haar Wavelet

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| √2 divisor | 1/√2 | Orthonormal Haar basis | Exact |

## Signal Generator

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| default N | 4096 | 2¹² samples, 12 decomposition levels possible | Medium — 1024 too few scales, 16384 slow |
| laminar harmonics | 10 Hz, 20 Hz | Arbitrary smooth flow frequencies | Low |
| laminar amplitude ratio | 0.3 | Second harmonic weaker | Low |
| kolmogorov exponent | -5/6 | E(k) ~ k^{-5/3} → amplitude ~ k^{-5/6} | Exact — Kolmogorov 1941 theory |
| intermittent n_bursts | 8 | Number of burst events | Low |
| burst multiplier | 5× | Burst amplitude relative to base | Medium — < 3 not intermittent enough |
| burst width range | 16–64 | Samples per burst | Low |
| tonal frequencies | 50 Hz, 100 Hz | Machine-like harmonics | Low |
| tonal noise amplitude | 0.1 | Slight noise floor | Low |

## Decomposition

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| default levels | 8 | 4096→2048→...→16, eight octaves | Medium — more levels → finer cascade resolution |

## Cascade Diagnostics

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| K41 ratio | 2^{5/3} ≈ 3.175 | Kolmogorov 1941 inertial cascade prediction | Exact — theoretical |
| K41 tolerance | 50% | Range for "inertial" scale identification | High — 30% too strict for Haar, 70% too loose |

## Classifier Thresholds

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| INTERMITTENT: kurt_max | > 5.0 | Bursts create extreme kurtosis | Medium — 3.0 too sensitive, 10.0 misses weak bursts |
| LAMINAR/TONAL: kurt_max | < 0.5 | Sinusoids have negative excess kurtosis | Medium |
| TONAL: residual | > 0.5 | Discrete peaks → poor cascade fit | Medium |
| BROADBAND: slope | < -0.3 | White noise has equal energy at all scales | Medium |
| KOLMOGOROV: approx_ratio | > 0.3 | Red spectrum: most energy at large scales | Medium |

## Numerical Safety

| Constant | Value | Purpose |
|----------|-------|---------|
| 1e-15 | std floor | Prevents division by zero in kurtosis/normalization |
| 1e-30 | energy floor | Prevents log(0) in energy calculations |

## Known Limitations

- Haar wavelet has poor frequency localization; K41 ratio not recovered cleanly
- Intermittent signal kurtosis_growth_rate is negative (bursts at random positions, not scale-dependent)
- Real turbulence analysis requires Daubechies/Morlet wavelets and continuous WT
- Classifier uses empirical thresholds from synthetic signals, not theoretical predictions
