#!/usr/bin/env python3
"""
Serie I · Colorimetry Spectral Engine
=======================================
Same architecture. Input: visible spectrum S(λ), 380-780nm.
Output: 29 features preserving structure that CIE XYZ discards.

Copyright (c) 2026 Ricardo Hernández Reveles
SPDX-License-Identifier: AGPL-3.0-or-later
"""
import numpy as np
import time

# CIE 1931 2° observer, 10nm intervals, 380-780nm (41 points)
# Simplified tabulation
WAVELENGTHS = np.arange(380, 790, 10, dtype=float)  # 41 points
N_LAMBDA = len(WAVELENGTHS)

# CIE x̄, ȳ, z̄ (simplified, normalized)
CIE_X = np.array([0.0014,0.0042,0.0143,0.0435,0.1344,0.2839,0.3483,0.3362,0.2908,0.1954,
                   0.0956,0.032,0.0049,0.0093,0.0633,0.1655,0.2904,0.4334,0.5945,0.7621,
                   0.9163,1.0263,1.0622,1.0026,0.8544,0.6424,0.4479,0.2835,0.1649,0.0874,
                   0.0468,0.0227,0.0114,0.0058,0.0029,0.0014,0.0007,0.0003,0.0002,0.0001,0.0])
CIE_Y = np.array([0.0,0.0001,0.0004,0.0012,0.004,0.0116,0.023,0.038,0.06,0.091,
                   0.139,0.208,0.323,0.503,0.71,0.862,0.954,0.995,0.995,0.952,
                   0.87,0.757,0.631,0.503,0.381,0.265,0.175,0.107,0.061,0.032,
                   0.017,0.0082,0.0041,0.0021,0.001,0.0005,0.0003,0.0001,0.0001,0.0,0.0])
CIE_Z = np.array([0.0065,0.0201,0.0679,0.2074,0.6456,1.3856,1.7471,1.7721,1.6692,1.2876,
                   0.813,0.4652,0.272,0.1582,0.0782,0.0422,0.0203,0.0087,0.0039,0.0021,
                   0.0017,0.0011,0.0008,0.0003,0.0002,0.0,0.0,0.0,0.0,0.0,
                   0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0])

def spectrum_to_xyz(S):
    """Convert spectrum to CIE XYZ"""
    dl = 10.0  # nm interval
    X = np.sum(S * CIE_X) * dl
    Y = np.sum(S * CIE_Y) * dl
    Z = np.sum(S * CIE_Z) * dl
    return np.array([X, Y, Z])

FEATURE_NAMES = [
    'X', 'Y', 'Z', 'dominant_wl',
    'peak_wl', 'peak_amp', 'bandwidth_50', 'n_peaks',
    'mean_spacing', 'spacing_cv', 'level_repulsion', 'spec_entropy',
    'centroid', 'spread', 'skewness', 'kurtosis_spec',
    'red_ratio', 'green_ratio', 'blue_ratio', 'uv_energy',
    'smoothness', 'flatness', 'purity', 'metamer_dim',
    'low_freq_E', 'mid_freq_E', 'high_freq_E',
    'total_power', 'crest_factor',
]

def color_features(S):
    """Extract 29 features from visible spectrum S(λ)"""
    S = np.array(S, dtype=float)
    if len(S) != N_LAMBDA: raise ValueError(f"Expected {N_LAMBDA} points, got {len(S)}")
    
    # XYZ
    xyz = spectrum_to_xyz(S)
    total = xyz.sum() + 1e-15
    
    # Dominant wavelength (simplified: wavelength of max chromaticity contribution)
    chrom_x = S * CIE_X; chrom_y = S * CIE_Y
    dom_idx = np.argmax(chrom_x + chrom_y)
    dom_wl = WAVELENGTHS[dom_idx]
    
    # Peaks
    from scipy.signal import find_peaks
    peaks, props = find_peaks(S, prominence=S.max()*0.05, distance=3)
    n_peaks = len(peaks)
    peak_wl = WAVELENGTHS[peaks[0]] if n_peaks > 0 else 580.0
    peak_amp = S[peaks[0]] if n_peaks > 0 else S.max()
    
    # Bandwidth at 50% of max
    half_max = S.max() * 0.5
    above = np.where(S > half_max)[0]
    bw50 = (WAVELENGTHS[above[-1]] - WAVELENGTHS[above[0]]) if len(above) > 1 else 0
    
    # Peak spacings
    if n_peaks > 1:
        sp = np.diff(WAVELENGTHS[peaks])
        ms = sp.mean(); scv = sp.std()/(ms+1e-15)
        if len(sp) > 1:
            rats = [min(sp[i],sp[i+1])/(max(sp[i],sp[i+1])+1e-15) for i in range(len(sp)-1)]
            lr = np.mean(rats)
        else: lr = 0
    else: ms = scv = lr = 0
    
    # Spectral entropy
    Sn = S / (S.sum() + 1e-15)
    entropy = -np.sum(Sn * np.log(Sn + 1e-15))
    
    # Moments
    centroid = np.sum(WAVELENGTHS * S) / (S.sum() + 1e-15)
    spread = np.sqrt(np.sum((WAVELENGTHS - centroid)**2 * S) / (S.sum() + 1e-15))
    m3 = np.sum(((WAVELENGTHS - centroid)/max(spread,1e-10))**3 * Sn)
    m4 = np.sum(((WAVELENGTHS - centroid)/max(spread,1e-10))**4 * Sn)
    
    # Band ratios (R/G/B)
    r_band = S[24:].sum()  # 620-780nm
    g_band = S[12:24].sum()  # 500-620nm
    b_band = S[:12].sum()  # 380-500nm
    band_total = r_band + g_band + b_band + 1e-15
    
    # UV energy (near 380-420nm)
    uv_e = S[:4].sum() / (S.sum() + 1e-15)
    
    # Smoothness (high-frequency content)
    diffs = np.diff(S)
    smoothness = np.sqrt(np.mean(diffs**2))
    
    # Flatness (geometric mean / arithmetic mean)
    S_pos = S[S > 1e-10]
    flatness = np.exp(np.mean(np.log(S_pos))) / (np.mean(S_pos) + 1e-15) if len(S_pos) > 0 else 0
    
    # Colorimetric purity
    dist_from_wp = np.sqrt((xyz[0]/total - 1/3)**2 + (xyz[1]/total - 1/3)**2)
    purity = dist_from_wp / 0.3  # normalized
    
    # Metamerism dimension: effective rank of spectrum beyond XYZ
    # Higher = more information lost by XYZ compression
    S_centered = S - S.mean()
    cov_approx = np.outer(S_centered, S_centered)
    eigs = np.sort(np.abs(np.linalg.eigvalsh(cov_approx)))[::-1]
    eigs_norm = eigs / (eigs.sum() + 1e-15)
    cum = np.cumsum(eigs_norm)
    metamer_dim = float(np.searchsorted(cum, 0.95) + 1)
    
    # Energy bands (low/mid/high thirds)
    third = N_LAMBDA // 3
    low_e = S[:third].sum() / (S.sum() + 1e-15)
    mid_e = S[third:2*third].sum() / (S.sum() + 1e-15)
    high_e = S[2*third:].sum() / (S.sum() + 1e-15)
    
    # Crest factor
    crest = S.max() / (np.sqrt(np.mean(S**2)) + 1e-15)
    
    return np.array([
        xyz[0], xyz[1], xyz[2], dom_wl,
        peak_wl, peak_amp, bw50, float(n_peaks),
        ms, scv, lr, entropy,
        centroid, spread, m3, m4,
        r_band/band_total, g_band/band_total, b_band/band_total, uv_e,
        smoothness, flatness, purity, metamer_dim,
        low_e, mid_e, high_e, S.sum(), crest,
    ], dtype=np.float64)


# ── Synthetic spectra ──
def gaussian_spectrum(peak_wl, width, amp=1.0):
    return amp * np.exp(-0.5*((WAVELENGTHS - peak_wl)/width)**2)

def multi_peak(peaks_wl, widths, amps):
    S = np.zeros(N_LAMBDA)
    for pw, w, a in zip(peaks_wl, widths, amps):
        S += gaussian_spectrum(pw, w, a)
    return S

SAMPLES = {
    'pure_red':     gaussian_spectrum(630, 15),
    'pure_green':   gaussian_spectrum(530, 15),
    'pure_blue':    gaussian_spectrum(460, 15),
    'daylight':     0.5 + 0.3*np.sin((WAVELENGTHS-400)*np.pi/400) + np.random.RandomState(42).normal(0, 0.02, N_LAMBDA),
    'incandescent': np.linspace(0.1, 1.0, N_LAMBDA)**2,  # red-heavy
    'fluorescent':  multi_peak([435, 545, 580, 610], [8, 8, 10, 8], [0.8, 1.0, 0.6, 0.4]),
    'LED_white':    multi_peak([450, 560], [15, 50], [0.8, 1.0]),
    'metamer_A':    multi_peak([480, 580], [20, 20], [0.6, 0.8]),
    'metamer_B':    multi_peak([500, 560, 620], [15, 15, 15], [0.4, 0.6, 0.3]),
    'ruby':         multi_peak([694], [5], [1.0]) + 0.05,
    'emerald':      multi_peak([520, 560], [10, 10], [0.8, 0.6]),
}

if __name__ == '__main__':
    print("="*72)
    print("COLORIMETRY ENGINE — 29 features per spectrum")
    print("="*72)
    
    results = {}
    for name, S in SAMPLES.items():
        S = np.maximum(S, 0)
        vec = color_features(S)
        results[name] = vec
        xyz = vec[:3]
        print(f"  {name:>14}: XYZ=[{xyz[0]:.2f},{xyz[1]:.2f},{xyz[2]:.2f}]  peaks={int(vec[7])}  BW={vec[6]:.0f}nm  purity={vec[22]:.3f}  entropy={vec[11]:.2f}")
    
    # Metamer test
    print(f"\n  Metamer test (A vs B):")
    va, vb = results['metamer_A'], results['metamer_B']
    xyz_dist = np.sqrt(sum((va[i]-vb[i])**2 for i in range(3)))
    feat_dist = np.sqrt(sum((va[i]-vb[i])**2 for i in range(3, 29)))
    print(f"    XYZ distance:     {xyz_dist:.4f}")
    print(f"    Feature distance: {feat_dist:.4f}")
    print(f"    Ratio (feature/XYZ): {feat_dist/(xyz_dist+1e-15):.1f}×")
    print(f"    → Features see {'MORE' if feat_dist > xyz_dist else 'LESS'} difference than XYZ")
    
    t0=time.time()
    for _ in range(1000): color_features(SAMPLES['daylight'])
    dt=time.time()-t0
    print(f"\n  Throughput: {1000/dt:.0f}/s ({dt/1000*1000:.2f}ms)")
