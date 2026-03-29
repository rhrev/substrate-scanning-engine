#!/usr/bin/env python3
# Copyright (c) 2026 Ricardo Hernández Reveles
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Serie I · Motor Fault Diagnosis Engine
========================================
Same architecture. Input: vibration spectrum V(f).
Output: 29 features + fault classification.

Fault signatures (classical vibration analysis):
  Normal:        1× dominant, harmonics decay fast
  Unbalance:     1× elevated, phase stable
  Misalignment:  2× elevated, axial component
  Looseness:     many harmonics (1×,2×,3×,...,n×), subharmonics ½×
  Bearing:       non-synchronous peaks at BPFO/BPFI/BSF/FTF
  Gear:          mesh frequency ± sidebands at 1×

The motor sees a spectrum and extracts geometry.
It doesn't know it's diagnosing a turbine.
"""

import numpy as np
from scipy.signal import find_peaks
from scipy.stats import kurtosis, skew
import time

# ═══════════════════════════════════════════════════════════════
# MODULE 1: VIBRATION SIGNAL GENERATOR (synthetic)
# ═══════════════════════════════════════════════════════════════

class VibrationSignal:
    """Vibration spectrum from rotating machinery"""
    
    def __init__(self, freqs, spectrum, rpm, label='unknown'):
        self.freqs = freqs          # Hz
        self.spectrum = spectrum      # magnitude (g or mm/s)
        self.rpm = rpm
        self.f_rot = rpm / 60.0      # rotation frequency (1×)
        self.label = label
        self.N = len(freqs)
    
    @staticmethod
    def generate(fault='normal', rpm=3600, fs=25600, N_samples=8192, snr_dB=40):
        """Generate synthetic vibration signal"""
        f_rot = rpm / 60.0  # 60 Hz at 3600 RPM
        dt = 1.0 / fs
        t = np.arange(N_samples) * dt
        
        # Base signal: always has 1× from residual unbalance
        signal = 0.5 * np.sin(2 * np.pi * f_rot * t + np.random.uniform(0, 2*np.pi))
        
        # Add harmonics with natural decay
        for h in range(2, 6):
            amp = 0.5 / h**2
            signal += amp * np.sin(2 * np.pi * h * f_rot * t + np.random.uniform(0, 2*np.pi))
        
        if fault == 'normal':
            pass  # just base signal
        
        elif fault == 'unbalance':
            # 1× grows 10×, phase locked
            signal += 4.0 * np.sin(2 * np.pi * f_rot * t + 0.3)
        
        elif fault == 'misalignment':
            # 2× grows 8×, 3× grows 4×
            signal += 3.0 * np.sin(2 * np.pi * 2 * f_rot * t + 0.5)
            signal += 1.5 * np.sin(2 * np.pi * 3 * f_rot * t + 0.8)
        
        elif fault == 'looseness':
            # Many harmonics + subharmonic at 0.5×
            signal += 0.8 * np.sin(2 * np.pi * 0.5 * f_rot * t + 1.2)
            for h in range(1, 12):
                amp = 1.5 / (h**0.5)
                signal += amp * np.sin(2 * np.pi * h * f_rot * t + np.random.uniform(0, 2*np.pi))
        
        elif fault == 'bearing_outer':
            # BPFO: Ball Pass Frequency Outer race
            # Typical: BPFO ≈ 0.4 × n_balls × f_rot
            n_balls = 9
            bpfo = 0.4 * n_balls * f_rot  # ~216 Hz at 3600 RPM
            signal += 2.0 * np.sin(2 * np.pi * bpfo * t) * (1 + 0.3 * np.sin(2 * np.pi * f_rot * t))
            # Sidebands at bpfo ± f_rot
            signal += 0.8 * np.sin(2 * np.pi * (bpfo + f_rot) * t)
            signal += 0.8 * np.sin(2 * np.pi * (bpfo - f_rot) * t)
            # Higher harmonics of BPFO
            signal += 1.0 * np.sin(2 * np.pi * 2 * bpfo * t)
        
        elif fault == 'bearing_inner':
            # BPFI: Ball Pass Frequency Inner race
            n_balls = 9
            bpfi = 0.6 * n_balls * f_rot  # ~324 Hz
            signal += 2.5 * np.sin(2 * np.pi * bpfi * t) * (1 + 0.4 * np.sin(2 * np.pi * f_rot * t))
            signal += 1.0 * np.sin(2 * np.pi * (bpfi + f_rot) * t)
            signal += 1.0 * np.sin(2 * np.pi * (bpfi - f_rot) * t)
        
        elif fault == 'gear_mesh':
            # Gear mesh frequency + sidebands
            n_teeth = 42
            f_mesh = n_teeth * f_rot  # 2520 Hz
            signal += 3.0 * np.sin(2 * np.pi * f_mesh * t)
            # Sidebands at f_mesh ± n×f_rot
            for n in range(1, 4):
                signal += 1.0 / n * np.sin(2 * np.pi * (f_mesh + n * f_rot) * t)
                signal += 1.0 / n * np.sin(2 * np.pi * (f_mesh - n * f_rot) * t)
        
        elif fault == 'early_bearing':
            # Very early bearing defect: slight BPFO, mostly normal
            n_balls = 9
            bpfo = 0.4 * n_balls * f_rot
            signal += 0.3 * np.sin(2 * np.pi * bpfo * t) * (1 + 0.1 * np.sin(2 * np.pi * f_rot * t))
            # Slightly elevated kurtosis from impulses
            impulse_times = np.arange(0, t[-1], 1.0/bpfo)
            for ti in impulse_times:
                idx = int(ti * fs)
                if idx < N_samples - 10:
                    signal[idx:idx+5] += np.random.exponential(0.3, 5)
        
        # Add noise
        noise_power = np.mean(signal**2) / (10**(snr_dB/10))
        signal += np.random.normal(0, np.sqrt(noise_power), N_samples)
        
        # FFT
        freqs = np.fft.rfftfreq(N_samples, dt)
        spectrum = np.abs(np.fft.rfft(signal)) / N_samples * 2
        
        return VibrationSignal(freqs, spectrum, rpm, fault)


# ═══════════════════════════════════════════════════════════════
# MODULE 2: FEATURE EXTRACTION (29 features)
# ═══════════════════════════════════════════════════════════════

def vib_features(sig):
    """Extract 29 spectral features from vibration signal"""
    f = sig.freqs
    s = sig.spectrum
    f_rot = sig.f_rot
    N = len(f)
    df = f[1] - f[0] if N > 1 else 1.0
    
    # ── Orders: amplitude at harmonics of rotation ──
    def amp_at(freq):
        """Amplitude at frequency (interpolated)"""
        idx = int(freq / df)
        if idx <= 0 or idx >= N-1: return 0.0
        # Peak in ±3 bins
        lo, hi = max(0, idx-3), min(N, idx+4)
        return np.max(s[lo:hi])
    
    a_half = amp_at(0.5 * f_rot)    # subharmonic
    a_1x = amp_at(f_rot)             # 1× (unbalance)
    a_2x = amp_at(2 * f_rot)        # 2× (misalignment)
    a_3x = amp_at(3 * f_rot)        # 3×
    a_4x = amp_at(4 * f_rot)
    a_5x = amp_at(5 * f_rot)
    
    # ── Harmonic decay rate ──
    harmonics = [a_1x, a_2x, a_3x, a_4x, a_5x]
    harmonics_nz = [h for h in harmonics if h > 1e-10]
    if len(harmonics_nz) > 2:
        log_h = np.log(np.array(harmonics_nz) + 1e-15)
        log_n = np.log(np.arange(1, len(harmonics_nz) + 1))
        harm_decay = np.polyfit(log_n, log_h, 1)[0]  # slope
    else:
        harm_decay = -2.0  # default
    
    # ── Non-synchronous peaks (bearing indicators) ──
    # Find all significant peaks
    peaks, props = find_peaks(s, height=np.mean(s) * 3, distance=max(1, int(f_rot * 0.3 / df)))
    
    # Classify peaks as synchronous (near n×f_rot) or non-synchronous
    sync_peaks = 0
    nonsync_peaks = 0
    nonsync_energy = 0.0
    for pk in peaks:
        f_pk = f[pk]
        # Is it near a harmonic?
        nearest_harm = round(f_pk / f_rot) * f_rot
        if abs(f_pk - nearest_harm) < f_rot * 0.05:
            sync_peaks += 1
        else:
            nonsync_peaks += 1
            nonsync_energy += s[pk]**2
    
    # ── Sideband detection ──
    # Look for sidebands around highest non-1× peak
    sideband_count = 0
    if len(peaks) > 1:
        peak_amps = s[peaks]
        sorted_idx = np.argsort(peak_amps)[::-1]
        for pi in sorted_idx[:5]:
            f_center = f[peaks[pi]]
            # Check for sidebands at ±f_rot
            for sign in [-1, 1]:
                f_sb = f_center + sign * f_rot
                a_sb = amp_at(f_sb)
                if a_sb > 0.3 * s[peaks[pi]]:
                    sideband_count += 1
    
    # ── Overall statistics ──
    total_energy = np.sum(s**2)
    energy_below_5x = np.sum(s[:int(5 * f_rot / df) + 1]**2)
    energy_ratio = energy_below_5x / (total_energy + 1e-15)
    
    # Spectral centroid
    centroid = np.sum(f * s**2) / (np.sum(s**2) + 1e-15)
    
    # Spectral spread
    spread = np.sqrt(np.sum((f - centroid)**2 * s**2) / (np.sum(s**2) + 1e-15))
    
    # Spectral kurtosis (peakedness)
    spec_kurt = kurtosis(s)
    
    # Crest factor
    crest = np.max(s) / (np.sqrt(np.mean(s**2)) + 1e-15)
    
    # ── Ratio features (classical vibration diagnostics) ──
    ratio_2x_1x = a_2x / (a_1x + 1e-15)  # misalignment indicator
    ratio_half_1x = a_half / (a_1x + 1e-15)  # looseness indicator
    ratio_nonsync = nonsync_energy / (total_energy + 1e-15)  # bearing indicator
    
    # ── Quality / severity ──
    overall_level = np.sqrt(total_energy)  # overall vibration level (g RMS)
    
    # ISO 10816 simplified severity (mm/s RMS, velocity)
    # Very rough: acceleration g × 1000 / (2π × centroid) ≈ velocity
    vel_approx = overall_level * 1000 / (2 * np.pi * centroid + 1e-15)
    
    # ── Pack 29 features ──
    vec = np.array([
        # Harmonic amplitudes (6)
        a_1x, a_2x, a_3x, a_half, a_4x + a_5x, harm_decay,
        # Peak classification (4)
        float(sync_peaks), float(nonsync_peaks), float(sideband_count), nonsync_energy,
        # Ratios (3)
        ratio_2x_1x, ratio_half_1x, ratio_nonsync,
        # Overall statistics (6)
        overall_level, centroid, spread, spec_kurt, crest, energy_ratio,
        # Spectral shape (4)
        float(len(peaks)), np.mean(s), np.std(s), np.max(s),
        # Derived (3)
        vel_approx, float(nonsync_peaks > 2), float(sideband_count > 2),
        # Severity (3)
        a_1x / (overall_level + 1e-15),   # 1× dominance
        (a_2x + a_3x) / (a_1x + 1e-15),  # harmonic content
        overall_level / (a_1x + 1e-15),    # broadband ratio
    ], dtype=np.float64)
    
    return vec

FEATURE_NAMES = [
    'A_1x', 'A_2x', 'A_3x', 'A_half', 'A_45x', 'harm_decay',
    'sync_peaks', 'nonsync_peaks', 'sidebands', 'nonsync_E',
    'ratio_2x_1x', 'ratio_half_1x', 'ratio_nonsync',
    'overall_g', 'centroid_Hz', 'spread_Hz', 'kurtosis', 'crest', 'E_ratio_5x',
    'n_peaks', 'mean_spec', 'std_spec', 'max_spec',
    'vel_mm_s', 'bearing_flag', 'gear_flag',
    'dominance_1x', 'harmonic_content', 'broadband_ratio',
]


# ═══════════════════════════════════════════════════════════════
# MODULE 3: CLASSIFIER
# ═══════════════════════════════════════════════════════════════

def diagnose(vec):
    """Rule-based fault classifier"""
    a1x = vec[FEATURE_NAMES.index('A_1x')]
    r21 = vec[FEATURE_NAMES.index('ratio_2x_1x')]
    r_half = vec[FEATURE_NAMES.index('ratio_half_1x')]
    nonsync = vec[FEATURE_NAMES.index('nonsync_peaks')]
    sidebands = vec[FEATURE_NAMES.index('sidebands')]
    overall = vec[FEATURE_NAMES.index('overall_g')]
    harm_d = vec[FEATURE_NAMES.index('harm_decay')]
    dom_1x = vec[FEATURE_NAMES.index('dominance_1x')]
    harm_c = vec[FEATURE_NAMES.index('harmonic_content')]
    broadband = vec[FEATURE_NAMES.index('broadband_ratio')]
    centroid = vec[FEATURE_NAMES.index('centroid_Hz')]
    
    severity = 'LOW'
    if overall > 2.0: severity = 'HIGH'
    elif overall > 0.8: severity = 'MEDIUM'
    
    # Decision tree (simplified ISO 13373-inspired)
    if overall < 0.4 and nonsync < 2:
        return 'NORMAL', severity, 'All indicators within baseline'
    
    if dom_1x > 0.7 and r21 < 0.5 and r_half < 0.2:
        return 'UNBALANCE', severity, f'1× dominant ({dom_1x:.0%}), low harmonics'
    
    if r21 > 1.0:
        return 'MISALIGNMENT', severity, f'2×/1× ratio = {r21:.2f} (>1.0)'
    
    if r_half > 0.3 and harm_d > -1.0:
        return 'LOOSENESS', severity, f'½× present ({r_half:.2f}×), slow harmonic decay ({harm_d:.1f})'
    
    if nonsync > 2 and sidebands > 0:
        if centroid > 500:
            return 'BEARING_INNER', severity, f'{int(nonsync)} non-sync peaks, {int(sidebands)} sidebands, high centroid'
        else:
            return 'BEARING_OUTER', severity, f'{int(nonsync)} non-sync peaks, {int(sidebands)} sidebands'
    
    if nonsync > 1:
        return 'BEARING_EARLY', severity, f'{int(nonsync)} non-sync peaks emerging'
    
    if sidebands > 3 and centroid > 1000:
        return 'GEAR_MESH', severity, f'{int(sidebands)} sidebands at high frequency'
    
    if harm_d > -1.0 and broadband > 3:
        return 'LOOSENESS', severity, f'Slow harmonic decay ({harm_d:.1f}), high broadband'
    
    if r21 > 0.5:
        return 'MISALIGNMENT_MILD', severity, f'2×/1× ratio = {r21:.2f} (elevated)'
    
    return 'UNKNOWN', severity, f'No clear pattern. Review manually.'


# ═══════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 72)
    print("MOTOR FAULT DIAGNOSIS ENGINE")
    print("29 features from vibration spectrum · Same architecture")
    print("=" * 72)
    
    faults = ['normal', 'unbalance', 'misalignment', 'looseness',
              'bearing_outer', 'bearing_inner', 'gear_mesh', 'early_bearing']
    
    # Generate and classify
    print(f"\n{'─'*72}")
    print("FAULT CLASSIFICATION (3600 RPM, fs=25.6kHz)")
    print(f"{'─'*72}")
    
    results = {}
    for fault in faults:
        sig = VibrationSignal.generate(fault, rpm=3600)
        vec = vib_features(sig)
        diag, sev, reason = diagnose(vec)
        results[fault] = {'vec': vec, 'diag': diag, 'severity': sev, 'reason': reason}
        
        match = '✓' if diag.lower().replace('_mild','').replace('_early','').startswith(fault.split('_')[0] if fault != 'normal' else 'normal') else '✗'
        print(f"\n  {match} Input: {fault:>16} → Detected: {diag:<18} [{sev}]")
        print(f"    {reason}")
    
    # Feature comparison
    print(f"\n{'─'*72}")
    print("KEY FEATURES BY FAULT TYPE")
    print(f"{'─'*72}")
    
    key_feats = ['A_1x', 'A_2x', 'A_half', 'ratio_2x_1x', 'ratio_half_1x',
                 'nonsync_peaks', 'sidebands', 'harm_decay', 'overall_g', 'dominance_1x']
    
    print(f"\n  {'feature':>16}", end='')
    for fault in faults:
        print(f" {fault[:7]:>7}", end='')
    print()
    
    for fname in key_feats:
        j = FEATURE_NAMES.index(fname)
        print(f"  {fname:>16}", end='')
        vals = [results[f]['vec'][j] for f in faults]
        for v in vals:
            print(f" {v:7.3f}", end='')
        if np.std(vals) > 0.1 * (np.mean(np.abs(vals)) + 1e-10):
            print("  *", end='')
        print()
    
    # Cross-domain mapping
    print(f"\n{'─'*72}")
    print("CROSS-DOMAIN MAPPING")
    print(f"{'─'*72}")
    print(f"""
  ζ engine:                Motor diagnosis:
  ─────────                ─────────────────
  t                        f (vibration frequency)
  primes p_k               harmonic orders 1×,2×,...
  zeros of ζ               fault frequencies (BPFO, BPFI)
  f(b) envelope            natural harmonic decay
  cos(ln(p)·γ) phase       sideband modulation pattern
  Canal A (arithmetic)     bearing geometry (n_balls, contact angle)
  Canal B (amplitude)      harmonic amplitudes
  Cross-channel            non-synchronous energy
  gap espectral            separation between 1× and bearing freq
  V(σ,t) landscape         vibration severity surface
  
  The spectrum is the spectrum.
""")
    
    # Throughput
    sig = VibrationSignal.generate('normal', rpm=3600)
    t0 = time.time()
    for _ in range(1000):
        vec = vib_features(sig)
        diagnose(vec)
    dt = time.time() - t0
    
    print(f"  Throughput: {1000/dt:.0f} diagnoses/second")
    print(f"  Per sample: {dt/1000*1000:.2f} ms")
    print(f"  At 50 kHz sampling, 8192-point FFT (0.16s window):")
    print(f"    Processing: {dt/1000*1000:.2f} ms  <<  Window: 160 ms")
    print(f"    → Real-time: YES")
    
    # Severity progression
    print(f"\n{'─'*72}")
    print("SEVERITY PROGRESSION: bearing fault developing over time")
    print(f"{'─'*72}")
    print(f"\n  Simulating SNR degradation (fault grows with time)")
    print(f"  {'stage':>12} {'overall_g':>10} {'nonsync_pk':>10} {'diagnosis':>18} {'severity':>8}")
    
    for snr in [60, 50, 40, 35, 30, 25, 20]:
        sig = VibrationSignal.generate('bearing_outer', rpm=3600, snr_dB=snr)
        vec = vib_features(sig)
        diag, sev, _ = diagnose(vec)
        overall = vec[FEATURE_NAMES.index('overall_g')]
        nonsync = vec[FEATURE_NAMES.index('nonsync_peaks')]
        stage = f"SNR={snr}dB"
        print(f"  {stage:>12} {overall:10.4f} {nonsync:10.0f} {diag:>18} {sev:>8}")
    
    print(f"\n{'='*72}")
    print("ENGINE READY")
    print(f"  Input: time-domain vibration signal or FFT spectrum")
    print(f"  Output: 29 features + fault type + severity + reason")
    print(f"{'='*72}")
