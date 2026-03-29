#!/usr/bin/env python3
"""
Serie I · Image Spectral Engine (2D radial power spectrum)
===========================================================
Same architecture as geometric_engine.py, applied to
2D grayscale images via radial power spectrum analysis.

Input:  2D numpy array (grayscale image)
Output: 29 spectral features for image type classification

Channels:
  Canal B = radial power spectrum (1/f^α decay = envelope)
  Canal A = angular distribution (isotropy/anisotropy)
  Cross   = local vs global spectrum anomaly (forgery detection)

The motor doesn't know it's doing image analysis.
It sees a spectrum and extracts geometry.

Copyright (c) 2026 Ricardo Hernández Reveles
SPDX-License-Identifier: AGPL-3.0-or-later
"""
import numpy as np
import time


# ═══════════════════════════════════════════════════════════════
# MODULE 1: RADIAL POWER SPECTRUM
# ═══════════════════════════════════════════════════════════════

def radial_power_spectrum(img):
    """
    Compute azimuthally averaged radial power spectrum of a 2D image.

    Returns
    -------
    freqs : ndarray, radial frequency bins (pixels)
    power : ndarray, mean power at each radial frequency
    """
    ny, nx = img.shape
    F = np.fft.fft2(img - img.mean())
    F = np.fft.fftshift(F)
    P = np.abs(F) ** 2

    cy, cx = ny // 2, nx // 2
    Y, X = np.mgrid[:ny, :nx]
    R = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2).astype(int)

    max_r = min(cx, cy)
    freqs = np.arange(1, max_r)
    power = np.zeros(len(freqs))
    for i, r in enumerate(freqs):
        mask = R == r
        if mask.sum() > 0:
            power[i] = P[mask].mean()

    return freqs, power


def angular_spectrum(img, n_sectors=8):
    """
    Compute power distribution across angular sectors.

    Returns
    -------
    sector_powers : ndarray, shape (n_sectors,), total power per sector
    """
    ny, nx = img.shape
    F = np.fft.fft2(img - img.mean())
    F = np.fft.fftshift(F)
    P = np.abs(F) ** 2

    cy, cx = ny // 2, nx // 2
    Y, X = np.mgrid[:ny, :nx]
    angles = np.arctan2(Y - cy, X - cx)  # [-π, π]

    sector_powers = np.zeros(n_sectors)
    edges = np.linspace(-np.pi, np.pi, n_sectors + 1)
    for i in range(n_sectors):
        mask = (angles >= edges[i]) & (angles < edges[i + 1])
        # Exclude DC
        R = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        mask = mask & (R > 1)
        if mask.sum() > 0:
            sector_powers[i] = P[mask].sum()

    return sector_powers


# ═══════════════════════════════════════════════════════════════
# MODULE 2: 29-FEATURE EXTRACTION
# ═══════════════════════════════════════════════════════════════

FEATURE_NAMES = [
    # Spectral slope (4)
    'spectral_slope', 'slope_residual', 'slope_low', 'slope_high',
    # Band energies (5)
    'energy_total', 'energy_low', 'energy_mid', 'energy_high', 'band_ratio_lh',
    # Peak detection (4)
    'n_peaks', 'peak_freq_1', 'peak_prominence_1', 'peak_spread',
    # Spectral shape (4)
    'spectral_centroid', 'spectral_spread', 'spectral_flatness', 'spectral_rolloff',
    # Angular / isotropy (4)
    'isotropy_index', 'anisotropy_ratio', 'dominant_angle_sector', 'angular_entropy',
    # Texture (3)
    'roughness', 'regularity', 'complexity',
    # Summary flags (5)
    'is_natural', 'is_synthetic', 'is_noisy', 'is_periodic', 'is_forged',
]


def image_features(img):
    """
    Extract 29 spectral features from a 2D grayscale image.

    Parameters
    ----------
    img : ndarray, shape (Ny, Nx), float

    Returns
    -------
    vec : ndarray, shape (29,)
    """
    ny, nx = img.shape
    freqs, power = radial_power_spectrum(img)

    if len(freqs) < 4 or power.sum() < 1e-30:
        return np.zeros(29, dtype=np.float64)

    # Normalize power
    p_safe = power.copy()
    p_safe[p_safe < 1e-30] = 1e-30
    log_f = np.log(freqs.astype(float))
    log_p = np.log(p_safe)

    # 1-4: Spectral slope
    # Full slope: fit log(P) = α·log(f) + c
    coeffs = np.polyfit(log_f, log_p, 1)
    slope_full = coeffs[0]
    resid_full = float(np.sqrt(np.mean((log_p - np.polyval(coeffs, log_f)) ** 2)))

    # Low-frequency slope (first third) and high-frequency slope (last third)
    n3 = max(2, len(freqs) // 3)
    if n3 >= 2:
        slope_low = np.polyfit(log_f[:n3], log_p[:n3], 1)[0]
        slope_high = np.polyfit(log_f[-n3:], log_p[-n3:], 1)[0]
    else:
        slope_low = slope_full
        slope_high = slope_full

    # 5-9: Band energies
    total_e = power.sum()
    te_safe = total_e if total_e > 1e-30 else 1.0
    n_freq = len(freqs)
    lo = power[:n_freq // 3].sum()
    mid = power[n_freq // 3: 2 * n_freq // 3].sum()
    hi = power[2 * n_freq // 3:].sum()
    band_ratio = lo / (hi + 1e-30)

    # 10-13: Peak detection (simple: local maxima above median)
    median_p = np.median(power)
    peaks = []
    for i in range(1, len(power) - 1):
        if power[i] > power[i - 1] and power[i] > power[i + 1]:
            if power[i] > 2 * median_p:  # prominence threshold
                peaks.append((i, power[i], power[i] / median_p))

    n_peaks = len(peaks)
    if n_peaks > 0:
        peaks_sorted = sorted(peaks, key=lambda x: -x[2])
        peak_freq_1 = float(freqs[peaks_sorted[0][0]])
        peak_prom_1 = peaks_sorted[0][2]
        peak_freqs = [freqs[p[0]] for p in peaks_sorted]
        peak_spread = float(np.std(peak_freqs)) if len(peak_freqs) > 1 else 0.0
    else:
        peak_freq_1 = 0.0
        peak_prom_1 = 0.0
        peak_spread = 0.0

    # 14-17: Spectral shape
    p_norm = power / (total_e + 1e-30)
    f_float = freqs.astype(float)
    centroid = float(np.dot(p_norm, f_float))
    spread = float(np.sqrt(np.dot(p_norm, (f_float - centroid) ** 2)))

    # Spectral flatness: geometric mean / arithmetic mean
    geo = np.exp(np.mean(log_p))
    arith = power.mean()
    flatness = geo / (arith + 1e-30)

    # Spectral rolloff: frequency below which 85% of energy
    cumsum = np.cumsum(power)
    rolloff_idx = np.searchsorted(cumsum, 0.85 * total_e)
    rolloff = float(freqs[min(rolloff_idx, len(freqs) - 1)])

    # 18-21: Angular / isotropy
    sectors = angular_spectrum(img, n_sectors=8)
    s_total = sectors.sum() + 1e-30
    s_norm = sectors / s_total

    # Isotropy: 1 - (max - min) / (max + min)
    s_max, s_min = sectors.max(), sectors.min()
    isotropy = 1.0 - (s_max - s_min) / (s_max + s_min + 1e-30)

    # Anisotropy ratio: max / min (capped to avoid overflow on pure edges)
    aniso_ratio = min(s_max / (s_min + 1e-30), 1e6)

    # Dominant angle sector
    dom_sector = float(np.argmax(sectors))

    # Angular entropy
    s_ent = s_norm[s_norm > 1e-15]
    angular_ent = float(-np.sum(s_ent * np.log(s_ent)))

    # 22-24: Texture proxies
    # Roughness: ratio of high-freq to total energy
    roughness = hi / te_safe

    # Regularity: how well power fits 1/f^α (low residual = regular)
    regularity = 1.0 / (1.0 + resid_full)

    # Complexity: product of n_peaks and spectral spread
    complexity = float(n_peaks) * spread / (n_freq + 1e-15)

    # 25-29: Summary flags
    is_natural = float(-3.0 < slope_full < -1.0 and n_peaks < 3 and isotropy > 0.6)
    is_synthetic = float(n_peaks >= 2 or abs(slope_full) < 0.5)
    is_noisy = float(abs(slope_full) < 0.5 and flatness > 0.3)
    is_periodic = float(n_peaks >= 2 and peak_prom_1 > 5.0)
    is_forged = 0.0  # Set by forgery_test, not from global features alone

    vec = np.array([
        slope_full, resid_full, slope_low, slope_high,
        total_e, lo, mid, hi, band_ratio,
        float(n_peaks), peak_freq_1, peak_prom_1, peak_spread,
        centroid, spread, flatness, rolloff,
        isotropy, aniso_ratio, dom_sector, angular_ent,
        roughness, regularity, complexity,
        is_natural, is_synthetic, is_noisy, is_periodic, is_forged,
    ], dtype=np.float64)

    return vec


def forgery_test(img, block_size=16):
    """
    Compare local vs global spectral slope to detect pasted regions.

    Returns
    -------
    anomaly_score : float, max |local_slope - global_slope| across blocks
    anomaly_block : tuple (row, col) of most anomalous block
    """
    global_vec = image_features(img)
    global_slope = global_vec[FEATURE_NAMES.index('spectral_slope')]

    ny, nx = img.shape
    max_anomaly = 0.0
    worst_block = (0, 0)

    for r in range(0, ny - block_size + 1, block_size):
        for c in range(0, nx - block_size + 1, block_size):
            block = img[r:r + block_size, c:c + block_size]
            if block.std() < 1e-10:
                continue
            bf, bp = radial_power_spectrum(block)
            if len(bf) < 3 or bp.sum() < 1e-30:
                continue
            log_f = np.log(bf.astype(float))
            log_p = np.log(np.maximum(bp, 1e-30))
            local_slope = np.polyfit(log_f, log_p, 1)[0]
            anomaly = abs(local_slope - global_slope)
            if anomaly > max_anomaly:
                max_anomaly = anomaly
                worst_block = (r, c)

    return max_anomaly, worst_block


# ═══════════════════════════════════════════════════════════════
# MODULE 3: SYNTHETIC IMAGE GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_image(kind, N=64, seed=42):
    """
    Generate synthetic 2D grayscale image.

    Kinds: white_noise, natural, periodic, edge, noisy_natural, forgery
    """
    rng = np.random.RandomState(seed)

    if kind == 'white_noise':
        return rng.randn(N, N)

    elif kind == 'natural':
        # 1/f^2 filtered noise (natural image proxy)
        noise = rng.randn(N, N)
        F = np.fft.fft2(noise)
        fy = np.fft.fftfreq(N)
        fx = np.fft.fftfreq(N)
        FY, FX = np.meshgrid(fy, fx, indexing='ij')
        R = np.sqrt(FX ** 2 + FY ** 2)
        R[0, 0] = 1.0
        filt = R ** (-1.0)  # 1/f → P(f) ~ 1/f^2
        filt[0, 0] = 0.0
        return np.real(np.fft.ifft2(F * filt))

    elif kind == 'periodic':
        # Sinusoidal grid texture
        x = np.linspace(0, 2 * np.pi * 4, N)
        X, Y = np.meshgrid(x, x)
        return np.sin(X) * np.sin(Y) + 0.3 * np.sin(3 * X) * np.cos(2 * Y)

    elif kind == 'edge':
        # Step function (half black, half white)
        img = np.zeros((N, N))
        img[:, N // 2:] = 1.0
        return img

    elif kind == 'noisy_natural':
        # Natural + additive noise
        natural = generate_image('natural', N, seed)
        noise = rng.randn(N, N) * 0.5
        return natural + noise

    elif kind == 'forgery':
        # Natural background + pasted periodic block
        bg = generate_image('natural', N, seed)
        # Insert a periodic texture block
        block_size = N // 4
        r0, c0 = N // 3, N // 3
        x = np.linspace(0, 2 * np.pi * 6, block_size)
        X, Y = np.meshgrid(x, x)
        block = np.sin(X) * np.sin(Y) * 3.0
        bg[r0:r0 + block_size, c0:c0 + block_size] = block
        return bg

    else:
        raise ValueError(f"Unknown image kind: {kind}")


IMAGES = ['white_noise', 'natural', 'periodic', 'edge', 'noisy_natural', 'forgery']


# ═══════════════════════════════════════════════════════════════
# MODULE 4: CLASSIFIER
# ═══════════════════════════════════════════════════════════════

def classify(vec):
    """
    Rule-based classifier: NATURAL / SYNTHETIC / NOISY / TEXTURED / EDGE / FORGED

    Key discriminators:
    - NATURAL: slope ~ -2, few peaks, isotropic
    - NOISY: flat slope (~0), high flatness
    - TEXTURED: many peaks with high prominence
    - EDGE: extreme anisotropy, steep low-freq slope
    - FORGED: detected by forgery_test (not from global features alone)
    """
    slope = vec[FEATURE_NAMES.index('spectral_slope')]
    n_peaks = vec[FEATURE_NAMES.index('n_peaks')]
    peak_prom = vec[FEATURE_NAMES.index('peak_prominence_1')]
    flatness = vec[FEATURE_NAMES.index('spectral_flatness')]
    isotropy = vec[FEATURE_NAMES.index('isotropy_index')]
    aniso = vec[FEATURE_NAMES.index('anisotropy_ratio')]
    roughness = vec[FEATURE_NAMES.index('roughness')]
    resid = vec[FEATURE_NAMES.index('slope_residual')]

    # Gate 1: NOISY — flat spectrum
    if abs(slope) < 0.8 and flatness > 0.15:
        return 'NOISY', f'flat slope ({slope:.2f}), high flatness ({flatness:.3f})'

    # Gate 2: EDGE — extreme anisotropy + steep slope (before peaks, since edges produce harmonics)
    if aniso > 3.0 and isotropy < 0.3 and slope < -2.5:
        return 'EDGE', f'anisotropic (ratio={aniso:.1f}), steep slope ({slope:.2f})'

    # Gate 3: TEXTURED — prominent peaks or anisotropic periodic structure
    if n_peaks >= 2 and peak_prom > 3.0:
        return 'TEXTURED', f'{int(n_peaks)} peaks, prominence={peak_prom:.1f}'
    if aniso > 3.0 and isotropy < 0.3:
        return 'TEXTURED', f'anisotropic periodic (ratio={aniso:.1f}), isotropy={isotropy:.3f}'

    # Gate 4: NATURAL — 1/f^α with α in [-3.5, -0.8]
    if -3.5 < slope < -0.8 and n_peaks < 3:
        quality = 'clean' if resid < 1.0 else 'noisy'
        return 'NATURAL', f'slope={slope:.2f} ({quality}), isotropy={isotropy:.3f}'

    # Default
    return 'SYNTHETIC', f'slope={slope:.2f}, {int(n_peaks)} peaks'


# ═══════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 72)
    print("IMAGE SPECTRAL ENGINE — DEMO")
    print("29 features from 2D FFT radial spectrum · Same architecture as ζ engine")
    print("=" * 72)

    results = {}
    for kind in IMAGES:
        img = generate_image(kind, N=64)
        vec = image_features(img)
        verdict, reason = classify(vec)
        results[kind] = {'vec': vec, 'verdict': verdict, 'reason': reason}

    # ── Classification results ──
    print(f"\n{'─'*72}")
    print("CLASSIFICATION")
    print(f"{'─'*72}")

    expected = {
        'white_noise': 'NOISY', 'natural': 'NATURAL',
        'periodic': 'TEXTURED', 'edge': 'EDGE',
        'noisy_natural': 'NATURAL', 'forgery': 'TEXTURED',
    }
    # forgery classified as TEXTURED at global level is correct:
    # the pasted periodic block injects peaks into the global spectrum.
    # forgery_test provides complementary local anomaly detection.
    correct = 0
    for kind in IMAGES:
        r = results[kind]
        match = r['verdict'] == expected.get(kind, '?')
        correct += int(match)
        sym = '✓' if match else '✗'
        print(f"\n  {sym} {kind:>14}: {r['verdict']}")
        print(f"    {r['reason']}")

    print(f"\n  Classifier: {correct}/{len(IMAGES)} correct")

    # ── Forgery detection ──
    print(f"\n{'─'*72}")
    print("FORGERY DETECTION (local vs global slope anomaly)")
    print(f"{'─'*72}")

    for kind in IMAGES:
        img = generate_image(kind, N=64)
        score, (br, bc) = forgery_test(img, block_size=16)
        is_forg = score > 1.5
        tag = '⚠ FORGERY' if is_forg else '  clean'
        print(f"  {kind:>14}: anomaly={score:.3f}  block=({br},{bc})  → {tag}")

    # ── Feature comparison ──
    print(f"\n{'─'*72}")
    print("FEATURE VECTORS (29-dim)")
    print(f"{'─'*72}")

    print(f"\n  {'feature':>22}", end='')
    for kind in IMAGES:
        print(f" {kind[:10]:>10}", end='')
    print()

    for j, fname in enumerate(FEATURE_NAMES):
        print(f"  {fname:>22}", end='')
        vals = [results[k]['vec'][j] for k in IMAGES]
        for v in vals:
            if abs(v) > 1000:
                print(f" {v:10.0f}", end='')
            elif abs(v) > 10:
                print(f" {v:10.2f}", end='')
            else:
                print(f" {v:10.4f}", end='')
        if np.std(vals) > 0.1 * (np.mean(np.abs(vals)) + 1e-10):
            print("  *", end='')
        print()

    # ── Channel orthogonality ──
    print(f"\n{'─'*72}")
    print("CHANNEL ORTHOGONALITY (Canal B=radial, Canal A=angular, Cross=local/global)")
    print(f"{'─'*72}")

    for kind in IMAGES:
        v = results[kind]['vec']
        # Canal B: spectral slope features
        canal_b = v[0:4]
        # Canal A: angular features
        canal_a = v[17:21]
        # Cross: texture features
        cross = v[21:24]

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
  ζ engine:                Image spectral engine:
  ─────────                ──────────────────────
  t (critical line)        spatial frequency f
  zeros of ζ               spectral peaks (texture frequencies)
  P(N) spiral rolloff      1/f^α power law decay
  f(b) = b/(b+1)          spectral slope α (natural images: α ≈ −2)
  cos(ln(p)·γ) phase       angular distribution (directional texture)
  Canal A (v₂)             angular sector energies (isotropy structure)
  Canal B (ln p)           radial power spectrum (amplitude decay)
  Cross (ρ~0)              local vs global slope anomaly (forgery)
  V(σ,t) landscape         power spectrum surface P(fx, fy)
  gap espectral            band ratio (low/high frequency separation)
  Ramanujan bound          peak prominence threshold

  Limitation: forgery_test uses block_size=16 on 64×64 images.
  Real forensics needs multi-scale analysis on megapixel images.
  The slope α ≈ −2 for natural images is a well-known result
  (Field 1987); the engine re-derives it as f(b) on this domain.

  The spectrum is the spectrum.
""")

    # ── Throughput estimate ──
    img_test = generate_image('natural', N=64)
    t0 = time.time()
    N_iter = 200
    for _ in range(N_iter):
        image_features(img_test)
    dt = time.time() - t0
    tput = N_iter / dt
    print(f"  Throughput: {tput:.0f} images/second ({dt/N_iter*1000:.1f}ms per image)")
    print(f"  Image size: 64×64 pixels")

    print(f"\n{'='*72}")
    print("ENGINE READY")
    print(f"  Input: 2D numpy array (grayscale image)")
    print(f"  Output: 29 features + NATURAL/SYNTHETIC/NOISY/TEXTURED/EDGE/FORGED + reason")
    print(f"  Bonus: forgery_test(img) → anomaly score + block location")
    print(f"{'='*72}")
