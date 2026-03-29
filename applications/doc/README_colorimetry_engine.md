# colorimetry_engine.py — Magic Numbers

Colorimetry spectral engine. 29 features from visible spectrum S(λ).

## Spectral grid

| Value | Location | Meaning |
|-------|----------|---------|
| `380` | `WAVELENGTHS = np.arange(380, 790, 10)` | Start of visible spectrum in nm. Below 380 nm is ultraviolet. |
| `790` | arange endpoint (exclusive) | Produces wavelengths up to 780 nm. Above 780 nm is near-infrared. |
| `10` | step | 10 nm sampling interval. Standard CIE observer data is tabulated at 5 nm or 10 nm; 10 nm is the coarser standard, yielding 41 points. Sufficient for colorimetric accuracy within 1 ΔE. |
| `41` | `N_LAMBDA = 41` | Number of spectral samples: (780 - 380)/10 + 1 = 41 points. |

## CIE 1931 2° observer

| Value | Location | Meaning |
|-------|----------|---------|
| `CIE_X`, `CIE_Y`, `CIE_Z` | 41-element arrays | Tabulated CIE 1931 color matching functions x̄(λ), ȳ(λ), z̄(λ) at 10 nm intervals, 380–780 nm. These are international standards (CIE 015:2018). The values are normalized to peak ȳ = 1.0 at 555 nm (photopic sensitivity maximum). Simplified tabulation — full-precision tables have 6 decimal places. |
| `10.0` | `dl = 10.0` in `spectrum_to_xyz` | Integration step size (nm). XYZ = Σ S(λ)·x̄(λ)·Δλ. The 10 nm step matches the sampling grid. |

## Feature computation

### Peaks and bandwidth

| Value | Location | Meaning |
|-------|----------|---------|
| `0.05` | `prominence=S.max()*0.05` | Peak detection prominence: 5% of maximum. Rejects noise ripples while catching real emission/absorption peaks. For a daylight spectrum with max ≈ 0.8, minimum prominence is 0.04. |
| `3` | `distance=3` | Minimum distance between peaks: 3 samples = 30 nm. Prevents double-counting a broad peak with a noisy top. |
| `580.0` | `peak_wl = 580.0` default | Default peak wavelength when no peaks are found. 580 nm is the yellow-green region where photopic sensitivity is highest — a reasonable default for broadband sources. |
| `0.5` | `half_max = S.max() * 0.5` | Half-maximum for FWHM bandwidth calculation. Standard definition. |

### Spectral moments

| Value | Location | Meaning |
|-------|----------|---------|
| `1e-15` | multiple denominators | Zero-guard for normalization (S.sum(), mean, centroid). |
| `1e-10` | `max(spread, 1e-10)` | Guard against zero spread in skewness/kurtosis computation. A perfectly monochromatic source has zero spread. |

### Band ratios

| Value | Location | Meaning |
|-------|----------|---------|
| `[:12]` | blue band | Indices 0–11 → 380–490 nm. The blue portion of the visible spectrum. |
| `[12:24]` | green band | Indices 12–23 → 500–610 nm. The green-yellow portion. |
| `[24:]` | red band | Indices 24–40 → 620–780 nm. The red-NIR portion. |
| `[:4]` | UV energy | Indices 0–3 → 380–410 nm. The near-UV tail that affects material degradation and fluorescence excitation. |

### Spectral quality

| Value | Location | Meaning |
|-------|----------|---------|
| `1e-10` | `S_pos = S[S > 1e-10]` | Filter for flatness computation (geometric mean requires positive values). 1e-10 excludes effectively dark spectral regions. |
| `1/3` | `xyz[0]/total - 1/3` | Equal-energy white point in CIE xy chromaticity: (x, y) = (1/3, 1/3). The distance from this point measures colorimetric purity. |
| `0.3` | `purity = dist_from_wp / 0.3` | Purity normalization. The maximum distance from the white point to the spectrum locus in CIE xy is approximately 0.3 for most saturated colors. This gives purity ∈ [0, ~1] for typical sources. Approximate, not exact — the spectrum locus is not circular. |
| `0.95` | `np.searchsorted(cum, 0.95)` | Metamer dimension: effective rank at 95% cumulative variance. Standard threshold for dimensionality estimation (cf. PCA scree plots). Higher metamer_dim means more spectral information beyond XYZ — sources with the same XYZ but different spectra (metamers) are distinguishable by these features. |

### Energy bands

| Value | Location | Meaning |
|-------|----------|---------|
| `N_LAMBDA // 3` | `third = 13` | Splits the spectrum into three equal-width bands of ~13 samples each (130 nm). Low: 380–510 nm (UV-blue), mid: 510–640 nm (green-yellow), high: 640–780 nm (red-NIR). |

## Synthetic spectra

| Value | Spectrum | Meaning |
|-------|----------|---------|
| `630, 15` | pure_red | Gaussian peak at 630 nm (orange-red), σ = 15 nm. Narrow emitter. |
| `530, 15` | pure_green | Peak at 530 nm (green), σ = 15 nm. |
| `460, 15` | pure_blue | Peak at 460 nm (blue), σ = 15 nm. |
| `0.5 + 0.3·sin(...)` | daylight | Broadband spectrum with sinusoidal modulation. The 0.5 baseline + 0.3 amplitude gives a spectrum between 0.2 and 0.8, roughly approximating CIE D65 daylight shape. Period of 400 nm matches the visible range. |
| `seed=42` | daylight noise | `RandomState(42)` for reproducible 0.02 σ Gaussian noise. |
| `np.linspace(0.1, 1.0)²` | incandescent | Quadratic rise from blue (0.01) to red (1.0). Models Planck blackbody tail shape — incandescent sources are red-heavy. |
| `[435, 545, 580, 610]` | fluorescent | Four mercury emission lines at standard phosphor wavelengths. These are the actual dominant lines in a tri-phosphor fluorescent tube. |
| `[8, 8, 10, 8]` | fluorescent widths | Narrow peaks (8-10 nm σ). Real fluorescent lines are 5-15 nm wide. |
| `[0.8, 1.0, 0.6, 0.4]` | fluorescent amplitudes | Relative intensities tuned to produce near-white appearance. |
| `[450, 560]` | LED_white | Blue LED (450 nm) + broadband phosphor (560 nm, σ=50 nm). This is the actual architecture of white LEDs (blue pump + yellow phosphor). |
| `[480, 580]` | metamer_A | Two-peak source designed to produce a specific XYZ value. |
| `[500, 560, 620]` | metamer_B | Three-peak source designed to produce a similar XYZ to metamer_A but with different spectral shape. The feature distance should exceed XYZ distance, demonstrating the engine detects structure that CIE XYZ discards. |
| `[694]` | ruby | Ruby fluorescence line at 694 nm (Cr³⁺ R-line). Very narrow (σ=5 nm). The 0.05 baseline models the broad absorption background. |
| `[520, 560]` | emerald | Emerald green: two peaks at 520 nm and 560 nm (Cr³⁺ in beryl). Narrow peaks (σ=10 nm). |

## Metamer test

| Value | Location | Meaning |
|-------|----------|---------|
| `range(3)` | XYZ distance | First 3 features are X, Y, Z. |
| `range(3, 29)` | Feature distance | Remaining 26 features capture spectral structure beyond XYZ. |
| `2.0×` | paper claim | Feature distance / XYZ distance ≈ 2.0 for the designed metamer pair. This ratio is the engine's value proposition: it sees 2× more difference than the human eye (via XYZ). |
