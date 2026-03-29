# Magic Numbers: wavelet_3d_engine.py

Every numerical constant in this file, its origin, meaning, and sensitivity.

## Haar Wavelet

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| √2 divisor | 1/√2 | Orthonormal Haar basis normalization | Exact — changing breaks energy preservation |

## Volume Generator

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| sphere radius | 0.5 | Arbitrary, fills ~half the grid | Low — any radius < 1 works |
| cylinder radius | 0.3 | Smaller than sphere for variety | Low |
| cylinder height | 0.7 | Fills most of z-axis | Low |
| two_spheres centers | ±0.3 | Separated but overlapping range | Low |
| two_spheres radii | 0.25, 0.15 | Different sizes = multi-scale | Medium — ratio matters |
| torus R_major | 0.5 | Standard torus proportion | Low |
| torus r_minor | 0.15 | R/r ≈ 3.3, typical torus | Low |
| noise amplitude | 0.3 | In sphere_noise: SNR ≈ 10 dB | Medium — higher noise → harder classification |
| default N | 32 | Grid size 32³ = 32768 voxels | High — must be power of 2 for Haar; 16 too coarse, 64 too slow |

## Decomposition

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| levels | 3 | 32→16→8→4, three octaves | Medium — 2 loses coarse info, 4 gives 2³ approx (too small) |

## Subband Statistics

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| sparsity threshold | 0.01 × max | Fraction of max for "zero" | Medium — 0.001 too strict, 0.1 too lenient |
| entropy floor | 1e-15 | Prevents log(0) | Exact — numerical safety |
| energy floor | 1e-30 | Prevents division by zero | Exact — numerical safety |

## Feature Extraction

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| n_detail_keys | 7 | LLH, LHL, LHH, HLL, HLH, HHL, HHH | Exact — 2³ - 1 = 7 detail subbands in 3D |
| edge keys | 3 | LLH, LHL, HLL (single-axis detail) | Exact — combinatorial |
| cross keys | 3 | LHH, HLH, HHL (two-axis detail) | Exact — combinatorial |
| corner key | 1 | HHH (three-axis detail) | Exact — combinatorial |

## Classifier Thresholds

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| NOISY: detail_ratio | > 0.8 | Noise fills all detail subbands | Medium — 0.7 catches some structured |
| NOISY: mean_kurtosis | < 1.0 | Gaussian noise has kurt ≈ 0 | Medium |
| NOISY: mean_sparsity | < 0.3 | Noise is dense (non-sparse) | Medium |
| UNIFORM: detail_ratio | < 0.05 | Nearly constant volume | Low — any small threshold works |
| MULTI_SCALE: spec_spread | > 0.3 | Energy spread across levels | Medium |
| MULTI_SCALE: self_sim | < 0.6 | Different pattern at each level | Medium |
| MULTI_SCALE: log(struct_ratio) | > 0.5 | Fine/coarse energy imbalance | Medium |
| STRUCTURED: max_kurtosis | > 1.0 | Sharp edges → super-Gaussian | Medium |
| STRUCTURED: mean_sparsity | > 0.3 | Edges are localized (sparse) | Medium |
| anisotropy CV threshold | 0.4 | Distinguishes isotropic/anisotropic | Medium |

## Known Limitations

- Cylinder and torus classified as MULTI_SCALE (arguably correct: two inherent length scales)
- Haar wavelet has poor frequency localization; Daubechies would improve
- 32³ grid is small; real volumetric data would need 128³+ with pywt
