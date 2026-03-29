# sparam_engine.py — Magic Numbers

S-parameter spectral engine. 29 features from 4-port differential channels.

## Touchstone parser

| Value | Location | Meaning |
|-------|----------|---------|
| `1e9` | `freq_mult = 1e9` | Default frequency unit: GHz. Touchstone files may specify HZ, KHZ, MHZ, or GHZ in the option line. If none is specified, the standard assumes GHz. |
| `50.0` | `z0 = 50.0` | Reference impedance (ohms). Standard for RF/microwave systems. Not used in the current feature extraction but stored for impedance-referenced calculations. |
| `33` | `len(values) < 33` | Expected values per frequency point in a 4-port Touchstone file: 1 frequency + 16 complex S-parameters × 2 (real/imag or mag/angle) = 33 numbers. |
| `1/np.sqrt(2)` | Mixed-mode matrix `M` | The 1/√2 normalization comes from the differential/common mode decomposition: V_diff = (V₁ - V₂)/√2, V_comm = (V₁ + V₂)/√2. Power-preserving transformation. |
| `20` (in `10**(v1/20)`) | dB→linear conversion | Standard: S-parameters in dB are 20·log₁₀(|S|), so the inverse is 10^(dB/20). The 20 comes from voltage (not power) convention for S-parameters. |

## Synthetic signal generator

| Value | Location | Meaning |
|-------|----------|---------|
| `401` | `N_freq=401` | Number of frequency points. Standard VNA sweep: 401 points from 100 MHz to 20 GHz gives ~50 MHz resolution. Industry default on many instruments. |
| `20e9` | `f_max=20e9` | Maximum frequency: 20 GHz. Covers PCIe Gen 5 (16 GHz Nyquist), USB4, and most high-speed serial links. |
| `0.1e9` | `freqs = np.linspace(0.1e9, ...)` | Start frequency: 100 MHz. Below this, differential signaling is rarely tested. |
| `1e-9` | `phase = -2 * np.pi * f * 1e-9` | Propagation delay: 1 ns. Typical for a 15 cm PCB trace (speed ~0.5c). Phase = -2πf·τ where τ = 1 ns. |
| `0.3` | `loss = 0.3 * fn` | Linear loss coefficient for "good" channel. At f_max, |S₂₁| = 0.7 → IL ≈ 3 dB. Typical for a well-designed 15 cm differential pair. |
| `0.05` | `Sdd11 = 0.05` | Return loss magnitude: |S₁₁| = 0.05 → RL = 26 dB. Good impedance match. |
| `0.01` | `Sdc21 = 0.01 * fn` | Mode conversion at low frequency: -40 dB. Growing linearly with frequency as asymmetry couples differentially into common mode. |
| `Q = 20` | resonant profile | Quality factor of synthetic resonance. Q = 20 is a moderate resonance (e.g., from a via stub). |
| `f_max / 3` | `f_res = f_max / 3` | Resonance at 6.67 GHz — a typical stub resonance at λ/4 for a 7.5 mm stub. |
| `0.6` | resonant loss amplitude | 0.6 at resonance → 60% power loss → ~8 dB notch. A significant but not catastrophic resonance. |
| `0.7` | lossy loss coefficient | IL coefficient for "lossy" channel: IL ≈ 7 dB at Nyquist. A failing channel. |
| `1.2e-9` | lossy delay | 1.2 ns delay: slightly longer trace (18 cm). |
| `0.9e-9` | crosstalk delay | 0.9 ns: shorter trace for crosstalk profile. |
| `0.2, 0.45, 0.7` | multi-resonant frequencies | Three resonances at 20%, 45%, 70% of f_max (4, 9, 14 GHz). Models a channel with multiple via stubs at different lengths. |
| `Q = 15` | multi-resonant Q | Lower Q = wider resonances, which is worse for broadband integrity. |
| `0.05` | `Scc11 = 0.05` | Common-mode return loss, constant across profiles. |
| `0.5` | `Sdc21 * 0.5` | Cross-coupling: Sdc₂₃ is half of Sdc₂₁, modeling asymmetric mode conversion between port pairs. |

## Feature extraction

| Value | Location | Meaning |
|-------|----------|---------|
| `3` | `-3 dB bandwidth` | Standard half-power bandwidth definition. |
| `6` | `-6 dB bandwidth` | Quarter-power bandwidth. Used in SI for "usable" bandwidth. |
| `N // 2` | `idx_nyq = N // 2` | Nyquist frequency index: half the maximum frequency. For a 20 GHz sweep, Nyquist = 10 GHz. |
| `0.02` | `prominence=0.02` in resonance detection | Minimum prominence for a notch in |Sdd21|. 0.02 in linear = ~0.17 dB. Rejects noise ripples, catches real resonances. |
| `N//50` | `distance=max(1, N//50)` | Minimum distance between detected peaks: ~8 points at N=401. Prevents double-counting a single resonance. |
| `0.01` | `prominence=0.01` in RL peaks | Lower prominence for return loss peaks (impedance mismatch is subtler). |
| `10` | `N > 10` for slope fitting | Minimum points for linear regression of mode conversion slope. |
| `1e-10` | std guards | Correlation guard: don't compute correlation on constant signals. |
| `3` | `N > 3` for group delay | Minimum points for phase unwrapping and group delay estimation. |
| `5` | `N > 5` for phase linearity | Minimum points for linear fit of phase vs. frequency. |
| `1e-9` | `mean_gd * 1e9` | Conversion: group delay from seconds to nanoseconds for the feature vector. |

## Quality metrics

| Value | Location | Meaning |
|-------|----------|---------|
| `30` | `IL_nyquist / 30` | Normalization for FoM: 30 dB is roughly the maximum useful IL before the channel is completely opaque. FoM = BW × (1 - IL/30). |
| `10` | `10 - IL_nyquist` | IL spec: typical spec mask requires IL < 10 dB at Nyquist. |
| `10` | `mean_RL - 10` | RL spec: typical spec mask requires RL > 10 dB (i.e., |S₁₁| < -10 dB). |
| `-20` | `-20 - worst_Sdc` | Mode conversion spec: Sdc < -20 dB. IEEE 802.3 and USB-IF commonly require this. |
| `-25` | `worst_Sdc < -25` | Low conversion flag: 5 dB better than spec. Indicates a clean layout. |

## Classifier

| Value | Location | Meaning |
|-------|----------|---------|
| `3` | `il_m > 3 and rl_m > 3` | 3 dB margin above spec for PASS. Conservative: 3 dB margin accounts for manufacturing variation. |
| `5` | `mc_m > 5` | 5 dB margin on mode conversion for PASS. Mode conversion is harder to control in production, so a wider margin is required. |
| `0` | `il_m > 0` | MARGINAL: meets spec but with no margin. |
| `120` | `1/120` at throughput check | Production rate: 120 boards/second. If classification takes > 1/120 s ≈ 8.3 ms, the engine can't keep up. |
