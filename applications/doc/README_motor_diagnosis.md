# motor_diagnosis.py — Magic Numbers

Vibration fault diagnosis engine. 29 features from accelerometer spectra.

## Signal generator

| Value | Location | Meaning |
|-------|----------|---------|
| `3600` | `rpm=3600` | Default shaft speed: 3600 RPM = 60 Hz rotation frequency. Common for 2-pole induction motors on 60 Hz mains (synchronous speed). |
| `25600` | `fs=25600` | Sampling frequency in Hz. Standard in vibration monitoring: gives 12.8 kHz Nyquist, sufficient for bearing and gear mesh frequencies. Matches common 25.6 kS/s accelerometer ADCs. |
| `8192` | `N_samples=8192` | FFT window: 8192 points at 25600 Hz = 0.32 s window, frequency resolution Δf = 3.125 Hz. 8192 = 2¹³, optimal for FFT. Gives ~0.05× f_rot resolution at 60 Hz. |
| `40` | `snr_dB=40` | Default signal-to-noise ratio in dB. Typical for an accelerometer on a well-mounted bearing housing. |
| `0.5` | `0.5 * np.sin(...)` | Base 1× amplitude: 0.5 g. Residual unbalance on a healthy machine — always present. |
| `0.5 / h**2` | `amp = 0.5 / h**2` | Natural harmonic decay: amplitude ∝ 1/h². This is the expected rolloff for a periodic mechanical impulse with finite rise time. |

### Fault amplitudes

| Value | Fault | Meaning |
|-------|-------|---------|
| `4.0` | unbalance 1× | 1× grows 8× above baseline (0.5→4.5). A severe unbalance condition — ISO 10816 Class IV. |
| `3.0, 1.5` | misalignment 2×, 3× | 2× at 6× baseline, 3× at 3× baseline. Classical angular misalignment signature per ISO 13373-3. |
| `0.8` | looseness ½× | Subharmonic at half rotation speed. Diagnostic of mechanical looseness (bolt rattle, bearing clearance). |
| `1.5 / h**0.5` | looseness harmonics | Slow harmonic decay ∝ h^{-0.5} (vs normal h^{-2}). Many harmonics present — the hallmark of looseness. |

### Bearing frequencies

| Value | Location | Meaning |
|-------|----------|---------|
| `9` | `n_balls = 9` | Number of rolling elements. Typical for a 6205 deep groove ball bearing (standard industrial bearing). |
| `0.4` | `BPFO ≈ 0.4 × n_balls × f_rot` | Ball Pass Frequency Outer race coefficient. For a contact angle ≈ 0° and Bd/Pd ≈ 0.2, BPFO/f_rot = n/2 × (1 - Bd/Pd × cos α) ≈ 0.4n. Simplified from ISO 15243 geometry. |
| `0.6` | `BPFI ≈ 0.6 × n_balls × f_rot` | Ball Pass Frequency Inner race: BPFI/f_rot = n/2 × (1 + Bd/Pd × cos α) ≈ 0.6n. Complementary to BPFO (sum ≈ n). |
| `0.3` | `1 + 0.3 * np.sin(...)` | Amplitude modulation depth for outer race fault. BPFO signal is modulated at 1× because the fault zone enters and exits the load zone once per revolution. 0.3 = 30% modulation, moderate severity. |
| `0.4` | inner race modulation depth | Higher modulation (40%) because the inner race rotates with the shaft, creating stronger amplitude variation. |
| `0.8` | sideband amplitude | Sidebands at BPFO ± f_rot: 0.8 relative to carrier. Clearly detectable sidebands. |

### Gear mesh

| Value | Location | Meaning |
|-------|----------|---------|
| `42` | `n_teeth = 42` | Number of teeth on the gear. 42 is common for a first-reduction spur gear. Mesh frequency = 42 × 60 Hz = 2520 Hz. |
| `3.0` | gear mesh amplitude | Mesh frequency amplitude: 6× baseline. A healthy gear has mesh vibration; faults increase sidebands rather than the fundamental. |
| `1.0 / n` | sideband decay | Sidebands at f_mesh ± n×f_rot decay as 1/n. Classical gear modulation pattern. |

### Early bearing

| Value | Location | Meaning |
|-------|----------|---------|
| `0.3` | BPFO amplitude | 0.3 g at BPFO: barely above noise floor. This simulates an incipient defect detectable only by statistical methods. |
| `0.1` | modulation depth | 10% AM: very faint modulation. Requires envelope analysis to detect. |
| `0.3` | impulse amplitude | Exponentially distributed impulses of mean 0.3 g. Models the random impact of a ball hitting a nascent spall. |
| `5` | impulse width (samples) | 5 samples at 25.6 kHz = 0.2 ms impulse duration. Typical for a high-frequency bearing impact. |

### Noise

| Value | Location | Meaning |
|-------|----------|---------|
| `10**(snr_dB/10)` | noise power calculation | SNR in dB to linear power ratio. Standard formula: SNR_linear = 10^(SNR_dB/10). |

## Feature extraction

| Value | Location | Meaning |
|-------|----------|---------|
| `±3` | `lo, hi = max(0, idx-3), min(N, idx+4)` | Peak search window: ±3 frequency bins around expected harmonic. At Δf = 3.125 Hz, this is ±9.4 Hz. Accounts for slight RPM variation and spectral leakage. |
| `3` | `height=np.mean(s) * 3` | Peak height threshold: 3× mean spectrum level. Ensures only significant peaks are detected, not noise bumps. |
| `0.3` | `f_rot * 0.3 / df` | Minimum peak distance: 0.3 × f_rot in bins. Prevents detecting sidelobes of the same peak as separate peaks. |
| `0.05` | `abs(f_pk - nearest_harm) < f_rot * 0.05` | Synchronous peak tolerance: within 5% of the nearest harmonic order. A peak at 59.5 Hz when f_rot = 60 Hz is still considered synchronous. |
| `5` | `sorted_idx[:5]` | Check the top 5 highest peaks for sidebands. Limits computation while catching the dominant fault frequency. |
| `0.3` | `a_sb > 0.3 * s[peaks[pi]]` | Sideband threshold: sideband must be at least 30% of the carrier amplitude to be counted. Below this, it could be noise. |
| `-2.0` | `harm_decay = -2.0` default | Default harmonic decay rate when fewer than 3 non-zero harmonics exist. -2.0 matches the expected natural decay (1/h²). |
| `1e-15` | multiple locations | Universal zero-guard for ratios. |
| `1000` | `vel_approx = overall_level * 1000 / (2π × centroid)` | Conversion factor: acceleration (g) to velocity (mm/s) via `v = a/(2πf)`, with g→mm/s² factor of 9810, simplified to 1000 as approximate. This is a rough ISO 10816 proxy, not a precise conversion. |

## Classifier thresholds

| Value | Location | Meaning |
|-------|----------|---------|
| `0.4` | `overall < 0.4` | NORMAL threshold: below 0.4 g RMS. Corresponds to ISO 10816 Class I (newly commissioned machines). |
| `0.8` | `overall > 0.8` | MEDIUM severity: 0.8 g RMS. ISO 10816 Class II boundary. |
| `2.0` | `overall > 2.0` | HIGH severity: 2.0 g RMS. ISO 10816 Class III/IV boundary (unacceptable for continuous operation). |
| `0.7` | `dom_1x > 0.7` | 1× dominance > 70%: unbalance (most energy in fundamental). |
| `0.5` | `r21 < 0.5` | 2×/1× ratio < 0.5 for unbalance (low harmonics confirm single-frequency fault). |
| `0.2` | `r_half < 0.2` | Subharmonic ratio < 0.2 for unbalance (no looseness indicators). |
| `1.0` | `r21 > 1.0` | 2×/1× > 1.0: definitive misalignment (2× exceeds 1×). |
| `0.3` | `r_half > 0.3` | ½× present: looseness signature. |
| `-1.0` | `harm_d > -1.0` | Slow harmonic decay (slope > -1): many harmonics have significant energy, indicating looseness or impacts. Normal decay is ~ -2. |
| `2` | `nonsync > 2` | More than 2 non-synchronous peaks: bearing defect. |
| `500` | `centroid > 500` | High spectral centroid (> 500 Hz): inner race fault (BPFI > BPFO). |
| `1000` | `centroid > 1000` | Very high centroid for gear mesh diagnosis. Mesh frequencies are typically > 1 kHz. |
| `3` | `sidebands > 3` | More than 3 sidebands: definitive gear fault pattern. |
| `3` | `broadband > 3` | Broadband ratio > 3: energy is spread far beyond 1× — looseness or advanced degradation. |
| `0.5` | `r21 > 0.5` | Mild misalignment threshold (lower than 1.0 for definitive). |

## Demo: severity progression

| Value | Location | Meaning |
|-------|----------|---------|
| `60, 50, 40, 35, 30, 25, 20` | SNR sweep | Simulates a bearing fault growing over time by decreasing SNR. At 60 dB the fault is buried in noise; at 20 dB it dominates. |
