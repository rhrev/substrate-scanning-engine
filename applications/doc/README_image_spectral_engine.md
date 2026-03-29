# Magic Numbers: image_spectral_engine.py

Every numerical constant in this file, its origin, meaning, and sensitivity.

## Image Generator

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| default N | 64 | 64×64 pixels, manageable FFT | Medium — 32 too coarse, 256 slow |
| natural filter | f^{-1} | P(f) ~ f^{-2}, Field 1987 natural image statistics | Exact — well-established |
| periodic grid | 4 cycles | sin(4·2π·x/N) | Low — any ≥ 2 creates texture |
| periodic harmonics | 3×, 2× | Higher harmonics for complexity | Low |
| noisy_natural SNR | 0.5 std | Moderate noise addition | Medium |
| forgery block_size | N/4 | Quarter of image | Medium — too small: undetectable; too large: trivial |
| forgery amplitude | 3.0× | Strong periodic block | Medium — must exceed natural texture |
| forgery frequency | 6 cycles | Dense texture in pasted block | Low |

## Radial Power Spectrum

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| max_r | min(cx, cy) | Nyquist radius | Exact |
| DC removal | img - mean | Standard practice, removes f=0 spike | Exact |

## Angular Spectrum

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| n_sectors | 8 | 45° sectors, standard angular resolution | Medium — 4 too coarse, 16 noisy |
| DC exclusion | R > 1 | Skip center pixel | Exact |

## Peak Detection

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| prominence threshold | 2 × median | Peak must be 2× above median power | High — 1.5 too many false peaks, 5 misses real ones |

## Feature Extraction

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| band split | thirds | Low/mid/high frequency bands | Low — any partition works |
| rolloff threshold | 85% | Standard spectral rolloff | Low — 90% and 95% also common |
| anisotropy cap | 1e6 | Prevents overflow for pure edges | Exact — numerical safety |

## Classifier Thresholds

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| NOISY: abs(slope) | < 0.8 | White noise: slope ≈ 0 | Medium |
| NOISY: flatness | > 0.15 | Flat spectrum indicator | Medium |
| EDGE: anisotropy | > 3.0 | Strong directional preference | Medium |
| EDGE: isotropy | < 0.3 | Low isotropy confirms directionality | Medium |
| EDGE: slope | < -2.5 | Step function: energy concentrated at low f | Medium |
| TEXTURED: n_peaks | ≥ 2 | Multiple spectral peaks | Medium |
| TEXTURED: prominence | > 3.0 | Peaks well above background | Medium |
| NATURAL: slope range | [-3.5, -0.8] | Natural images: slope ≈ -2 (Field 1987) | Medium |

## Forgery Detection

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| block_size | 16 | Local analysis window | High — too small: noisy; too large: averages out anomaly |
| anomaly threshold | 1.5 | |local_slope - global_slope| for flagging | High — set empirically |
| std floor | 1e-10 | Skip constant blocks | Exact |

## Known Limitations

- 64×64 is small; real forensics needs megapixel images with multi-scale blocks
- Forgery test uses slope comparison only; professional forensics uses JPEG artifacts, noise patterns, etc.
- The 1/f^α result for natural images is well-established (Field 1987); the engine re-derives it
