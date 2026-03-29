#!/usr/bin/env python3
"""
Serie I · Turbulence Spectral Engine (1D wavelet cascade)
==========================================================
Same architecture as geometric_engine.py, applied to
1D velocity signals via multi-scale wavelet decomposition.

Input:  1D velocity time series v(t)
Output: 29 spectral features for turbulence regime classification

Channels:
  Canal B = per-scale energy profile (amplitude decay = cascade)
  Canal A = per-scale kurtosis profile (intermittency structure)
  Cross   = cross-scale energy correlation (cascade coupling)

The motor doesn't know it's doing turbulence analysis.
It sees a spectrum and extracts geometry.

Copyright (c) 2026 Ricardo Hernández Reveles
SPDX-License-Identifier: AGPL-3.0-or-later
"""
import numpy as np
import time


# ═══════════════════════════════════════════════════════════════
# MODULE 1: MANUAL 1D HAAR WAVELET
# ═══════════════════════════════════════════════════════════════

def haar_1d_one_level(signal):
    """One-level 1D Haar: returns (approx, detail)."""
    N = len(signal)
    h = N // 2
    a = (signal[0::2] + signal[1::2]) / np.sqrt(2)
    d = (signal[0::2] - signal[1::2]) / np.sqrt(2)
    return a, d


def haar_1d_multilevel(signal, levels):
    """
    Multi-level 1D Haar DWT.

    Returns list of detail coefficient arrays (finest to coarsest)
    and the final approximation.
    """
    details = []
    approx = signal.copy()
    for lev in range(levels):
        N = len(approx)
        if N < 2:
            break
        if N % 2 != 0:
            approx = np.append(approx, 0.0)
        a, d = haar_1d_one_level(approx)
        details.append(d)
        approx = a
    return details, approx


# ═══════════════════════════════════════════════════════════════
# MODULE 2: PER-SCALE STATISTICS
# ═══════════════════════════════════════════════════════════════

def scale_energy(coeffs):
    """Energy at a scale."""
    return float(np.sum(coeffs ** 2))


def scale_kurtosis(coeffs):
    """Excess kurtosis at a scale (intermittency indicator)."""
    c = coeffs.ravel()
    if len(c) < 4:
        return 0.0
    std = c.std()
    if std < 1e-15:
        return 0.0
    return float(np.mean(((c - c.mean()) / std) ** 4) - 3.0)


def scale_entropy(coeffs):
    """Shannon entropy of squared coefficients."""
    c2 = coeffs ** 2
    s = c2.sum()
    if s < 1e-30:
        return 0.0
    p = c2 / s
    p = p[p > 1e-15]
    return float(-np.sum(p * np.log(p)))


# ═══════════════════════════════════════════════════════════════
# MODULE 3: 29-FEATURE EXTRACTION
# ═══════════════════════════════════════════════════════════════

FEATURE_NAMES = [
    # Energy structure (7)
    'total_energy', 'approx_energy_ratio', 'detail_energy_ratio',
    'energy_slope', 'energy_slope_residual', 'energy_centroid', 'energy_spread',
    # Cascade diagnostics (5)
    'cascade_ratio_mean', 'cascade_ratio_std', 'k41_deviation',
    'energy_flux_constancy', 'inertial_range_width',
    # Kurtosis profile (5)
    'kurtosis_mean', 'kurtosis_max', 'kurtosis_growth_rate',
    'kurtosis_at_fine', 'kurtosis_at_coarse',
    # Entropy (3)
    'entropy_mean', 'entropy_max', 'entropy_spread',
    # Cross-scale (4)
    'magnitude_correlation', 'energy_autocorrelation',
    'self_similarity', 'spectral_flatness',
    # Summary (5)
    'n_scales', 'total_variance', 'is_laminar',
    'is_kolmogorov', 'is_intermittent',
]


def turbulence_features(signal, levels=8):
    """
    Extract 29 spectral features from a 1D signal via Haar DWT.

    Parameters
    ----------
    signal : ndarray, shape (N,)
    levels : int, number of decomposition levels (default 8)

    Returns
    -------
    vec : ndarray, shape (29,)
    """
    # Normalize
    sig = signal - signal.mean()
    std = sig.std()
    if std > 1e-15:
        sig = sig / std

    details, approx = haar_1d_multilevel(sig, levels)
    n_scales = len(details)
    if n_scales < 2:
        return np.zeros(29, dtype=np.float64)

    # Per-scale energy, kurtosis, entropy
    energies = np.array([scale_energy(d) for d in details])
    kurtoses = np.array([scale_kurtosis(d) for d in details])
    entropies = np.array([scale_entropy(d) for d in details])
    approx_e = scale_energy(approx)
    total_e = energies.sum() + approx_e
    te_safe = total_e if total_e > 1e-30 else 1.0

    # 1-7: Energy structure
    approx_ratio = approx_e / te_safe
    detail_ratio = energies.sum() / te_safe

    # Energy slope: log-linear fit E(j) ~ 2^{-αj}
    # For K41: E(j) ~ 2^{5j/3} (energy at scale j for Kolmogorov)
    log_e = np.log(energies + 1e-30)
    j_idx = np.arange(n_scales, dtype=float)
    if n_scales >= 2:
        coeffs = np.polyfit(j_idx, log_e, 1)
        slope = coeffs[0]
        residual = float(np.sqrt(np.mean((log_e - np.polyval(coeffs, j_idx)) ** 2)))
    else:
        slope = 0.0
        residual = 0.0

    # Energy centroid and spread
    weights = energies / (energies.sum() + 1e-30)
    indices = j_idx + 1
    centroid = float(np.dot(weights, indices))
    spread = float(np.sqrt(np.dot(weights, (indices - centroid) ** 2)))

    # 8-12: Cascade diagnostics
    # Adjacent scale energy ratios E(j+1)/E(j)
    ratios = []
    for i in range(n_scales - 1):
        if energies[i] > 1e-30:
            ratios.append(energies[i + 1] / energies[i])
    ratios = np.array(ratios) if ratios else np.array([1.0])
    cascade_mean = ratios.mean()
    cascade_std = ratios.std() if len(ratios) > 1 else 0.0

    # K41 predicts E(j+1)/E(j) = 2^{5/3} ≈ 3.175 for inertial range
    k41_expected = 2 ** (5.0 / 3.0)
    k41_dev = abs(cascade_mean - k41_expected) / k41_expected

    # Energy flux constancy: std of ratios / mean (low = constant cascade)
    flux_const = cascade_std / (cascade_mean + 1e-15)

    # Inertial range width: number of scales where ratio is within 50% of K41
    inertial = sum(1 for r in ratios if abs(r - k41_expected) / k41_expected < 0.5)

    # 13-17: Kurtosis profile
    kurt_mean = kurtoses.mean()
    kurt_max = kurtoses.max()
    # Kurtosis growth rate: slope of kurtosis vs scale index
    if n_scales >= 2:
        kurt_slope = np.polyfit(j_idx, kurtoses, 1)[0]
    else:
        kurt_slope = 0.0
    kurt_fine = kurtoses[0]
    kurt_coarse = kurtoses[-1]

    # 18-20: Entropy
    ent_mean = entropies.mean()
    ent_max = entropies.max()
    ent_spread = entropies.std()

    # 21-24: Cross-scale
    # Magnitude correlation between adjacent scales
    mag_corrs = []
    for i in range(n_scales - 1):
        d1 = np.abs(details[i])
        d2 = np.abs(details[i + 1])
        # Downsample finer scale to match coarser
        n = min(len(d1) // 2, len(d2))
        if n > 2:
            d1_ds = d1[:2 * n:2][:n]
            r = np.corrcoef(d1_ds, d2[:n])[0, 1]
            if np.isfinite(r):
                mag_corrs.append(abs(r))
    mag_corr = np.mean(mag_corrs) if mag_corrs else 0.0

    # Energy autocorrelation (lag-1 correlation of energy profile)
    if n_scales >= 3:
        e_ac = np.corrcoef(energies[:-1], energies[1:])[0, 1]
        e_ac = float(e_ac) if np.isfinite(e_ac) else 0.0
    else:
        e_ac = 0.0

    # Self-similarity: correlation of detail distributions across scales
    self_sim_vals = []
    for i in range(n_scales - 1):
        # Compare normalized histograms
        h1, _ = np.histogram(np.abs(details[i]), bins=20, density=True)
        h2, _ = np.histogram(np.abs(details[i + 1]), bins=20, density=True)
        n1, n2 = np.linalg.norm(h1), np.linalg.norm(h2)
        if n1 > 1e-15 and n2 > 1e-15:
            self_sim_vals.append(float(np.dot(h1, h2) / (n1 * n2)))
    self_sim = np.mean(self_sim_vals) if self_sim_vals else 0.0

    # Spectral flatness of energy profile
    geo_mean = np.exp(np.mean(log_e))
    arith_mean = energies.mean()
    flatness = geo_mean / (arith_mean + 1e-30) if arith_mean > 1e-30 else 0.0

    # 25-29: Summary
    total_var = float(sig.var())

    # Classification flags (empirical, not theoretical)
    is_laminar = float(kurt_max < 0.5 and residual < 0.5)
    is_kolmogorov = float(approx_ratio > 0.3 and kurt_max < 5.0 and slope > 0)
    is_intermittent = float(kurt_max > 5.0)

    vec = np.array([
        total_e, approx_ratio, detail_ratio,
        slope, residual, centroid, spread,
        cascade_mean, cascade_std, k41_dev,
        flux_const, float(inertial),
        kurt_mean, kurt_max, kurt_slope,
        kurt_fine, kurt_coarse,
        ent_mean, ent_max, ent_spread,
        mag_corr, e_ac, self_sim, flatness,
        float(n_scales), total_var,
        is_laminar, is_kolmogorov, is_intermittent,
    ], dtype=np.float64)

    return vec


# ═══════════════════════════════════════════════════════════════
# MODULE 4: SYNTHETIC SIGNAL GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_signal(kind, N=4096, seed=42):
    """
    Generate synthetic 1D velocity signal.

    Kinds: laminar, kolmogorov, intermittent, white_noise, tonal
    """
    rng = np.random.RandomState(seed)
    t = np.linspace(0, 1, N, endpoint=False)

    if kind == 'laminar':
        # Smooth, periodic flow: few harmonics
        return np.sin(2 * np.pi * 10 * t) + 0.3 * np.sin(2 * np.pi * 20 * t)

    elif kind == 'kolmogorov':
        # White noise filtered with k^{-5/6} amplitude → E(k) ~ k^{-5/3}
        freqs = np.fft.rfftfreq(N, d=1.0 / N)
        freqs[0] = 1.0  # avoid division by zero
        amplitude = freqs ** (-5.0 / 6.0)
        amplitude[0] = 0.0
        phases = rng.uniform(0, 2 * np.pi, len(freqs))
        spectrum = amplitude * np.exp(1j * phases)
        signal = np.fft.irfft(spectrum, n=N)
        return signal

    elif kind == 'intermittent':
        # Kolmogorov base + random 5× bursts
        base = generate_signal('kolmogorov', N, seed)
        # Add intermittent bursts
        n_bursts = 8
        for _ in range(n_bursts):
            pos = rng.randint(0, N - 64)
            width = rng.randint(16, 64)
            base[pos:pos + width] *= 5.0
        return base

    elif kind == 'white_noise':
        return rng.randn(N)

    elif kind == 'tonal':
        # Strong periodic component (machine-like, not turbulent)
        return (np.sin(2 * np.pi * 50 * t)
                + 0.5 * np.sin(2 * np.pi * 100 * t)
                + 0.1 * rng.randn(N))

    else:
        raise ValueError(f"Unknown signal kind: {kind}")


SIGNALS = ['laminar', 'kolmogorov', 'intermittent', 'white_noise', 'tonal']


# ═══════════════════════════════════════════════════════════════
# MODULE 5: CLASSIFIER
# ═══════════════════════════════════════════════════════════════

def classify(vec):
    """
    Rule-based classifier: LAMINAR / KOLMOGOROV / INTERMITTENT / BROADBAND / TONAL

    Key discriminators (from feature analysis):
    - INTERMITTENT: extreme kurtosis at fine scales (bursts → kurt_max >> 3)
    - LAMINAR: negative kurtosis (sinusoidal = sub-Gaussian), smooth cascade
    - TONAL: negative kurtosis + high residual (energy at discrete scales)
    - BROADBAND: negative slope (equal energy across scales = white noise)
    - KOLMOGOROV: high approx ratio (red spectrum), positive slope, moderate kurtosis

    Limitation: Haar wavelet has poor frequency resolution. The K41 cascade
    ratio 2^{5/3} is not recovered cleanly. Classification uses empirical
    thresholds from synthetic signals, not theoretical predictions.
    """
    kurt_max = vec[FEATURE_NAMES.index('kurtosis_max')]
    residual = vec[FEATURE_NAMES.index('energy_slope_residual')]
    slope = vec[FEATURE_NAMES.index('energy_slope')]
    approx_ratio = vec[FEATURE_NAMES.index('approx_energy_ratio')]
    flatness = vec[FEATURE_NAMES.index('spectral_flatness')]

    # Gate 1: INTERMITTENT — extreme kurtosis (bursts)
    if kurt_max > 5.0:
        return 'INTERMITTENT', (
            f'extreme kurtosis ({kurt_max:.1f}) indicates fine-scale bursts'
        )

    # Gate 2: Sub-Gaussian signals (kurtosis < 0 → sinusoidal content)
    if kurt_max < 0.5:
        # TONAL: discrete peaks → high residual from cascade fit
        if residual > 0.5:
            return 'TONAL', (
                f'sub-Gaussian (kurt={kurt_max:.2f}), peaky spectrum (residual={residual:.3f})'
            )
        # LAMINAR: smooth harmonics → low residual
        return 'LAMINAR', (
            f'sub-Gaussian (kurt={kurt_max:.2f}), smooth cascade (residual={residual:.3f})'
        )

    # Gate 3: BROADBAND — energy at fine scales dominates (white noise)
    if slope < -0.3:
        return 'BROADBAND', (
            f'negative slope ({slope:.3f}), energy at fine scales'
        )

    # Gate 4: KOLMOGOROV — red spectrum with cascade structure
    if approx_ratio > 0.3:
        return 'KOLMOGOROV', (
            f'red spectrum (approx_ratio={approx_ratio:.3f}), cascade slope={slope:.3f}'
        )

    # Default
    return 'BROADBAND', f'no dominant regime (slope={slope:.2f}, kurt={kurt_max:.1f})'


# ═══════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 72)
    print("TURBULENCE SPECTRAL ENGINE — DEMO")
    print("29 features from 1D Haar DWT · Same architecture as ζ engine")
    print("=" * 72)

    results = {}
    for kind in SIGNALS:
        sig = generate_signal(kind, N=4096)
        vec = turbulence_features(sig, levels=8)
        verdict, reason = classify(vec)
        results[kind] = {'vec': vec, 'verdict': verdict, 'reason': reason}

    # ── Classification results ──
    print(f"\n{'─'*72}")
    print("CLASSIFICATION")
    print(f"{'─'*72}")

    expected = {
        'laminar': 'LAMINAR', 'kolmogorov': 'KOLMOGOROV',
        'intermittent': 'INTERMITTENT', 'white_noise': 'BROADBAND',
        'tonal': 'TONAL',
    }
    correct = 0
    for kind in SIGNALS:
        r = results[kind]
        match = r['verdict'] == expected.get(kind, '?')
        correct += int(match)
        sym = '✓' if match else '✗'
        print(f"\n  {sym} {kind:>14}: {r['verdict']}")
        print(f"    {r['reason']}")

    print(f"\n  Classifier: {correct}/{len(SIGNALS)} correct")

    # ── Feature comparison ──
    print(f"\n{'─'*72}")
    print("FEATURE VECTORS (29-dim)")
    print(f"{'─'*72}")

    print(f"\n  {'feature':>24}", end='')
    for kind in SIGNALS:
        print(f" {kind[:10]:>10}", end='')
    print()

    for j, fname in enumerate(FEATURE_NAMES):
        print(f"  {fname:>24}", end='')
        vals = [results[k]['vec'][j] for k in SIGNALS]
        for v in vals:
            if abs(v) > 100:
                print(f" {v:10.1f}", end='')
            else:
                print(f" {v:10.4f}", end='')
        if np.std(vals) > 0.1 * (np.mean(np.abs(vals)) + 1e-10):
            print("  *", end='')
        print()

    # ── Channel orthogonality ──
    print(f"\n{'─'*72}")
    print("CHANNEL ORTHOGONALITY (Canal B=energy, Canal A=kurtosis, Cross=correlation)")
    print(f"{'─'*72}")

    for kind in SIGNALS:
        v = results[kind]['vec']
        # Canal B: energy profile [total, approx, detail, slope, residual]
        canal_b = v[0:5]
        # Canal A: kurtosis profile [mean, max, growth, fine, coarse]
        canal_a = v[12:17]
        # Cross: cross-scale [mag_corr, e_ac, self_sim, flatness]
        cross = v[20:24]

        n = max(len(canal_b), len(canal_a), len(cross))
        cb = np.zeros(n); cb[:len(canal_b)] = canal_b
        ca = np.zeros(n); ca[:len(canal_a)] = canal_a
        cr = np.zeros(n); cr[:len(cross)] = cross

        r_ba = abs(np.corrcoef(cb, ca)[0, 1]) if np.std(ca) > 1e-10 else 0
        r_bc = abs(np.corrcoef(cb, cr)[0, 1]) if np.std(cr) > 1e-10 else 0
        r_ac = abs(np.corrcoef(ca, cr)[0, 1]) if np.std(ca) > 1e-10 and np.std(cr) > 1e-10 else 0

        orth = "ORTHOGONAL" if max(r_ba, r_bc, r_ac) < 0.5 else "PARTIAL" if max(r_ba, r_bc, r_ac) < 0.8 else "COUPLED"
        print(f"  {kind:>14}: |ρ(B,A)|={r_ba:.3f}  |ρ(B,C)|={r_bc:.3f}  |ρ(A,C)|={r_ac:.3f}  → {orth}")

    # ── Cross-domain mapping ──
    print(f"\n{'─'*72}")
    print("CROSS-DOMAIN MAPPING")
    print(f"{'─'*72}")
    print(f"""
  ζ engine:                Turbulence engine:
  ─────────                ──────────────────
  primes p                 wavelet scales j
  p^{{-σ}} amplitude         E(j) energy per scale
  f(b) = b/(b+1)          energy cascade ratio E(j+1)/E(j)
  cos(ln(p)·γ) phase       kurtosis per scale (phase coherence → intermittency)
  Canal A (v₂)             kurtosis profile (intermittency structure)
  Canal B (ln p)           energy profile (cascade shape)
  Cross (ρ~0)              cross-scale magnitude correlation
  V(σ,t) landscape         E(j,t) scalogram
  gap espectral            inertial range width
  Ramanujan bound          K41 cascade ratio 2^{{5/3}}

  Limitation: Haar wavelet has poor frequency resolution.
  Real turbulence analysis would use Daubechies or Morlet.
  The features discriminate synthetic regimes; real data needs
  higher-order wavelets.

  The spectrum is the spectrum.
""")

    # ── Throughput estimate ──
    sig_test = generate_signal('kolmogorov', N=4096)
    t0 = time.time()
    N_iter = 200
    for _ in range(N_iter):
        turbulence_features(sig_test, levels=8)
    dt = time.time() - t0
    tput = N_iter / dt
    print(f"  Throughput: {tput:.0f} signals/second ({dt/N_iter*1000:.1f}ms per signal)")
    print(f"  Signal length: 4096 samples, {len(haar_1d_multilevel(sig_test, 8)[0])} scales")

    print(f"\n{'='*72}")
    print("ENGINE READY")
    print(f"  Input: 1D numpy array (velocity signal)")
    print(f"  Output: 29 features + LAMINAR/KOLMOGOROV/INTERMITTENT/BROADBAND/TONAL + reason")
    print(f"{'='*72}")
